import os
import random
import threading
import time
import queue
import tkinter as tk
from PIL import Image, ImageTk
import pygame

ASSETS_DIR = "assets"
PAIR_GAP_SECONDS = 1.0
POPUP_DURATION_SECONDS = 1.5
PAIRS_PER_TRIGGER = 5

_popup_queue = queue.Queue()
_photo_refs = []
_open_windows = []
_root = None
_root_ready = threading.Event()
_cancel_event = threading.Event()


def _ensure_mixer():
    if not pygame.mixer.get_init():
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"pygame mixer init warning: {e}")


_ensure_mixer()


def _list_files(folder):
    if not os.path.isdir(folder):
        return []
    return [os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))]


def _spawn_popup(image_path):
    if _root is None:
        return

    win = tk.Toplevel(_root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)

    try:
        img = Image.open(image_path)
        photo = ImageTk.PhotoImage(img, master=win)
        _photo_refs.append(photo)

        w, h = img.size
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = random.randint(0, max(0, screen_w - w))
        y = random.randint(0, max(0, screen_h - h))
        win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(win, image=photo).pack()
        _open_windows.append(win)

        def _cleanup():
            if win in _open_windows:
                _open_windows.remove(win)
            try:
                win.destroy()
            except Exception:
                pass
            if photo in _photo_refs:
                _photo_refs.remove(photo)

        win.after(int(POPUP_DURATION_SECONDS * 1000), _cleanup)
    except Exception as e:
        print(f"Error spawning popup for {image_path}: {e}")


def _close_all_popups_gui():
    """Destroys all active popup windows and clears references."""
    for win in list(_open_windows):
        try:
            win.destroy()
        except Exception:
            pass
    _open_windows.clear()
    _photo_refs.clear()


def _process_queue():
    try:
        while True:
            item = _popup_queue.get_nowait()
            if item == "__CLOSE_ALL__":
                _close_all_popups_gui()
            else:
                _spawn_popup(item)
    except queue.Empty:
        pass
    if _root:
        _root.after(50, _process_queue)


def _gui_thread():
    global _root
    _root = tk.Tk()
    _root.withdraw()
    _root.after(50, _process_queue)
    _root_ready.set()
    _root.mainloop()


threading.Thread(target=_gui_thread, daemon=True).start()
_root_ready.wait(timeout=5)


def stop_effects():
    """
    Instantly stops all playing sound audio, clears popup queue, closes open popup windows,
    and cancels background effect threads.
    """
    _cancel_event.set()

    # 1. Stop all audio playback immediately
    _ensure_mixer()
    try:
        pygame.mixer.stop()
    except Exception as e:
        print(f"Error stopping mixer: {e}")

    # 2. Clear queued popup images
    while not _popup_queue.empty():
        try:
            _popup_queue.get_nowait()
        except queue.Empty:
            break

    # 3. Schedule closing all open windows on GUI thread
    _popup_queue.put("__CLOSE_ALL__")


def trigger_effect(scenario):
    """
    Triggers popup images and sound clips for the specified scenario.
    Cancels any previous effect before running.
    """
    # Cancel previous effect threads and clear old popups/audio
    stop_effects()
    time.sleep(0.05)
    _cancel_event.clear()

    def _run():
        images = _list_files(os.path.join(ASSETS_DIR, "images", scenario))
        sounds = _list_files(os.path.join(ASSETS_DIR, "sounds", scenario))
        if not images or not sounds:
            print(f"No assets found for scenario '{scenario}'")
            return

        chosen_images = random.sample(images, min(PAIRS_PER_TRIGGER, len(images)))
        chosen_sounds = random.sample(sounds, min(PAIRS_PER_TRIGGER, len(sounds)))

        for image_path, sound_path in zip(chosen_images, chosen_sounds):
            if _cancel_event.is_set():
                break

            _ensure_mixer()
            try:
                pygame.mixer.Sound(sound_path).play()
            except Exception as e:
                print(f"Error playing sound {sound_path}: {e}")

            _popup_queue.put(image_path)

            # Interruptible sleep interval
            steps = int(PAIR_GAP_SECONDS / 0.1)
            for _ in range(steps):
                if _cancel_event.is_set():
                    break
                time.sleep(0.1)

    threading.Thread(target=_run, daemon=True).start()
