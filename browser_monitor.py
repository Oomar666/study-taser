import pygetwindow as gw

KEYWORDS = {
    "social_media": ["youtube", "facebook", "instagram", "tiktok"],
    "chess": ["chess.com"],
}


def check_browser():
    """
    Checks the currently focused window's title against known site keywords.
    Returns: {"scenario": "social_media" | "chess" | None, "window_title": str}
    """
    try:
        active = gw.getActiveWindow()
    except Exception:
        return {"scenario": None, "window_title": ""}

    if not active or not active.title:
        return {"scenario": None, "window_title": ""}

    title_lower = active.title.lower()

    for scenario, words in KEYWORDS.items():
        for word in words:
            if word in title_lower:
                return {"scenario": scenario, "window_title": active.title}

    return {"scenario": None, "window_title": active.title}
