"""
Calibration Tool for Block Blast on Windows
This tool helps detect your screen resolution and the position of the game window.
"""
try:
    import pyautogui
    from PIL import Image
    import time
    import os
    
    # Try importing mss, if fails, use pyautogui
    try:
        from mss import mss
        HAS_MSS = True
    except ImportError:
        HAS_MSS = False
        print("Warning: 'mss' library not found. Using pyautogui for screenshot (slower).")
        print("To install mss: pip install mss")

    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)

    print("=" * 60)
    print("BLOCK BLAST CALIBRATION TOOL")
    print("=" * 60)

    # Get screen info
    screen_width, screen_height = pyautogui.size()
    print(f"\n1. Screen Resolution: {screen_width} x {screen_height}")

    # Take a screenshot
    print("\n2. Taking screenshot...")
    screenshot_path = "temp/calibration_screenshot.png"
    
    if HAS_MSS:
        with mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            img.save(screenshot_path)
    else:
        # Fallback to pyautogui
        img = pyautogui.screenshot()
        img.save(screenshot_path)
        
    print(f"   Screenshot saved to: {screenshot_path}")
    print(f"   Image size: {img.size[0]} x {img.size[1]}")

    print("\n" + "=" * 60)
    print("INSTRUCTIONS:")
    print("=" * 60)
    print(f"""
1. Open the file '{screenshot_path}'
   (Full path: {os.path.abspath(screenshot_path)})

2. Ensure the Block Blast game window is visible in the screenshot.

3. If the game is NOT visible:
   - Open the game window
   - Run this script again: py calibrate.py

4. Once you see the game in the screenshot, please provide:
   - The (X, Y) coordinates of the TOP-LEFT corner of the 8x8 board.
   - The (X, Y) coordinates of the BOTTOM-RIGHT corner of the 8x8 board.
   
   (You can use Paint or any image viewer to find pixel coordinates)
""")
except Exception as e:
    import traceback
    print("\nCRITICAL ERROR:")
    traceback.print_exc()
    print("\nPlease report this error.")

