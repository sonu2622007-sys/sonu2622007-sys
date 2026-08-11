from pathlib import Path

import cv2
import numpy as np
from PIL import Image


INPUT = Path("scripts/input/portrait_cropped.png")
OUTPUT = Path("stats/portrait.txt")

COLS = 90

# Light → dark
RAMP = " .`:-=+*cs#%@"


# --------------------------------------------------
# 1. Load RGBA image
# --------------------------------------------------

image = Image.open(INPUT).convert("RGBA")

rgba = np.array(image)

rgb = rgba[:, :, :3]
alpha = rgba[:, :, 3]


# --------------------------------------------------
# 2. Resize the image first
# --------------------------------------------------

height, width = alpha.shape

rows = int(
    COLS * (height / width) * 0.48
)

rgb = cv2.resize(
    rgb,
    (COLS, rows),
    interpolation=cv2.INTER_AREA
)

alpha = cv2.resize(
    alpha,
    (COLS, rows),
    interpolation=cv2.INTER_AREA
)


# --------------------------------------------------
# 3. Convert RGB to grayscale
# --------------------------------------------------

gray = cv2.cvtColor(
    rgb,
    cv2.COLOR_RGB2GRAY
)


# --------------------------------------------------
# 4. Background handling
# --------------------------------------------------

# Anything transparent becomes WHITE.
# This is extremely important for ASCII.

transparent = alpha < 128

gray[transparent] = 255


# --------------------------------------------------
# 5. Improve contrast
# --------------------------------------------------

clahe = cv2.createCLAHE(
    clipLimit=3.0,
    tileGridSize=(8, 8)
)

gray = clahe.apply(gray)


# Restore transparent pixels to white
gray[transparent] = 255


# --------------------------------------------------
# 6. Darkening curve
# --------------------------------------------------

normalized = gray.astype(np.float32) / 255.0

darkened = (
    normalized ** 1.7
) * 255

gray = darkened.astype(np.uint8)


# Transparent background MUST remain white
gray[transparent] = 255


# --------------------------------------------------
# 7. Convert pixels to ASCII
# --------------------------------------------------

result = []

for row_index in range(rows):

    line = ""

    for col_index in range(COLS):

        pixel = gray[row_index, col_index]

        # Completely white = blank space
        if pixel >= 245:
            line += " "
            continue

        index = int(
            pixel / 256 * len(RAMP)
        )

        index = min(
            index,
            len(RAMP) - 1
        )

        line += RAMP[index]

    result.append(line.rstrip())


# --------------------------------------------------
# 8. Save
# --------------------------------------------------

OUTPUT.write_text(
    "\n".join(result),
    encoding="utf-8"
)

print("ASCII portrait generated!")
print(f"Columns: {COLS}")
print(f"Rows: {rows}")
print(f"Saved to: {OUTPUT}")