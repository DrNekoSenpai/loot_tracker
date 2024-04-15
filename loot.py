import pickle, re, argparse, os, time, pyautogui, subprocess
from typing import List
from datetime import datetime, timedelta
from contextlib import redirect_stdout as redirect
from io import StringIO

parser = argparse.ArgumentParser()

# Add an argument called "--force-new", "-f" to force the script to create a new pickle file.
parser.add_argument("--force-new", "-f", help="Force the script to create a new pickle file.", action="store_true")

args = parser.parse_args()

raiding = True

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

class Item: 
    def __init__(self, name:str, ilvl:int, slot:int, boe:bool=False): 
        self.name = name
        self.ilvl = ilvl 
        self.slot = slot
        self.boe = boe

class Log: 
    def __init__(self, name, item:Item, roll_type, date:str, note:str = None): 
        """
        Create a log entry.
        - Name: The name of the player
        - Item: The Item object of what was awarded
        - Roll: Roll type (MS, OS, reserve)
        - Date: The date the item was awarded
        """

        self.name = name
        self.item = item
        self.roll = roll_type
        self.date = date
        self.note = note

class Player: 
    def __init__(self, name:str, alias:str, reserves:List[str], pclass:str):
        self.name = name
        self.alias = alias

        self._reserves = reserves
        self._player_class = pclass

        self._regular_plusses = 0
        self._reserve_plusses = 0
        self._attendance = False

        self._raid_log = []
        self._history = {
            "ETC": [], 
            "Head": [],
            "Neck": [],
            "Shoulder": [],
            "Back": [],
            "Chest": [],
            "Wrist": [],
            "Hands": [],
            "Waist": [],
            "Legs": [],
            "Feet": [],
            "Ring": [],
            "Trinket": [],
            "Main-Hand": [],
            "Off-Hand": [],
            "Two-Hand": [],
            "Ranged": [], 
            "Relic": [],
        }

with open('items.sql', 'r', encoding="utf-8") as items_file: 
    items = items_file.read()
    items = items.replace("'", '"')
    items = items.replace('\\"', "'")
    items = items.splitlines()

    # NORMAL 25
    # (52025,'Vanquisher\'s Mark of Sanctification',64877,4,0,1192,80,80,0),
    # (52026,'Protector\'s Mark of Sanctification',64877,4,0,69,80,80,0),
    # (52027,'Conqueror\'s Mark of Sanctification',64877,4,0,274,80,80,0),

    # HEROIC 25
    # (52028,'Vanquisher\'s Mark of Sanctification',64878,4,0,1192,80,80,0),
    # (52029,'Protector\'s Mark of Sanctification',64878,4,0,69,80,80,0),
    # (52030,'Conqueror\'s Mark of Sanctification',64878,4,0,274,80,80,0),

    with open("all_items.txt", 'w', encoding="utf-8") as file: 
        for item in items: 
            file.write(f"{item}\n")

all_items = {}
# (50008,"Ring of Rapid Ascent",64170,4,11,-1,264,80,0),
# Capture the item ID, name, inventory type, and item level.
pattern = re.compile(r'\((\d+),\"(.+)\",\d+,\d+,(\d+),-?\d+,(\d+),\d+,\d+\),?')
slots = {}

exceptions = [
    "Vanquisher's Mark of Sanctification",
    "Protector's Mark of Sanctification",
    "Conqueror's Mark of Sanctification",
    "Shadowfrost Shard",
    "Rotface's Acidic Blood", 
    "Festergut's Acidic Blood"
]

for item in items:
    match = pattern.match(item)
    if match: 
        item_id = int(match.group(1))
        name = match.group(2)
        item_level = int(match.group(4))
        inventory_type = int(match.group(3))

        if item_level <= 251 and not name in exceptions: continue

        if item_id == 52025: name += " (N25)"
        elif item_id == 52026: name += " (N25)"
        elif item_id == 52027: name += " (N25)"
        elif item_id == 52028: name += " (H25)"
        elif item_id == 52029: name += " (H25)"
        elif item_id == 52030: name += " (H25)"

        all_items[item_id] = Item(name, item_level, inventory_type, False)

for item in all_items.values(): 
    if item.slot not in slots: slots[item.slot] = [item]
    else: slots[item.slot].append(item)

# sort the categories dictionary by slot number
slots = dict(sorted(slots.items()))

slot_names = {
    0: "ETC", 
    1: "Head", 
    2: "Neck",
    3: "Shoulder",
    5: "Chest",
    6: "Waist",
    7: "Legs",
    8: "Feet",
    9: "Wrist",
    10: "Hands",
    11: "Ring",
    12: "Trinket",
    13: "Main-Hand",
    14: "Off-Hand",
    15: "Ranged",
    16: "Back",
    17: "Two-Hand",
    20: "Chest", 
    21: "Main-Hand",
    22: "Off-Hand",
    23: "Off-Hand",
    24: "Ranged", 
    25: "Ranged",
    26: "Ranged",
    28: "Relic"
}

def import_pickle(): 
    # Import the pickle file
    try: 
        with open('players.pickle', 'rb') as f:
            players = pickle.load(f)

    except FileNotFoundError:
        print('No pickle file found. Creating a new one.')
        players = []
        players.append(Player("_disenchanted", "_disenchanted", [], ""))

    return players

def export_pickle(players):
    # Export the pickle file
    with open('players.pickle', 'wb') as f:
        pickle.dump(players, f)

# We'll import the pickle if the "--force-new" argument is not present.
if not args.force_new:
    players = import_pickle()
else:
    players = []

    # Create a special player called "_disenchanted", for items that were not awarded to anyone.
    # This is used when no one rolls. 
    players.append(Player("_disenchanted", "_disenchanted", [], ""))

if datetime.now().weekday() == 6 and datetime.now().hour >= 16 and datetime.now().hour < 19: raiding = True
elif datetime.now().weekday() == 2 and datetime.now().hour >= 18 and datetime.now().hour < 20: raiding = True
else: raiding = False

known_aliases = {
    "Sõçkö": "Socko", 
    "Flambeaü": "Flambeau",
    "Killädin": "Killadin",
    "Beásty": "Beasty",
}

