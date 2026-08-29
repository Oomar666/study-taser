import time

EYES_CLOSED_THRESHOLD = 0.4

PRIORITY = ["phone", "away", "sleeping", "social_media", "chess"]

# (trigger_seconds, clear_seconds)
# Set clear_seconds to 0.0 for instant recovery as soon as user returns to focus
THRESHOLDS = {
    "phone": (0.5, 0.0),         # 0.5s trigger threshold, instant clear (0.0s)
    "away": (2.0, 0.0),          # 2.0s trigger threshold, instant clear (0.0s)
    "sleeping": (3.0, 0.0),      # 3.0s trigger threshold, instant clear (0.0s)
    "social_media": (3.0, 0.0),  # 3.0s trigger threshold, instant clear (0.0s)
    "chess": (3.0, 0.0),         # 3.0s trigger threshold, instant clear (0.0s)
}


class _CategoryState:
    def __init__(self, trigger_seconds, clear_seconds):
        self.trigger_seconds = trigger_seconds
        self.clear_seconds = clear_seconds
        self.true_since = None
        self.false_since = None
        self.fired = False

    def update(self, is_true, now):
        just_triggered = False
        if is_true:
            self.false_since = None
            if self.true_since is None:
                self.true_since = now
            if not self.fired and (now - self.true_since) >= self.trigger_seconds:
                self.fired = True
                just_triggered = True
        else:
            if self.true_since is not None:
                if self.false_since is None:
                    self.false_since = now
                if (now - self.false_since) >= self.clear_seconds:
                    self.true_since = None
                    self.false_since = None
                    self.fired = False
        return just_triggered

    def get_progress(self, now) -> float:
        """Returns normalized progress (0.0 to 1.0) towards triggering."""
        if self.fired:
            return 1.0
        if self.true_since is None:
            return 0.0
        return min(1.0, (now - self.true_since) / self.trigger_seconds)


class DistractionStateMachine:
    def __init__(self):
        self._states = {cat: _CategoryState(*THRESHOLDS[cat]) for cat in PRIORITY}

    def update(self, face_present: bool, eyes_closed_conf: float, phone_detected: bool, browser_scenario: str):
        now = time.time()
        conditions = {
            "phone": phone_detected,
            "away": not face_present,
            "sleeping": face_present and (eyes_closed_conf > EYES_CLOSED_THRESHOLD),
            "social_media": browser_scenario == "social_media",
            "chess": browser_scenario == "chess",
        }

        newly_triggered = None
        for cat in PRIORITY:
            just_triggered = self._states[cat].update(conditions[cat], now)
            if just_triggered and newly_triggered is None:
                newly_triggered = cat

        # Determine if any distraction scenario is actively fired
        is_active = any(s.fired for s in self._states.values())

        # Identify primary active or pending category for HUD status display
        primary_scenario = None
        max_progress = 0.0

        for cat in PRIORITY:
            if self._states[cat].fired:
                primary_scenario = cat
                max_progress = 1.0
                break
            prog = self._states[cat].get_progress(now)
            if prog > max_progress:
                max_progress = prog
                primary_scenario = cat

        return {
            "is_active": is_active,
            "new_trigger": newly_triggered,
            "primary_scenario": primary_scenario if (max_progress > 0.0 or is_active) else None,
            "warning_progress": max_progress,
        }
