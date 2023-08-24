with open("details.txt", "r") as file: 
    lines = file.readlines()

import re
# Format: 
# 1. Ferrousblade ....... 288.4K (20.0%)
# We only need the name, so we can use regex to extract it
# In this case, the name is Ferrousblade. 
# Everything else is just noise

names = []

for ind,val in enumerate(lines):
    if ind == 0: continue
    else: 
        name = re.search(r"\d. (.*) \.* \d.*", val).group(1)
        names.append(name)

print(" ".join(names))