def import_softreserve(players): 
    # We'll attempt to import reserve data from the CSV file. 
    if not os.path.exists("soft_reserves.csv"):
        print("No reserve file found. Skipping.")
        return players

    # Go through the list of players, and wipe all reserves. 
    for p in players: 
        p._reserves = []

    with open("soft_reserves.csv", "r", encoding="utf-8") as f: 
        sr_data = f.readlines()

    # Parse the data. 
    for ind,soft_res in enumerate(sr_data):
        if ind == 0: continue # Header row 
        # Split the string into a list.
        soft_res = soft_res.split(",")

        # We'll check if the second column is a number. If it's not, then this item has a comma in it; and we'll join the first two elements together with a comma. 
        if not soft_res[1].isdigit():
            soft_res[0:2] = [",".join(soft_res[0:2])]

        # We'll remove all the quotes from the string. 
        soft_res = [x.replace('"', "") for x in soft_res]

        # Format the strings.
        # Item,ItemId,From,Name,Class,Spec,Note,Plus,Date
        # We care about: Item, Name, Class, Spec
        
        # Item
        item = soft_res[0]
        name = soft_res[3]

        if name == "Swiftblades": name = "Swiftbladess"

        if name in known_aliases.keys(): 
            alias = known_aliases[name]

        else: 
            alias = name
        
        # Check if the player's name can be typed using the English keyboard. 
        if not regular_keyboard(alias):
            print(f"Player name {alias} is not valid. Please input the name manually.")
            alias = input("Name: ")

        # Search for an existing player object. Create it if it doesn't exist. 

        # Check if the player is in the list of players. 
        # If so, wipe their reserve. 
        player_exists = False
        current_player = None
        for p in players: 
            if p.alias == alias: 
                player_exists = True
                current_player = p
                break
        
        if not player_exists: 

            if name in known_players:
                pclass = known_players[name]
                print(f"Player {name} not found in dictionary, but found in list of known players. Player class auto-selected as {pclass}.")
                players.append(Player(name, alias, [], pclass))
                current_player = players[-1]

            else: 
                pclass = input(f"Could not find player {alias}. Creating from scratch. What class are they? ")
                if pclass.lower() in "death knight": pclass = "Death Knight"
                elif pclass.lower() in "druid": pclass = "Druid"
                elif pclass.lower() in "hunter": pclass = "Hunter"
                elif pclass.lower() in "mage": pclass = "Mage"
                elif pclass.lower() in "paladin": pclass = "Paladin"
                elif pclass.lower() in "priest": pclass = "Priest"
                elif pclass.lower() in "rogue": pclass = "Rogue"
                elif pclass.lower() in "shaman": pclass = "Shaman"
                elif pclass.lower() in "warlock": pclass = "Warlock"
                elif pclass.lower() in "warrior": pclass = "Warrior"

                players.append(Player(name, alias, [], pclass))
                current_player = players[-1]

        # Add the item to the player's reserve list, but only if an item of the same name isn't already there. 
        current_player._reserves.append(item)
        print(f"{current_player.name} has reserved {item}.")

    return players

def print_write(string, file=None):
    print(string)
    if file:
        file.write(string + "\n")

def regular_keyboard(input_string): 
    pattern = r"^[A-Za-z0-9 \~!@#$%^&*()\-=\[\]{}|;:'\",.<>/?\\_+]*$"
    return re.match(pattern, input_string) is not None 

