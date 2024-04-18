import re, subprocess

from contextlib import redirect_stdout as redirect
from io import StringIO

def up_to_date(): 
    # Return FALSE if there is a new version available.
    # Return TRUE if the version is up to date.
    try:
        # Fetch the latest changes from the remote repository without merging or pulling
        # Redirect output, because we don't want to see it.
        with redirect(StringIO()):
            subprocess.check_output("git fetch", shell=True)

        # Compare the local HEAD with the remote HEAD
        local_head = subprocess.check_output("git rev-parse HEAD", shell=True).decode().strip()
        remote_head = subprocess.check_output("git rev-parse @{u}", shell=True).decode().strip()

        return local_head == remote_head

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

if up_to_date() is False:
    print("Error: the local repository is not up to date. Please pull the latest changes before running this script.")
    print("To pull the latest changes, simply run the command 'git pull' in this terminal.")
    exit(1)
    
with open("loot.txt", "r", encoding="utf-8") as loot_file: 
    loot = loot_file.readlines()

with open("partial-export.txt", "r", encoding="utf-8") as export_file:
    export = export_file.readlines()

loot = [x.strip() for x in loot]
export = [x.strip() for x in export]

print("")

item_log = []
export_log = []

exceptions = [
    "Vanquisher's Mark of Sanctification",
    "Protector's Mark of Sanctification",
    "Conqueror's Mark of Sanctification",
    "Shadowfrost Shard",
    "Rotface's Acidic Blood", 
    "Festergut's Acidic Blood"
]

def regular_keyboard(input_string): 
    pattern = r"^[A-Za-z0-9 \~!@#$%^&*()\-=\[\]{}|;:'\",.<>/?\\_+]*$"
    return re.match(pattern, input_string) is not None 

for ind,item in enumerate(loot): 
    if ind == 0: continue 

    pattern_1 = re.compile(r"(\S+) \(\+\d+ \w+\) \(\+\d+ \w+\)")
    pattern_1_dis = re.compile(r"\_disenchanted")
    pattern_2 = re.compile(r"- (.*) \((.*)\) \((.*)\) -- received on [\*\*]{0,2}(\d{4}-\d{2}-\d{2})[\*\*]{0,2}")
    pattern_3 = re.compile(r"- (.*) \((.*)\) -- received on [\*\*]{0,2}(\d{4}-\d{2}-\d{2})[\*\*]{0,2}")
    pattern_dis = re.compile(r"- (.*)")

    if pattern_1.match(item):
        winner = pattern_1.match(item).groups()[0]
    elif pattern_1_dis.match(item):
        continue
    elif pattern_2.match(item):
        item, ilvl, roll, _ = pattern_2.match(item).groups()
        item_log.append((item, ilvl, roll, winner))
    elif pattern_3.match(item):
        item, roll, _ = pattern_3.match(item).groups()
        item_log.append((item, "0", roll, winner))
    elif pattern_dis.match(item):
        continue

    else: 
        if not item == "": print(f"ERROR: {item}")

for ind,line in enumerate(export):
    if ind == 0: continue 
    line = line.split(";")

    item_id = int(line[0])
    item_name = line[1]
    ilvl = line[2]
    reserved = True if line[3] == "1" else False 
    offspec = True if line[4] == "1" else False
    winner = line[5]

    if item_id == 52025: ilvl = "N25"
    elif item_id == 52026: ilvl = "N25"
    elif item_id == 52027: ilvl = "N25"
    elif item_id == 52028: ilvl = "H25"
    elif item_id == 52029: ilvl = "H25"
    elif item_id == 52030: ilvl = "H25"
    
    if item_id in [50274, 50231, 50226]: roll_type = "ETC"
    elif "Wrathful Gladiator's" in item_name: roll_type = "OS"
    else: roll_type = "SR" if reserved else "OS" if offspec else "MS"

    export_log.append((item_name, ilvl, roll_type, winner))

for item in item_log: 
    item_name = item[0]
    # Find an entry in the export_log that matches the item name
    matches = [x for x in export_log if item_name in x[0]]

    if len(matches) == 0:
        print(f"ERROR: {item_name} not found.")
        continue

    # Find if there is a tuple in export_log that matches the tuple in the item_log. 

    exact_match = False

    for match in matches:
        if item[1] == match[1] and item[2] == match[2] and item[3] == match[3]:
            print(f"EXACT: {match}.")
            exact_match = True
            break
    
    if not exact_match:
        print("+----------------------------------------+")
        item_name = item_name + " " * (38 - len(item_name))
        print(f"| {item_name} |")
        print("+--------+---------------+---------------+")
        print("|  TYPE  |    ACTUAL     |    EXPORT     |")
        print("+--------+---------------+---------------+")
        for match in matches:
            if item[1] != match[1]:
                # Append extra spaces to the end each string, to a maximum of 15 characters. 
                actual = item[1] + " " * (13 - len(item[1]))
                export = match[1] + " " * (13 - len(match[1]))

                print(f"|  ILVL  | {actual} | {export} |")

            if item[2] != match[2]:
                actual = item[2] + " " * (13 - len(item[2]))
                export = match[2] + " " * (13 - len(match[2]))

                print(f"|  ROLL  | {actual} | {export} |")

            if item[3] != match[3]:
                actual = item[3] + " " * (13 - len(item[3]))
                export = match[3] + " " * (13 - len(match[3]))

                print(f"| WINNER | {actual} | {export} |")
        print("+--------+---------------+---------------+")