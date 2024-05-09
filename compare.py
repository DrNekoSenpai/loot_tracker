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
disenchants = []

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
        item_log.append((item, ilvl, roll, winner, False))
    elif pattern_3.match(item):
        item, roll, _ = pattern_3.match(item).groups()
        item_log.append((item, "0", roll, winner, False))
    elif pattern_dis.match(item):
        item = pattern_dis.match(item).groups()[0]
        disenchants.append(item)

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

    export_log.append((item_name, ilvl, roll_type, winner, False))

for ind_i,item in enumerate(item_log): 
    item_name = item[0]
    # Find an entry in the export_log that matches the item name
    matches = [x for x in export_log if item_name in x[0]]

    if len(matches) == 0:
        continue

    elif len(matches) == 1: 
        # Find if there is a tuple in export_log that matches the tuple in the item_log.
        exact_match = False

        for match in matches:
            if item[1] == match[1] and item[2] == match[2] and item[3] == match[3]:
                # print(f"EXACT: {match[:-1]}.")
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

# At this point, we've eliminated all of the items that dropped exactly once. 
# Now we need to find out if there are items that dropped multiple times.

# Identify the items that dropped multiple times, disregarding who won them. 

multiples = list(set([x[0] for x in item_log if item_log.count(x) > 1]))

for item in multiples: 
    # Figure out the list of players who won this item, counting the number of times they won it.
    winners = [x[3] for x in item_log if x[0] == item]
    winner_count = {x: winners.count(x) for x in winners}

    # Find out the number of times this item was awarded in the export log, along with who they went to. 
    export_winners = [x[3] for x in export_log if x[0] == item]
    export_winner_count = {x: export_winners.count(x) for x in export_winners}

    # Find out the number of times this item was awarded in the loot log, along with who they went to.
    loot_winners = [x[3] for x in item_log if x[0] == item]
    loot_winner_count = {x: loot_winners.count(x) for x in loot_winners}

    # Now, we should compare the two dictionaries.
    # Skip over the ones that are exactly the same.

    # We need to sort the dictionaries, first alphabetically by name, then number of times won, descending.
    export_winner_count = dict(sorted(export_winner_count.items(), key=lambda x: (x[0], x[1]), reverse=True))
    loot_winner_count = dict(sorted(loot_winner_count.items(), key=lambda x: (x[0], x[1]), reverse=True))

    if export_winner_count == loot_winner_count: continue

    print(f"{item}: ")
    print("+--------------+---+---+")

    # At this point, we know that the two dictionaries are not the same.
    # Print out any discrepancies between the dictionaries, including winner and count. 
    # Skip exact matches, even if they're not in order. 

    for winner in export_winner_count:
        text_winner = f"{winner:<12}"
        if winner not in loot_winner_count:
            print(f"| {text_winner} | {export_winner_count[winner]} | 0 |")
        elif export_winner_count[winner] != loot_winner_count[winner]:
            print(f"| {text_winner} | {export_winner_count[winner]} | {loot_winner_count[winner]} |")

    for winner in loot_winner_count:
        text_winner = f"{winner:<12}"
        if winner not in export_winner_count:
            print(f"| {text_winner} | 0 | {loot_winner_count[winner]} |")

    print("+--------------+---+---+")

# At this point, we should look and see if there are any items that seem to have been awarded more times in the export log, than they were in the loot log.
# This could be due to overridden rolls. 

for item in export_log:
    item_name = item[0]
    item_count = sum([1 for x in item_log if x[0] == item_name])

    if item_count == 0: 
        # Check if this item was disenchanted.
        if item_name in disenchants: 
            continue

        print(f"ERROR: {item_name} was not found in the loot log.")
        continue

    if item_count < sum([1 for x in export_log if x[0] == item_name]):
        print(f"ERROR: {item_name} was awarded more times in the export log than in the loot log.")