def award_loot(players): 
    print("----------------------------------------")
    # First, we'll ask what item we're rolling off; supporting both case insensitivity and partial matching. 
    item = input("What item are we rolling off? ").lower()
    if item == "": return players
    print("")
    # Then, we'll cross check this with our item database.
    item_matches = []
    for i in all_items.values(): 
        if item in i.name.lower(): 
            item_matches.append(i)

    # If there are no matches, we'll print an error and exit.
    # If there is one match, we'll use that.
    # If there are multiple matches, we'll ask the user to specify which one they want.

    if len(item_matches) == 0:
        print("No matches found. Please double-check the item name and try again.")
        return players
    
    elif len(item_matches) == 1: 
        # We'll select this match, and then move on. 
        item_match = item_matches[0]

    elif len(item_matches) > 1: 
        # We'll print all of the matches, and ask them to select one. 
        print("Multiple matches found. Please select one of the following:")
        for i in range(len(item_matches)): 
            print(f"{i+1}. {item_matches[i].name} ({item_matches[i].ilvl})")
        
        # We'll ask the user to select a number.
        sel = input("Select a number: ")
        try: 
            sel = int(sel)
            if sel < 1 or sel > len(item_matches):
                print("Invalid integer input.")
                return players
        except: 
            print("Invalid non-convertible input.")
            return players
        
        # We'll select this match, and then move on.
        item_match = item_matches[sel-1]
        print("")
    # Now, we'll print out the item name; the corresponding category; and the item level.
    print(f"Item: {item_match.name} ({item_match.ilvl})")
    print(f"Slot: {slot_names[int(item_match.slot)]}")

    reserves = []
    ineligible = 0

    # We'll check the soft-reserves to see if anyone has this item soft-reserved, excluding anyone who has already won the same item, with the same item level. 
    # For example, Ring of Rapid Ascent (264) and Ring of Rapid Ascent (277) are considered different items.
    # We need to check the corresponding _history list, which is categorized based on slot. 

    for p in players: 
        # Skip this person if they're not here.
        if p._attendance == False: continue

        if item_match.name in p._reserves: 
            print(f"{p.name} has soft-reserved this item ({item_match.name}).")
            # First, we should check if the player has double-reserved this item; that is, if they want two.
            count = len([i for i in p._reserves if i == item_match.name])
            if count > 1:
                num_received = 0
                for log in p._history[slot_names[int(item_match.slot)]]: 
                    if log.item.name == item_match.name and log.item.ilvl == item_match.ilvl: 
                        num_received += 1
                
                if num_received != 2: 
                    if item_match.ilvl == 277: 
                        # We want to check if the player has already won the 264 version of this item. If so, we'll add a note to the reserves list.
                        num_received_264 = 0
                        for log in p._history[slot_names[int(item_match.slot)]]: 
                            if log.item.name == item_match.name and log.item.ilvl == 264: 
                                num_received_264 += 1
                        
                        reserves.append((p.name, p._reserve_plusses, f" (ilvl 277: {num_received}/2, ilvl 264: {num_received_264}/2)"))
                            
                    else: 
                        reserves.append((p.name, p._reserve_plusses, f" (ilvl 264: {num_received}/2)"))
                
                else: 
                    print(f"{p.name} has already won both copies of this item ({item_match.name} {item_match.ilvl}).")
                    ineligible += 1

            else: 
                # Only append the player to the reserves list if they have not already won the same item, with the same item level.
                already_received = False
                for log in p._history[slot_names[int(item_match.slot)]]: 
                    if log.item.name == item_match.name and log.item.ilvl == item_match.ilvl: 
                        already_received = True
                        print(f"{p.name} has already won this item ({item_match.name} {item_match.ilvl}).")
                        ineligible += 1
                        break

                if not already_received: 
                    if item_match.ilvl == 277: 
                        if any([item_match.name == log.item.name and log.item.ilvl == 264 for log in p._history[slot_names[int(item_match.slot)]]]):
                            reserves.append((p.name, p._reserve_plusses, f" (has 264 version)"))
                        else: 
                            reserves.append((p.name, p._reserve_plusses, ""))

                    else: 
                        reserves.append((p.name, p._reserve_plusses, ""))
    
    if len(reserves) > 0:
        # Sort the reserves list by reserve plusses, then by name.
        reserves.sort(key=lambda x: (x[1], x[0]))

        print("")

        print("The following people have soft-reserved this item:")
        roll_type = "SR"
        for r in reserves: 
            print(f"  - {r[0]} ({roll_type} +{r[1]}){r[2]}")

        if raiding: 
            ready = input("Ready to announce? (y/n): ").lower()
            if ready == "y": 
                pyautogui.moveTo(1920/2, 1080/2)
                pyautogui.click()
                time.sleep(0.1)

                pyautogui.write("/")
                time.sleep(0.1)
                pyautogui.write("rw")
                time.sleep(0.1)
                pyautogui.press("space")
                time.sleep(0.1)
                pyautogui.write(f"The following people have soft-reserved this item, {item_match.name}:")
                time.sleep(0.1)
                pyautogui.press("enter")
                time.sleep(0.25)

                for r in reserves:
                    pyautogui.write("/")
                    time.sleep(0.1)
                    pyautogui.write("rw")
                    time.sleep(0.1)
                    pyautogui.press("space")
                    time.sleep(0.1)
                    pyautogui.write(f"{r[0]} ({roll_type} +{r[1]}){r[2]}")
                    time.sleep(0.1)
                    pyautogui.press("enter")
                    time.sleep(0.25)

    elif len(reserves) == 0 and not slot_names[int(item_match.slot)] == "ETC": 
        if ineligible == 0: print(f"The following item, {item_match.name}, is an open roll -- no one has reserved it.")
        else: print(f"The following item, {item_match.name}, is an open roll -- ALL those who have reserved it have already won this item.")

        if raiding: 
            ready = input("Ready to announce? (y/n): ").lower()
            if ready == "y": 
                pyautogui.moveTo(1920/2, 1080/2)
                pyautogui.click()
                time.sleep(0.1)

                pyautogui.write("/")
                time.sleep(0.1)
                pyautogui.write("rw")
                time.sleep(0.1)
                pyautogui.press("space")
                time.sleep(0.1)
                if ineligible == 0: pyautogui.write(f"The following item, {item_match.name}, is an open roll -- no one has reserved it.")
                else: pyautogui.write(f"The following item, {item_match.name}, is an open roll -- ALL those who have reserved it have already won this item.")
                time.sleep(0.1)
                pyautogui.press("enter")
                time.sleep(0.25)

    elif slot_names[int(item_match.slot)] == "ETC": 
        if item_match.name == "Shadowfrost Shard": 
            # Priority: Artaz, then Ferrousblade, then Pastiry
            # Print out the number of shards that these players have. 
            eligible_players = ["Artaz", "Ferrousblade", "Pastiry"]
            print("")

            priority = ""
            for p in players:
                if p.name in eligible_players: 
                    # Check if this player is present. If not, they can't receive a shard. 
                    if p._attendance == False: continue
                    count = 0
                    for log in p._history["ETC"]: 
                        if log.item.name == item_match.name: 
                            count += 1
                    print(f"{p.name}: {count} shards.")
                    if count < 50 and priority == "": 
                        priority = p.name

            if priority == "": 
                print(f"An error occurred; all players marked as eligible for {item_match.name} have already received 50 shards.")
            
            else: 
                print(f"This shard goes to: {priority}.")

    print("")
    # We'll ask the user to input the name of the person who won the roll. 
    name = input("Who won the roll? ").lower()
    if name == "": return players

    player_matches = []
    for p in players:
        if p._attendance == False: continue
        if name in p.alias.lower(): 
            player_matches.append(p)

    if len(player_matches) == 0:
        print("No matches found. Please double-check the player name and try again.")
        return players
    
    elif len(player_matches) == 1:
        # We'll select this match, and then move on.
        player = player_matches[0]

    elif len(player_matches) > 1:
        # We'll print all of the matches, and ask them to select one.
        print("Multiple matches found. Please select one of the following:")
        for i in range(len(player_matches)):
            print(f"{i+1}. {player_matches[i].alias}")

        # We'll ask the user to select a number.
        sel = input("Select a number: ")
        try:
            sel = int(sel)
            if sel < 1 or sel > len(player_matches):
                print("Invalid integer input.")
                return players
            
        except:
            print("Invalid non-convertible input.")
            return players

        # We'll select this match, and then move on.
        player = player_matches[sel-1]

    if player.name == "_disenchanted":
        if len(reserves) > 0: 
            confirm = input("This item is reserved. Are you sure it should be disenchanted instead? (y/n): ").lower()
            if confirm != "y":
                print("Aborting.")
                return players
            
        print(f"{item_match.name} ({item_match.ilvl}) has been disenchanted.")
        # Find the disenchanted player. 
        for p in players:
            if p.name == "_disenchanted":
                # Add the item to the player's history list.
                p._raid_log.append(Log(player.name, item_match, "DE", datetime.now().strftime("%Y-%m-%d")))
                p._history[slot_names[int(item_match.slot)]].append(Log(player.name, item_match, "DE", datetime.now().strftime("%Y-%m-%d")))
                return players

    confirm = ""
    
    # If the player isn't on the reserves list, we'll ask to confirm that this is intentional. 
    if len(reserves) > 0 and player.name not in [r[0] for r in reserves]: 
        confirm = input("This person is not on the reserves list. Are you sure this is intentional? (y/n/sr): ").lower()
        if confirm != "y" and confirm != "sr": 
            print("Aborting.")
            return players
        
    elif len(reserves) > 0 and player.name in [r[0] for r in reserves]: 
        confirm = "sr"
        
    # We'll ask the user whether or not this is an off-spec roll, but only if the player is not on the reserves list.
    # If they are, it's a soft-reserve roll. 
    if player.name in [r[0] for r in reserves] or confirm == "sr": 
        roll_type = "SR"

        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        player._reserve_plusses += 1
        player._regular_plusses += 1

        if not raiding: 
            confirm = input("We do not appear to be raiding. Add this to the log manually? (y/n): ").lower()
        else: 
            confirm = "y"
        
        if confirm == "y":
            roll_type = "SR"

            player._history[slot_names[int(item_match.slot)]].append(log)
            # If the item level is 277, we'll also add the 264 version to the history, but only if it's not already there.
            if item_match.ilvl == 277: 
                if not any([item_match.name == log.item.name and log.item.ilvl == 264 for log in player._history[slot_names[int(item_match.slot)]]]):
                    player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 264, item_match.slot), roll_type, datetime.now().strftime("%Y-%m-%d"), "auto"))

            # If the item level is 264, w e'll also add the 251 version to the history, but only if it's not already there.
            elif item_match.ilvl == 264: 
                if not any([item_match.name == log.item.name and log.item.ilvl == 251 for log in player._history[slot_names[int(item_match.slot)]]]):
                    player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 251, item_match.slot), roll_type, datetime.now().strftime("%Y-%m-%d"), "auto"))

    elif slot_names[int(item_match.slot)] != "ETC" or "Mark of Sanctification" in item_match.name: 
        off_spec = input("Is this an off-spec roll? (y/n): ").lower()
        if off_spec == "y": roll_type = "OS"
        else: roll_type = "MS"
    
        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        if not off_spec == "y": player._regular_plusses += 1

        if not raiding: 
            confirm = input("We do not appear to be raiding. Add this to the log manually? (y/n): ").lower()
        else: 
            confirm = "y"

        if confirm == "y": 
            player._history[slot_names[int(item_match.slot)]].append(log)
            # If the item level is 277, we'll also add the 264 version to the history, but only if it's not already there.
            if item_match.ilvl == 277: 
                if not any([item_match.name == log.item.name and log.item.ilvl == 264 for log in player._history[slot_names[int(item_match.slot)]]]):
                    player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 264, item_match.slot), roll_type, datetime.now().strftime("%Y-%m-%d"), "auto"))

            # If the item level is 264, we'll also add the 251 version to the history, but only if it's not already there.
            elif item_match.ilvl == 264: 
                if not any([item_match.name == log.item.name and log.item.ilvl == 251 for log in player._history[slot_names[int(item_match.slot)]]]):
                    player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 251, item_match.slot), roll_type, datetime.now().strftime("%Y-%m-%d"), "auto"))

    else: 
        roll_type = "ETC"
        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)

        if not raiding: 
            confirm = input("We do not appear to be raiding. Add this to the log manually? (y/n): ").lower()
        else:
            confirm = "y"

        if confirm == "y":
            player._history[slot_names[int(item_match.slot)]].append(log)

    print(f"{player.name} has been awarded {item_match.name} ({item_match.ilvl}) as an {roll_type} item.")
        
    return players

