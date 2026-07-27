from PIL import Image

img = Image.open("docs/references/pygame_visual/main_menu.png")
w, h = img.size
pixels = img.load()

# Look for button color (brownish: ~ 0x994c00 -> R=153, G=76, B=0)
# Let's sample down the vertical center line
print("Vertical center scan:")
button_lines = []
for y in range(h):
    r,g,b = pixels[w//2, y][:3]
    if r > 100 and g < 150 and b < 50:
        button_lines.append(y)

if button_lines:
    print(f"Buttons start at y={button_lines[0]}, end at y={button_lines[-1]}")
    # group contiguous lines
    buttons = []
    current_start = button_lines[0]
    for i in range(1, len(button_lines)):
        if button_lines[i] > button_lines[i-1] + 5:
            buttons.append((current_start, button_lines[i-1]))
            current_start = button_lines[i]
    buttons.append((current_start, button_lines[-1]))

    for idx, (start, end) in enumerate(buttons):
        print(f"  Button {idx+1}: y={start} to {end} (height={end-start+1})")
        if idx > 0:
            print(f"  Gap to prev: {start - buttons[idx-1][1] - 1}")

