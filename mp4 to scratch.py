"""
mp4_to_scratch.py
-----------------
Converts an .mp4 video into a sequence of binary frames for use in Scratch.

Each frame is:
  - Resized to 153 x 120 pixels
  - Converted to grayscale, then thresholded to pure black/white
  - Encoded as a string of 18,000 digits (150 * 120):
      0 = black pixel
      1 = white pixel

Output: a .txt file where each line is one frame (18,360 digits long).

Usage:
    python mp4_to_scratch.py input.mp4

Dependencies:
    pip install opencv-python Pillow
"""

import sys
import os
import cv2
from PIL import Image

# ── Configuration ──────────────────────────────────────────────────────────────
TARGET_FPS   = int(sys.argv[2]) if len(sys.argv) >= 3 else 12
FRAME_WIDTH  = 150
FRAME_HEIGHT = 120
# ──────────────────────────────────────────────────────────────────────────────


def process_video(input_path: str) -> None:
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: could not open video: {input_path}")
        sys.exit(1)

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / source_fps if source_fps > 0 else 0

    print(f"Source FPS   : {source_fps:.2f}")
    print(f"Total frames : {total_frames}")
    print(f"Duration     : {duration_sec:.2f}s")
    print(f"Target FPS   : {TARGET_FPS}")
    print(f"Frame size   : {FRAME_WIDTH}x{FRAME_HEIGHT}")

    # How many source frames to skip between each kept frame
    frame_interval = max(1, round(source_fps / TARGET_FPS))

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = base_name + "_scratch.txt"

    frames_written = 0
    frame_index = 0

    with open(output_path, "w") as out_file:
        while True:
            ret, bgr_frame = cap.read()
            if not ret:
                break

            # Only keep every Nth frame to hit target FPS
            if frame_index % frame_interval == 0:
                # Convert BGR → RGB → PIL Image
                rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)

                # Resize to target resolution using high-quality downsampling
                pil_img = pil_img.resize(
                    (FRAME_WIDTH, FRAME_HEIGHT), Image.LANCZOS
                )

                # Grayscale → threshold → binary string
                gray = pil_img.convert("L")  # 8-bit grayscale
                pixels = gray.getdata()       # flat sequence of 0-255 values

                binary_row = "".join(
                    str(min(9, p // 28)) for p in pixels
                )

                # Sanity check: should always be FRAME_WIDTH * FRAME_HEIGHT
                expected = FRAME_WIDTH * FRAME_HEIGHT
                assert len(binary_row) == expected, (
                    f"Frame {frame_index}: got {len(binary_row)} digits, "
                    f"expected {expected}"
                )

                out_file.write(binary_row + "\n")
                frames_written += 1

                if frames_written % 12 == 0:
                    elapsed_sec = frames_written / TARGET_FPS
                    print(f"  Processed {frames_written} frames "
                          f"({elapsed_sec:.1f}s of video)...")

            frame_index += 1

    cap.release()

    print(f"\nDone!")
    print(f"Frames written : {frames_written}")
    print(f"Output file    : {output_path}")
    print()
    print("File format:")
    print(f"  Each line  = 1 frame = {FRAME_WIDTH * FRAME_HEIGHT} digits")
    print(f"  Digit '0'  = black pixel")
    print(f"  Digit '1'  = white pixel")
    print(f"  Grid       = {FRAME_WIDTH} cols x {FRAME_HEIGHT} rows")
    print()
    print("Scratch import tip:")
    print("  Read the file line by line. Each line is one frame.")
    print(f"  Split each line into {FRAME_HEIGHT} chunks of {FRAME_WIDTH} digits")
    print("  to get rows, then index into each chunk for individual pixels.")
    print(f"  Total digits per frame: {FRAME_WIDTH * FRAME_HEIGHT} (150 x 120)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 mp4_to_scratch.py <input.mp4> [fps]")
        print("  fps defaults to 12 if not specified")
        print("  Example: python3 mp4_to_scratch.py badapple.mp4 5")
        sys.exit(1)

    process_video(sys.argv[1])