known_players = {
    "Ferrousblade": "Death Knight",
    "Sighanama": "Hunter",
    "Strixien": "Druid",
    "Bunniful": "Druid",
    "Lumosbringer": "Paladin",
    "Kelorlyn": "Druid",
    "Catreene": "Paladin",
    "Mettybeans": "Shaman",
    "Sõçkö": "Rogue",
    "Wamili": "Warlock",
    "Pacratt": "Mage",
    "Flambeaü": "Shaman",
    "Jwizard": "Warlock",
    "Killädin": "Paladin",
    "Artaz": "Death Knight",
    "Soulreaverr": "Death Knight",
    "Darkfern": "Death Knight",
    "Swiftbladess": "Rogue",
    "Killiandra": "Mage",
    "Pastiry": "Warrior",
    "Meemeemeemee": "Shaman",
    "Tinyraider": "Mage",
    "Beásty": "Hunter",
    "Axsel": "Warlock",
    "Snedpie": "Priest",
    "Bigpapapaul": "Hunter",
    "Gnoraa": "Warlock",
    "Abletu": "Druid",
    "Bzorder": "Druid",
    "Elisesolis": "Paladin",
    "Prunejuuce": "Warrior",
    "Medulla": "Paladin",
    "Lorniras": "Warlock",
    "Vangoat": "Shaman",
    "Miatotems": "Shaman",
    "Lilypalooza": "Priest",
    "Gnoya": "Priest",
    "Killit": "Warlock",
}

def mark_attendance(players):
    num_present = 0

    for p in players: 
        p._attendance = False

        if p.name == "_disenchanted":
            p._attendance = True

    print("")
    with open("attendance.txt", "r", encoding="utf-8") as file: 
        lines = file.readlines()

    new_players = []

    for ind,val in enumerate(lines):
        if ind == 0: continue
        elif val.startswith("Details!"): continue
        else: 
            name = re.search(r"\d. (.*) \.* \d.*", val).group(1)
            if name not in new_players: new_players.append(name)

    for new_player in new_players:
        if new_player in known_aliases.keys(): 
            alias = known_aliases[new_player]

        else:
            alias = new_player

        if not regular_keyboard(alias):
            print(f"Player name {alias} is not valid. Please input the name manually.")
            new_player = input("Name: ")

        new_player = new_player.title()
        alias = alias.title()

        found = False
        for p in players:
            if p.name == new_player:
                found = True
                break
        
        if not found: 
            if new_player in known_players:
                pclass = known_players[new_player]
                print(f"Player {new_player} not found in dictionary, but found in list of known players. Player class auto-selected as {pclass}.")
                players.append(Player(new_player, alias, [], pclass))

            else:
                pclass = input(f"Could not find player {new_player}. Creating from scratch. What class are they? ")
                if pclass.lower() in "death knight": pclass = "Death Knight"
                elif pclass.lower() in "druid": pclass = "Druid"
                elif pclass.lower() in "hunter": pclass = "Hunter"
                elif pclass.lower() in "mage": pclass = "Mage"
                elif pclass.lower() in "paladin": pclass = "Paladin"
                elif pclass.lower() in "priest": pclass = "Priest"
                elif pclass.lower() in "rogue": pclass = "Rogue"
                elif pclass.lower() in "shaman": pclass = "Shaman"
                elif pclass.lower() in "warlock": pclass = "Warlock"
                elif pclass.lower() in "warrior": pclass = "Warrior"

                players.append(Player(new_player, alias, [], pclass))

        # Find the player in the list of players, and change their _attendance to True. 
        for p in players:
            if p.name == new_player:
                if not p._attendance: num_present += 1
                p._attendance = True
                print(f"HERE: {p.name}")
                break

    print("")
    for p in players: 
        if p._attendance == False and not p.name == "_disenchanted": 
            print(f"ABSENT: {p.name}")

    print(f"\n{num_present} players present.")

    print("")
    return players

