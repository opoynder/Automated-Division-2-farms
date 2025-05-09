import os
import ctypes

# Load ViGEmClient.dll before importing vgamepad
try:
    dll_path = os.path.join(os.path.dirname(__file__), 'ViGEmClient.dll')
    ctypes.CDLL(dll_path)
except Exception as e:
    print(f"[WARNING] Failed to load ViGEmClient.dll from local path: {e}")
    try:
        ctypes.CDLL("ViGEmClient.dll")
        print("[INFO] Fallback to system path for ViGEmClient.dll successful.")
    except Exception as fallback_error:
        print(f"[ERROR] Fallback also failed: {fallback_error}")
        raise

import time
import cv2
import numpy as np
import mss
import threading
import keyboard
import vgamepad as vg
from ctypes import windll
from win10toast import ToastNotifier

# Setup
GAMEPAD = vg.VX360Gamepad()
IMAGE_DIR = r"Division_Macro\\images"
TEMPLATES = {
    "delta_03_a": os.path.join(IMAGE_DIR, "delta_03_a.png"),
    "delta_03_b": os.path.join(IMAGE_DIR, "delta_03_b.png"),
    "mike_01": os.path.join(IMAGE_DIR, "mike_01.png")
}

CHARACTER_CREATION_LOGIN_TIME = 25
CHARACTER_CREATION_LOGOUT_TIME = 40
SAFE_HOUSE_LOGIN_TIME = 25
SAFE_HOUSE_LOGOUT_TIME = 40
MENU_LOAD_TIME = 15

running = True
DRY_RUN = True
error_detected = False

toaster = ToastNotifier()

def toggle_macro():
    global running
    running = not running
    status = 'resumed' if running else 'paused'
    print(f"[TOGGLE] Macro {status}")
    toaster.show_toast("Division Macro", f"Macro {status.capitalize()}", duration=2)

def press_button(button, press_duration=0.04, release_wait=0.04):
    if DRY_RUN:
        print(f"[DRY RUN] Would press {button.name} for {press_duration}s, then wait {release_wait}s")
        return
    GAMEPAD.press_button(button=button)
    GAMEPAD.update()
    time.sleep(press_duration)
    GAMEPAD.release_button(button=button)
    GAMEPAD.update()
    time.sleep(release_wait)

def press_thumb(button, press_duration=0.04, release_wait=0.04):
    if DRY_RUN:
        print(f"[DRY RUN] Would press thumb {button.name} for {press_duration}s, then wait {release_wait}s")
        return
    GAMEPAD.press_button(button=button)
    GAMEPAD.update()
    time.sleep(press_duration)
    GAMEPAD.release_button(button=button)
    GAMEPAD.update()
    time.sleep(release_wait)

def press_trigger(left=True, value=255, press_duration=0.04, release_wait=0.04):
    if DRY_RUN:
        trigger = "LT" if left else "RT"
        print(f"[DRY RUN] Would press {trigger} to {value} for {press_duration}s, then wait {release_wait}s")
        return
    if left:
        GAMEPAD.left_trigger(value)
    else:
        GAMEPAD.right_trigger(value)
    GAMEPAD.update()
    time.sleep(press_duration)
    if left:
        GAMEPAD.left_trigger(0)
    else:
        GAMEPAD.right_trigger(0)
    GAMEPAD.update()
    time.sleep(release_wait)

def move_joystick(x=0, y=0, duration=0.5):
    if DRY_RUN:
        print(f"[DRY RUN] Would move joystick to x={x}, y={y} for {duration}s")
        return
    GAMEPAD.left_joystick(x_value=x, y_value=y)
    GAMEPAD.update()
    time.sleep(duration)
    GAMEPAD.left_joystick(0, 0)
    GAMEPAD.update()

def wait(seconds):
    if DRY_RUN:
        print(f"[DRY RUN] Would wait {seconds}s")
    else:
        time.sleep(seconds)

def press_space():
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

def detect_error_live():
    global error_detected
    with mss.mss() as sct:
        while True:
            if not running:
                time.sleep(1)
                continue
            screenshot = np.array(sct.grab(sct.monitors[0]))
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2GRAY)

            for name, path in TEMPLATES.items():
                template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if template is None:
                    continue
                result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > 0.85:
                    print(f"[ERROR DETECTED] {name} with confidence {max_val:.2f}")
                    error_detected = True
                    break
            time.sleep(1)

def run_macro():
    global error_detected
    print("[MACRO] Starting macro loop...")

    for i in range(3):
        if DRY_RUN:
            print(f"[DRY RUN] Would press right trigger (attempt {i + 1})")
        else:
            GAMEPAD.right_trigger(255)
            GAMEPAD.update()
            time.sleep(0.04)
            GAMEPAD.right_trigger(0)
            GAMEPAD.update()
            time.sleep(0.1)

    wait(3)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 1.0, 0.04)
    wait(CHARACTER_CREATION_LOGIN_TIME)

    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.04, 0.04)

    for _ in range(5):
        press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.04, 0.04)

    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 1.94, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.01)

    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START, 0.01, 0.01)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, 0.04, 0.01)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.01)

    wait(CHARACTER_CREATION_LOGOUT_TIME)

    press_trigger(left=True, press_duration=0.04, release_wait=0.04)  # LT press added
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)

    wait(SAFE_HOUSE_LOGIN_TIME)

    move_joystick(32767, 32767, 0.52)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X, 0.22, 0.06)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, 0.04, 0.42)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)
    press_thumb(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.04,0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04,0.04)

    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X, 0.04, 0.34)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_X, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER, 0.04, 0.04)

    press_thumb(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, 1.5, 0.1)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_B, 0.6, 0.8)

    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_START, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_Y, 0.04, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)

    wait(SAFE_HOUSE_LOGOUT_TIME)

    for i in range(3):
        if DRY_RUN:
            print(f"[DRY RUN] Would press right trigger (attempt {i + 1})")
        else:
            GAMEPAD.right_trigger(255)
            GAMEPAD.update()
            time.sleep(0.04)
            GAMEPAD.right_trigger(0)
            GAMEPAD.update()
            time.sleep(0.1)

    press_thumb(vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB, 3.02, 0.04)
    press_button(vg.XUSB_BUTTON.XUSB_GAMEPAD_A, 0.04, 0.04)

    wait(MENU_LOAD_TIME)

def main():
    keyboard.add_hotkey('f11', toggle_macro)
    print("[INFO] Press F11 to toggle the macro on/off. Set DRY_RUN = True at the top to test without input.")
    threading.Thread(target=detect_error_live, daemon=True).start()

    try:
        while True:
            global error_detected
            if running:
                run_macro()
                if error_detected:
                    print("[ERROR] Handling error popup...")
                    press_space()
                    wait(3)
                    error_detected = False
            else:
                wait(1)
    except KeyboardInterrupt:
        print("[EXIT] Macro stopped by user (Ctrl+C)")

if __name__ == "__main__":
    main()
