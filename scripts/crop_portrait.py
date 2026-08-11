from pathlib import Path
from PIL import Image


INPUT = Path("scripts/input/portrait_no_bg.png")
OUTPUT = Path("scripts/input/portrait_cropped.png")


image = Image.open(INPUT).convert("RGBA")

alpha = image.getchannel("A")

bbox = alpha.getbbox()

if bbox is None:
    raise RuntimeError("No visible subject found in the image.")

cropped = image.crop(bbox)

cropped.save(OUTPUT)

print("Portrait cropped successfully!")
print(f"Original size: {image.size}")
print(f"Cropped size: {cropped.size}")
print(f"Saved to: {OUTPUT}")