def export_history(): 
    # Sort the players by alphabetical order.
    players.sort(key=lambda x: x.name)

    for p in players: 
        for slot in p._history:
            # If the slot is ETC, sort it so that shards are first. 
            if slot == "ETC":
                p._history[slot].sort(key=lambda x: (x.item.name != "Shadowfrost Shard", x.date, x.roll, -x.item.ilvl, x.item.name))
            else: 
                p._history[slot].sort(key=lambda x: (x.date, x.roll, -x.item.ilvl, x.item.name))

    with open("history.txt", "w", encoding="utf-8") as file:
        for player in players: 
            if sum([len(player._history[x]) for x in player._history]) == 0: 
                continue      

            if player.name != "_disenchanted":     
                shards = []
                num_items = []

                # Shards are always in the ETC slot. 
                for item in player._history["ETC"]:
                    if item.item.name == "Shadowfrost Shard": 
                        shards.append(item)

                for slot in player._history:
                    if len(player._history[slot]) == 0: continue
                    for item in player._history[slot]: 
                        if item.note == "auto": continue
                        if item.item.name == "Shadowfrost Shard": continue
                        num_items.append(item)
                file.write(f"{player.name}: {len(num_items)} items.\n")

                shards_written = False 
                for slot in player._history:
                    if len(player._history[slot]) == 0: continue
                    file.write("\n")
                    file.write(f"{slot}:\n")
                    for item in player._history[slot]: 
                        if item.note == "auto": continue
                        # print(item.item.name)
                        if item.item.name == "Shadowfrost Shard" and not shards_written:
                            # Find the item id, this is the key of the item in the dictionary
                            for key, value in all_items.items():
                                if value.name == item.item.name:
                                    link = f"<https://www.wowhead.com/wotlk/item={key}>"
                                    break
                            file.write(f"  \- [{item.item.name} ({len(shards)}x)]({link})\n")
                            shards_written = True

                        elif not item.item.name == "Shadowfrost Shard": 
                            # Find the item id, this is the key of the item in the dictionary
                            for key, value in all_items.items():
                                if value.name == item.item.name:
                                    link = f"<https://www.wowhead.com/wotlk/item={key}>"
                                    break
                            if not "Mark of Sanctification" in item.item.name: 
                                file.write(f"  \- [{item.item.name} ({item.item.ilvl})]({link}) ({item.roll}) ({item.date})\n")
                            else: 
                                file.write(f"  \- [{item.item.name}]({link}) ({item.roll}) ({item.date})\n")
                file.write("----------------------------------------\n")

            else:  
                continue 
                num_items = []

                for slot in player._history:
                    if len(player._history[slot]) == 0: continue
                    for item in player._history[slot]: 
                        if item.note == "auto": continue
                        num_items.append(item)
                file.write(f"{player.name}: {len(num_items)} items.\n")

                for slot in player._history:
                    if len(player._history[slot]) == 0: continue
                    file.write("\n")
                    file.write(f"{slot}:\n")
                    for item in player._history[slot]: 
                        if item.note == "auto": continue
                        # print(item.item.name)

                        # Find the item id, this is the key of the item in the dictionary
                        for key, value in all_items.items():
                            if value.name == item.item.name:
                                link = f"<https://www.wowhead.com/wotlk/item={key}>"
                                break
                        if not "Mark of Sanctification" in item.item.name: 
                            file.write(f"  \- [{item.item.name} ({item.item.ilvl})]({link}) ({item.date})\n")
                        else: 
                            file.write(f"  \- [{item.item.name}]({link})  ({item.date})\n")

                file.write("----------------------------------------\n")
                    
        file.write("Number of tokens received:\n\n")

        file.write("Conqueror's Mark of Sanctification:\n\n")
        for p in players: 
            normal_tokens = 0
            heroic_tokens = 0

            if p._player_class in ["Paladin", "Priest", "Warlock"]:
                for l in p._history["ETC"]:
                    if l.item.name == "Conqueror's Mark of Sanctification (N25)":
                        normal_tokens += 1
                    elif l.item.name == "Conqueror's Mark of Sanctification (H25)":
                        heroic_tokens += 1

            if normal_tokens == 0 and heroic_tokens == 0: continue 
            else: 
                file.write(f"\- {p.name}: {normal_tokens} Normal")
                if heroic_tokens == 0: file.write("\n")
                else: file.write(f", {heroic_tokens} Heroic\n")

        file.write("\nProtector's Mark of Sanctification:\n\n")
        for p in players:
            normal_tokens = 0
            heroic_tokens = 0

            if p._player_class in ["Warrior", "Hunter", "Shaman"]:
                for l in p._history["ETC"]:
                    if l.item.name == "Protector's Mark of Sanctification (N25)":
                        normal_tokens += 1
                    elif l.item.name == "Protector's Mark of Sanctification (H25)":
                        heroic_tokens += 1

            if normal_tokens == 0 and heroic_tokens == 0: continue 
            else: 
                file.write(f"\- {p.name}: {normal_tokens} Normal")
                if heroic_tokens == 0: file.write("\n")
                else: file.write(f", {heroic_tokens} Heroic\n")

        file.write("\nVanquisher's Mark of Sanctification:\n\n")
        for p in players:
            normal_tokens = 0
            heroic_tokens = 0

            if p._player_class in ["Death Knight", "Druid", "Mage", "Rogue"]:
                for l in p._history["ETC"]:
                    if l.item.name == "Vanquisher's Mark of Sanctification (N25)":
                        normal_tokens += 1
                    elif l.item.name == "Vanquisher's Mark of Sanctification (H25)":
                        heroic_tokens += 1

            if normal_tokens == 0 and heroic_tokens == 0: continue 
            else: 
                file.write(f"\- {p.name}: {normal_tokens} Normal")
                if heroic_tokens == 0: file.write("\n")
                else: file.write(f", {heroic_tokens} Heroic\n")

        file.write("----------------------------------------\n")
        file.write("Number of Shadowfrost Shards received:\n\n")
        for p in players: 
            shards = 0
            for l in p._history["ETC"]:
                if l.item.name == "Shadowfrost Shard":
                    shards += 1
            if shards == 0: continue 
            else: 
                file.write(f"\- {p.name}: {shards}\n")

