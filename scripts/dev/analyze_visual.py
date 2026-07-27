from PIL import Image

img = Image.open("docs/references/pygame_visual/main_menu.png")
w, h = img.size
print(f"Image size: {w}x{h}")

pixels = img.load()

# Let's find the panel bounding box
# Panel is dark grey/black, starting around y=500
panel_y_start = None
panel_y_end = None
panel_x_start = None
panel_x_end = None

for y in range(h):
    # check center pixel
    r,g,b = pixels[w//2, y][:3]
    if r < 40 and g < 40 and b < 40:
        if panel_y_start is None:
            panel_y_start = y
        panel_y_end = y

# Find panel width at center of panel
if panel_y_start is not None:
    py = (panel_y_start + panel_y_end) // 2
    for x in range(w//2, -1, -1):
        r,g,b = pixels[x, py][:3]
        if r > 40 or g > 40 or b > 40:
            panel_x_start = x + 1
            break
    for x in range(w//2, w):
        r,g,b = pixels[x, py][:3]
        if r > 40 or g > 40 or b > 40:
            panel_x_end = x - 1
            break

print(f"Panel: y={panel_y_start} to {panel_y_end}, x={panel_x_start} to {panel_x_end}")
print(f"Panel height: {panel_y_end - panel_y_start if panel_y_end else 0}")
print(f"Panel width: {panel_x_end - panel_x_start if panel_x_end else 0}")

# Find buttons
# button color is brownish R=153, G=76, B=0 typically (0x994c00)
# let's scan down the center
in_button = False
button_starts = []
button_ends = []

for y in range(panel_y_start, panel_y_end):
    r,g,b = pixels[w//2, y][:3]
    if r > 100 and g < 150 and b < 50: # roughly orange/brown
        if not in_button:
            button_starts.append(y)
            in_button = True
    else:
        if in_button:
            button_ends.append(y)
            in_button = False

print(f"Found {len(button_starts)} buttons:")
for i in range(len(button_starts)):
    print(f"  Button {i+1}: y={button_starts[i]} to {button_ends[i]} (height={button_ends[i]-button_starts[i]})")
    if i > 0:
        print(f"  Gap to previous: {button_starts[i] - button_ends[i-1]}")

# Let's find button width
if len(button_starts) > 0:
    by = (button_starts[0] + button_ends[0]) // 2
    bx_start = 0
    bx_end = w
    for x in range(w//2, -1, -1):
        r,g,b = pixels[x, by][:3]
        if r < 100 or g > 150 or b > 50:
            bx_start = x + 1
            break
    for x in range(w//2, w):
        r,g,b = pixels[x, by][:3]
        if r < 100 or g > 150 or b > 50:
            bx_end = x - 1
            break
    print(f"Button Width: {bx_end - bx_start} (x={bx_start} to {bx_end})")

