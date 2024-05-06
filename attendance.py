import pytesseract
from PIL import Image

left, right, up, down = 0, 467, 131, 754
with open("screenshot.png", "rb") as file:
    screenshot = Image.open(file).crop((left, up, right, down))

# Coordinates: left, right, up, down
group_1 = (24, 239, 96, 203)
group_2 = (240, 455, 96, 203)
group_3 = (24, 239, 219, 326)
group_4 = (240, 455, 219, 326)
group_5 = (24, 239, 343, 450)

groups = [group_1, group_2, group_3, group_4, group_5]
for group in groups:
    attendance = screenshot.crop((group[0], group[2], group[1], group[3]))
    attendance_text = pytesseract.image_to_string(attendance)
    print(f"Group {groups.index(group) + 1}: {attendance_text}")