def export_loot(): 
    """
    Export loot received as console output. 
    We will sort players by soft-reserve plusses, then by regular plusses. 
    If there is a tie, we will sort alphabetically by name. 
    Under each name, we'll print out what items they received. 
    """

    # Sort the list of players by soft-reserve plusses, then by regular plusses. 
    # We will sort in descending order; so higher plusses should come first. 
    # If there is a tie, we will sort alphabetically by name. 
    # Names should be sorted alphabetically. 

    # If the mode is "console", output to both console and file.
    # If the mode is "file", output to file only.

    players.sort(key=lambda x: (-x._reserve_plusses, -x._regular_plusses, x.name))
    # The most recent raid was either last Wednesday, or last Sunday -- whichever is closer. This is one-directional; if the closest Wednesday is one day in the future, that doesn't count; that's six days.
    # Exception is if last Wednesday or last Sunday is today -- that is, if the last raid was today. In that case, we want to include it. 

    # Check if today's date is a Wednesday or a Sunday. 
    if datetime.now().weekday() == 2: last_wednesday = datetime.now()
    else: last_wednesday = datetime.now() - timedelta(days=(datetime.now().weekday() - 2) % 7)

    if datetime.now().weekday() == 6: last_sunday = datetime.now()
    else: last_sunday = datetime.now() - timedelta(days=(datetime.now().weekday() - 6) % 7)

    last_raid = (last_wednesday if last_wednesday > last_sunday else last_sunday).strftime("%Y-%m-%d")

    with open("loot.txt", "w", encoding="utf-8") as f:
        
        # If last_raid is WEDNESDAY, print WEDNESDAY's date. Bold the date.
        # If last raid is SUNDAY, print both WEDNESDAY and SUNDAY's date. Bold only Sunday's date. 

        if last_raid == last_wednesday.strftime("%Y-%m-%d"):
            f.write(f"Loot log for **Wednesday, {last_wednesday.strftime('%Y-%m-%d')}**:\n\n")

        elif last_raid == last_sunday.strftime("%Y-%m-%d"):
            f.write(f"Loot log for Wednesday, {last_wednesday.strftime('%Y-%m-%d')} and **Sunday, {last_sunday.strftime('%Y-%m-%d')}**:\n\n")

        # Print out the list of players.
        for p in players:
            # First, check if the player has not won any items; that is, their log is empty.
            # If so, we'll skip them.
            if len(p._raid_log) == 0:
                continue

            # We'll print out the disenchanted player last.
            if p.name == "_disenchanted":
                continue

            # Print out the player's name, and then the number of plusses they have; of both types.
            f.write(f"{p.name} (+{p._regular_plusses} MS) (+{p._reserve_plusses} SR)\n")

            for l in p._raid_log:
                if l.roll == "SR":
                    if "Mark of Sanctification" in l.item.name: 
                        f.write(f"- {l.item.name} (SR) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")
                    else:
                        f.write(f"- {l.item.name} ({l.item.ilvl}) (SR) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")

            for l in p._raid_log:
                if l.roll == "MS":
                    if "Mark of Sanctification" in l.item.name: 
                        f.write(f"- {l.item.name} (MS) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")
                    else: 
                        f.write(f"- {l.item.name} ({l.item.ilvl}) (MS) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")

            for l in p._raid_log:
                if l.roll == "OS":
                    if "Mark of Sanctification" in l.item.name: 
                        f.write(f"- {l.item.name} (OS) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")
                    else: 
                        f.write(f"- {l.item.name} ({l.item.ilvl}) (OS) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")

            for l in p._raid_log:
                if l.roll == "ETC":
                    f.write(f"- {l.item.name} (ETC) -- received on")
                    date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                    f.write(f" {date_string}\n")

            f.write("\n")

        # Print out "_disenchanted" last, but only if they have items.
        for p in players:
            if p.name == "_disenchanted":
                # Check if the player has not won any items; that is, their log is empty.
                # If so, we'll skip them.
                if len(p._raid_log) == 0:
                    continue

                # Print out the player's name.
                f.write(f"{p.name}\n")

                for l in p._raid_log:
                    f.write(f"- {l.item.name}\n")

