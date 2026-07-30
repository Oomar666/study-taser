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

pygame.mixer.init()

_popup_queue = queue.Queue()
_photo_refs = []
_root = None
_root_ready = threading.Event()


def _list_files(folder):
    if not os.path.isdir(folder):
        return []
    return [os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))]


def _spawn_popup(image_path):
    win = tk.Toplevel(_root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)

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

    def _cleanup():
        win.destroy()
        if photo in _photo_refs:
            _photo_refs.remove(photo)

    win.after(int(POPUP_DURATION_SECONDS * 1000), _cleanup)


def _process_queue():
    try:
        while True:
            image_path = _popup_queue.get_nowait()
            _spawn_popup(image_path)
    except queue.Empty:
        pass
    _root.after(100, _process_queue)


def _gui_thread():
    global _root
    _root = tk.Tk()
    _root.withdraw()
    _root.after(100, _process_queue)
    _root_ready.set()
    _root.mainloop()


threading.Thread(target=_gui_thread, daemon=True).start()
_root_ready.wait(timeout=5)


def trigger_effect(scenario):
    def _run():
        images = _list_files(os.path.join(ASSETS_DIR, "images", scenario))
        sounds = _list_files(os.path.join(ASSETS_DIR, "sounds", scenario))
        if not images or not sounds:
            print(f"No assets found for scenario '{scenario}'")
            return

        chosen_images = random.sample(
            images, min(PAIRS_PER_TRIGGER, len(images)))
        chosen_sounds = random.sample(
            sounds, min(PAIRS_PER_TRIGGER, len(sounds)))

        for image_path, sound_path in zip(chosen_images, chosen_sounds):
            pygame.mixer.Sound(sound_path).play()
            _popup_queue.put(image_path)
            time.sleep(PAIR_GAP_SECONDS)

    threading.Thread(target=_run, daemon=True).start()
