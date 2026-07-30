import time

EYES_CLOSED_THRESHOLD = 0.4

PRIORITY = ["phone", "away", "sleeping", "chess", "social_media"]

THRESHOLDS = {
    "phone": (2.0, 1.0),
    "away": (5.0, 1.0),
    "sleeping": (10.0, 1.0),
    "chess": (2.0, 1.0),
    "social_media": (2.0, 1.0),
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
                elif (now - self.false_since) >= self.clear_seconds:
                    self.true_since = None
                    self.false_since = None
                    self.fired = False
        return just_triggered


class DistractionStateMachine:
    def __init__(self):
        self._states = {cat: _CategoryState(
            *THRESHOLDS[cat]) for cat in PRIORITY}

    def update(self, face_present, eyes_closed_conf, phone_detected, browser_scenario):
        now = time.time()
        conditions = {
            "phone": phone_detected,
            "away": not face_present,
            "sleeping": face_present and eyes_closed_conf > EYES_CLOSED_THRESHOLD,
            "chess": browser_scenario == "chess",
            "social_media": browser_scenario == "social_media",
        }

        newly_triggered = None
        for cat in PRIORITY:
            just_triggered = self._states[cat].update(conditions[cat], now)
            if just_triggered and newly_triggered is None:
                newly_triggered = cat

        is_active = any(s.fired for s in self._states.values())
        return {"is_active": is_active, "new_trigger": newly_triggered}