def remove_loot(players):
    player = input("Enter the name of the player who we are removing from: ").lower()
    player_matches = []
    for p in players:
        if p._attendance == False: continue
        if player in p.alias.lower(): 
            player_matches.append(p)

    if len(player_matches) == 0:
        print("No matches found. Please double-check the player name and try again.")
        return players
    
    elif len(player_matches) == 1:
        # We'll select this match, and then move on.
        player = player_matches[0]

    elif len(player_matches) > 1:
        # We'll print all of the matches, and ask them to select one.
        print("Multiple matches found. Please select one of the following:")
        for i in range(len(player_matches)):
            print(f"{i+1}. {player_matches[i].name}")

        # We'll ask the user to select a number.
        sel = input("Please select a number: ")
        try: 
            sel = int(sel)
            if sel < 1 or sel > len(player_matches):
                print("Invalid integer input.")
                return players
            
        except:
            print("Invalid non-convertible input.")
            return players

        # We'll select this match, and then move on.
        player = player_matches[sel-1]

    # Now, we'll ask the user to select the item they want to remove.
    # We'll print out the list of items they've won, and ask them to select one.

    print("")
    print("Select an item to remove:")
    for i in range(len(player._raid_log)):
        print(f"{i+1}. {player._raid_log[i].item.name} ({player._raid_log[i].item.ilvl}) ({player._raid_log[i].roll})")

    sel = input("Select a number: ")
    try:
        sel = int(sel)
        if sel < 1 or sel > len(player._raid_log):
            print("Invalid integer input.")
            return players
        
    except:
        print("Invalid non-convertible input.")
        return players
    
    # We want to confirm that this is the item that is to be traded. 
    confirm = input(f"Are you sure you want to remove {player._raid_log[sel-1].item.name} ({player._raid_log[sel-1].item.ilvl}) ({player._raid_log[sel-1].roll}) from {player.name}? (y/n): ").lower()
    if confirm != "y": 
        print("Aborting.")
        return players
    
    # We'll check if the item was won through a main-spec roll. If so, we'll decrement regular plusses. 
    # Similarly, if it's through a reserve roll, we'll decrement reserve plusses. 
    if player._raid_log[sel-1].roll == "MS":
        player._regular_plusses -= 1

    elif player._raid_log[sel-1].roll == "SR":
        player._reserve_plusses -= 1
        player._regular_plusses -= 1
    
    # Remove the item from the player's log.
    item = player._raid_log[sel-1]
    player._raid_log.remove(item)

    # Remove the item from the player's history. If it's a 277 item, remove the 264 version as well -- but only if the note is "auto". 

    # We can only check the logs if the item was not disenchanted. 
    if not player.name == "_disenchanted": 

        # We'll check if the item is 277. If so, we'll remove the 264 version as well.
        if item.item.ilvl == 277:
            # First, check if there exists a 264 version of the item in the history; and if so, if the note is "auto". 

            if any([item.item.name == log.item.name and log.item.ilvl == 264 and log.note == "auto" for log in player._history[slot_names[int(item.item.slot)]]]):
                # If so, find the index of the 264 version, and use that to remove it. 
                index = [item.item.name == log.item.name and log.item.ilvl == 264 and log.note == "auto" for log in player._history[slot_names[int(item.item.slot)]]].index(True)
                player._history[slot_names[int(item.item.slot)]].pop(index)

        # We'll check if the item is 264. If so, we'll remove the 251 version as well.
        elif item.item.ilvl == 264:
            # First, check if there exists a 251 version of the item in the history; and if so, if the note is "auto". 

            if any([item.item.name == log.item.name and log.item.ilvl == 251 and log.note == "auto" for log in player._history[slot_names[int(item.item.slot)]]]):
                # If so, find the index of the 251 version, and use that to remove it. 
                index = [item.item.name == log.item.name and log.item.ilvl == 251 and log.note == "auto" for log in player._history[slot_names[int(item.item.slot)]]].index(True)
                player._history[slot_names[int(item.item.slot)]].pop(index)

        index = player._history[slot_names[int(item.item.slot)]].index(item)
        player._history[slot_names[int(item.item.slot)]].pop(index)

    return players

def weekly_reset(players):
    players_with_plusses = [p for p in players if p._regular_plusses > 0 or p._reserve_plusses > 0]
    if len(players_with_plusses) == 0: 
        print("There's nothing to clear!")
        return players

    confirm = input("Are you sure you want to reset the weekly loot? (y/n): ").lower()
    if confirm != "y":
        print("Aborting.")
        return players

    for i in range(len(players)): 
        players[i]._raid_log = []
        players[i]._regular_plusses = 0
        players[i]._reserve_plusses = 0

    return players 

def sudo_mode(players, raiding):
    print("----------------------------------------")
    print("WARNING: Sudo mode is a dangerous mode that allows you to modify a lot of things directly. Use with caution.")
    
    confirm = input("Are you sure you want to enter sudo mode? (y/n): ").lower()
    if confirm != "y":
        print("Aborting.")
        return players, raiding
    
    while(True): 
        print("---- SUDO MODE ----")
        print("a. COMPLETELY wipe the pickle file")
        print("b. Restore history from Gargul export")
        print(f"c. {'Enter' if not raiding else 'Exit'} raiding mode")
        print("d. Exit sudo mode")
        sel = input("Select an option: ").lower()
        print("")

        if sel == "a": 
            print("WARNING: This will completely wipe the pickle file. This cannot be undone.")
            print("Removing the pickle file will affect: ")
            print("  - The loot history")
            print("  - The reserve lists of ALL players")
            print("  - The names of ALL players")
            print("  - The plusses of ALL players")

            confirm = input("Are you sure you want to wipe the pickle file? (y/n): ").lower()
            if confirm == "y":
                os.remove("players.pickle")

            players = []
            players.append(Player("_disenchanted", "_disenchanted", [], ""))

        elif sel == "b":
            with open("gargul-export.txt", "r", encoding="utf-8") as file: 
                lines = file.readlines()

            for p in players: 
                for slot in p._history: 
                    p._history[slot] = []
                p._raid_log = []
                p._regular_plusses = 0
                p._reserve_plusses = 0

            for ind,line in enumerate(lines):
                if ind == 0: continue
                line = line.strip().split(";")

                item_id = int(line[0])
                item_name = line[1]
                ilvl = int(line[2])
                reserved = True if line[3] == "1" else False 
                offspec = True if line[4] == "1" else False
                winner = line[5]
                date = line[6]

                if ilvl <= 263 and not item_name in exceptions: continue

                if winner in known_aliases.keys(): 
                    alias = known_aliases[winner]

                else: 
                    alias = winner

                if not regular_keyboard(alias):
                    print(f"Player name {alias} is not valid. Please input the name manually.")
                    alias = input("Name: ")

                player = None
                for p in players:
                    if p.name == winner: 
                        player = p
                        break

                if item_id == 52025: item_name += " (N25)"
                elif item_id == 52026: item_name += " (N25)"
                elif item_id == 52027: item_name += " (N25)"
                elif item_id == 52028: item_name += " (H25)"
                elif item_id == 52029: item_name += " (H25)"
                elif item_id == 52030: item_name += " (H25)"

                item = None
                for i in all_items.values():
                    if i.name == item_name and i.ilvl == ilvl: 
                        item = i
                        break
                
                if item_id in [50274, 50231, 50226]: 
                    roll_type = "ETC"

                elif "Wrathful Gladiator's" in item_name: 
                    roll_type = "OS"

                else: 
                    roll_type = "SR" if reserved else "OS" if offspec else "MS"
                    
                if player is None: 
                    if winner in known_players:
                        pclass = known_players[winner]
                        print(f"Player {winner} not found in dictionary, but found in list of known players. Player class auto-selected as {pclass}.")
                        players.append(Player(winner, alias, [], pclass))
                        player = players[-1]

                    else: 
                        pclass = input(f"Could not find player {winner}. Creating from scratch. What class are they? ")
                        if pclass.lower() in "death knight": pclass = "Death Knight"
                        elif pclass.lower() in "druid": pclass = "Druid"
                        elif pclass.lower() in "hunter": pclass = "Hunter"
                        elif pclass.lower() in "mage": pclass = "Mage"
                        elif pclass.lower() in "paladin": pclass = "Paladin"
                        elif pclass.lower() in "priest": pclass = "Priest"
                        elif pclass.lower() in "rogue": pclass = "Rogue"
                        elif pclass.lower() in "shaman": pclass = "Shaman"
                        elif pclass.lower() in "warlock": pclass = "Warlock"
                        elif pclass.lower() in "warrior": pclass = "Warrior"

                        players.append(Player(winner, alias, [], pclass))
                        player = players[-1]

                player._history[slot_names[int(item.slot)]].append(Log(player.name, item, roll_type, date))
                print(f"Added {item.name} ({item.ilvl}) [{roll_type}] to {player.name}'s history.")

                # Check if the date is after the last weekly reset, on Tuesday. If so, we must also add this item to their raid log.
                todays_date = datetime.strptime(date, "%Y-%m-%d")
                
                # Take today's date, and subtract the number of days that have elapsed since Tuesday. 
                today = datetime.today()
                days_since_tuesday = (today.weekday() - 1) % 7
                last_tuesday = today - timedelta(days=days_since_tuesday)
                
                if todays_date >= last_tuesday:
                    player._raid_log.append(Log(player.name, item, roll_type, date))
                    if reserved: 
                        player._reserve_plusses += 1
                        player._regular_plusses += 1
                    elif not offspec and not roll_type == "ETC" and not roll_type == "OS": 
                        player._regular_plusses += 1

        elif sel == "c": 
            if raiding: print("Exiting raiding mode.")
            else: print("Entering raiding mode.")
            raiding = not raiding

        elif sel == "d":
            print("Exiting sudo mode.")
            return players, raiding

