from PIL import Image

img = Image.open("docs/references/pygame_visual/local_match.png")
w, h = img.size
print(f"Image size: {w}x{h}")
