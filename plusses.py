# This file aims to help restore original plusses, by comparing Gargul logs and the backup file, which is provided by "soft_reserve.py". 
# This file should be used when we are changing raids; from Trial of the Crusader, over to Ulduar; as plusses are reset. 

with open("backup.txt", "r") as backup_file: 
    backup = backup_file.readlines()

with open("actual.txt", "r") as actual_file: 
    actual = actual_file.readlines()

# For each line in "actual", remove "-oldblanchy"
actual = [line.replace("-oldblanchy", "") for line in actual]
actual = [line.strip() for line in actual]
actual = [line.split(",") for line in actual]

# For each line in "backup", convert to lowercase
backup = [line.lower() for line in backup]
backup = [line.strip() for line in backup]
backup = [line.split(",") for line in backup]

# For each line in "backup", check if the name is in "actual"
for line in backup:
    # If the name exists in actual, subtract the number of plusses 
    if line[0] in [a[0] for a in actual]:
        # Find the index of the name in actual
        index = [a[0] for a in actual].index(line[0])
        actual[index][1] = f"{int(actual[index][1]) - int(line[1])}"

# Join together the name and number of plusses again
actual = [",".join(line) for line in actual]

# Print each line
import re

for line in actual:
    if re.match(r"^\w+,0", line) is None: print(line)