def export_gargul(players):
    with open("plusses.txt", "w", encoding="utf-8") as file: 
        for p in players: 
            if p._regular_plusses > 0: file.write(f"{p.name},{p._regular_plusses}\n")

def export_chat(players): 
    # Hit alt tab
    pyautogui.moveTo(1920/2, 1080/2)
    pyautogui.click()
    time.sleep(0.1)
    
    pyautogui.typewrite("/")
    time.sleep(0.1)
    pyautogui.typewrite(f"raid")
    time.sleep(0.1)
    pyautogui.press("space")
    time.sleep(0.1)
    pyautogui.typewrite(f"Plusses: ")
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.25)
    
    for p in players: 
        if p._regular_plusses == 0 and p._reserve_plusses == 0: continue
        # Announce in raid chat. 
        pyautogui.typewrite("/")
        time.sleep(0.1)
        pyautogui.typewrite(f"raid")
        time.sleep(0.1)
        pyautogui.press("space")
        time.sleep(0.1)
        pyautogui.typewrite(f"- {p.name}: (+{p._regular_plusses} MS) (+{p._reserve_plusses} SR)")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.25)

    pyautogui.typewrite("/")
    time.sleep(0.1)
    pyautogui.typewrite(f"raid")
    time.sleep(0.1)
    pyautogui.press("space")
    time.sleep(0.1)
    pyautogui.typewrite(f"If your name is not on this list, you don't have any plusses.")
    time.sleep(0.1)
    pyautogui.press("enter")
    time.sleep(0.25)

def paste_history(): 
    # Delete all files in "./history"
    for file in os.listdir("./history"):
        os.remove(f"./history/{file}")
        
    with open("history.txt", "r", encoding="utf-8") as file: 
        lines = file.read()

    lines = lines.split("\n")
    for i in range(len(lines)):
        lines[i] += "\n"

    paste = ""
    total_length = 0
    index = 0

    for line in lines: 
        receiver = line.split("\n")[0]

        if len(line) + total_length < 3900: 
            paste += line
            total_length += len(line)
        
        else: 
            with open(f"./history/paste_{index}.txt", "w", encoding="utf-8") as file:
                file.write(paste)
                index += 1
            paste = line
            total_length = len(line)
    
    with open(f"./history/paste_{index}.txt", "w", encoding="utf-8") as file:
        file.write(paste)

while(True): 
    export_pickle(players)
    
    print("----------------------------------------")
    print(f"Loot Tracker{'' if raiding else ' (Debug Mode)'}")
    print("1) Award loot")
    print("2) Import soft-reserve")
    print("3) Mark attendance")
    print("4) Export THIS RAID's loot to a file")
    print("5) Export the loot history to a file")
    print("6) Split up history into paste-sized chunks")
    print("7) Remove loot, or weekly reset")
    print("8) Export plusses in Gargul style")
    print("9) Export plusses to be pasted into chat")
    print(f"10) Enter sudo mode (edit history, {'enter' if not raiding else 'exit'} raiding mode, enter debug mode)")

    print("")

    try: sel = int(input("Select an option: "))
    except: break

    if sel == 1: players = award_loot(players)
    elif sel == 2: players = import_softreserve(players)
    elif sel == 3: players = mark_attendance(players)
    elif sel == 4: export_loot()
    elif sel == 5: export_history()
    elif sel == 6: paste_history()
    elif sel == 7: 
        print("Choose an option: ")
        print("a) Remove one piece of loot from a player")
        print("b) Weekly reset (clear plusses and raid logs, but not history)")
        sel = input("Select an option: ").lower()

        if sel == "a": remove_loot(players)
        elif sel == "b": players = weekly_reset(players)
        else: print("Invalid option.")
    elif sel == 8: export_gargul(players)
    elif sel == 9: export_chat(players)
    elif sel == 10: players, raiding = sudo_mode(players, raiding)
    else: break