from rembg import remove
from PIL import Image

INPUT = "scripts/input/portrait.jpg"
OUTPUT = "scripts/input/portrait_no_bg.png"

image = Image.open(INPUT)

result = remove(image)

result.save(OUTPUT)

print("Background removed!")
print("Saved to:", OUTPUT)