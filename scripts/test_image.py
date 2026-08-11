from PIL import Image

image = Image.open("scripts/input/portrait.jpg")

print("Image loaded successfully!")
print("Image size:", image.size)
print("Image mode:", image.mode)