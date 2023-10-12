import pickle, requests, re, argparse, os, random
from typing import List, Union

parser = argparse.ArgumentParser()

# Add an argument called "--force-new", "-f" to force the script to create a new pickle file.
parser.add_argument("--force-new", "-f", help="Force the script to create a new pickle file.", action="store_true")

args = parser.parse_args()

from datetime import datetime

# Raid times: Wednesday, 6:00pm to 9:00pm; Sunday, 4:00pm to 7:00pm. 
# We'll use the current date and time to determine whether or not we're currently raiding. If we are NOT, we'll use debug mode. 
if datetime.now().weekday() == 2 and datetime.now().hour >= 18 and datetime.now().hour < 21: 
    raiding = True

elif datetime.now().weekday() == 6 and datetime.now().hour >= 16 and datetime.now().hour < 19:
    raiding = True

else:
    raiding = False

print("Raiding:", raiding)

class Item: 
    def __init__(self, name:str, ilvl:int, slot:int): 
        self.name = name
        self.ilvl = ilvl 
        self.slot = slot

class Log: 
    def __init__(self, name, item:Item, roll_type, date:str, note:str = None): 
        """
        Create a log entry.
        - Name: The name of the player
        - Item: The Item object of what was awarded
        - Roll: Roll type (MS, OS, soft reserve)
        - Date: The date the item was awarded
        """

        self.name = name
        self.item = item
        self.roll = roll_type
        self.date = date
        self.note = note

class Player: 
    def __init__(self, name:str,  soft_reserve:List[str]):
        self.name = name
        self.soft_reserve = soft_reserve

        self._regular_plusses = 0
        self._soft_reserve_plusses = 0

        self._raid_log = []
        self._history = {
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
            "ETC": []
        }

with open('items.sql') as items_file: 
    items = items_file.read()
    items = items.replace("'", '"')
    items = items.replace('\\"', "'")
    items = items.splitlines()

    with open("all_items.txt", 'w') as file: 
        for item in items: 
            file.write(f"{item}\n")

all_items = {}
# (50008,"Ring of Rapid Ascent",64170,4,11,-1,264,80,0),
# Capture the item ID, name, inventory type, and item level.
pattern = re.compile(r'\((\d+),\"(.+)\",\d+,\d+,(\d+),-?\d+,(\d+),\d+,\d+\),?')
slots = {}

for item in items:
    match = pattern.match(item)
    if match: 
        item_id = int(match.group(1))
        name = match.group(2)
        item_level = int(match.group(4))
        inventory_type = int(match.group(3))

        if item_level < 200: continue

        all_items[item_id] = Item(name, item_level, inventory_type)

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

with open("slots.txt", "w") as file: 
    for slot in slot_names: 
        file.write(f"{slot}: {slot_names[slot]}\n")
        for item in slots[slot]: 
            file.write(f"  - {item.name} ({item.ilvl})\n")

def import_pickle() -> list: 
    # Import the pickle file
    try: 
        with open('players.pickle', 'rb') as f:
            players = pickle.load(f)

    except FileNotFoundError:
        print('No pickle file found. Creating a new one.')
        players = []

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
    players.append(Player("_disenchanted", []))

def import_softreserve(players): 
    # We'll attempt to import soft reserve data from the CSV file. 
    if not os.path.exists("soft_reserves.csv"):
        print("No soft reserve file found. Skipping.")
        return players

    with open("soft_reserves.csv", "r") as f: 
        sr_data = f.readlines()

    # Parse the data. 
    for soft_res in sr_data: 
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

        # Exception: If the name is "Class", skip it.
        if name == "Class":
            continue

        # Exception: If the name is "KÃ­llit", change it to "Killit". Special characters are not allowed.
        if name == "KÃ­llit":
            name = "Killit"

        # Search for an existing player object. Create it if it doesn't exist. 

        # Check if the player is in the list of players. 
        # If so, wipe their soft reserve. 
        player_exists = False
        current_player = None
        for p in players: 
            if p.name == name: 
                player_exists = True
                current_player = p
                current_player.soft_reserve = []
                break
        
        if not player_exists: 
            # Create a new player object and append it the list. 
            players.append(Player(name, []))
            current_player = players[-1]

        # Add the item to the player's soft reserve list.
        current_player.soft_reserve.append(item)

    return players

players = import_softreserve(players)

def print_write(string, file=None):
    print(string)
    if file:
        file.write(string + "\n")

def regular_keyboard(input_string): 
    pattern = r"^[A-Za-z0-9 !@#$%^&*()\-=\[\]{}|;:'\",.<>/?\\_+]*$"
    return re.match(pattern, input_string) is not None 

def award_loot(players): 
    print("----------------------------------------")
    # First, we'll ask what item we're rolling off; supporting both case insensitivity and partial matching. 
    item = input("What item are we rolling off? ").lower()
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

    # We'll check the soft-reserves to see if anyone has this item soft-reserved, excluding anyone who has already won the same item, with the same item level. 
    # For example, Ring of Rapid Ascent (264) and Ring of Rapid Ascent (277) are considered different items.
    # We need to check the corresponding _history list, which is categorized based on slot. 

    reserves = []
    for p in players: 
        if item_match.name in p.soft_reserve and not any([item_match.name == log.item.name and item_match.ilvl == log.item.ilvl for log in p._history[slot_names[int(item_match.slot)]]]): 
            reserves.append((p.name, p._soft_reserve_plusses))
    
    if len(reserves) > 0:
        print("")
        print("The following people have soft-reserved this item:")
        for r in reserves: 
            print(f"  - {r[0]} (SR +{r[1]})")
            
    print("")
    # We'll ask the user to input the name of the person who won the roll. 
    name = input("Who won the roll? ").lower()
    if name == "": return players

    player_matches = []
    for p in players:
        if name in p.name.lower(): 
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

    # If the player isn't on the reserves list, we'll ask to confirm that this is intentional. 
    if len(reserves) > 0 and player.name not in [r[0] for r in reserves]: 
        confirm = input("This person is not on the reserves list. Are you sure this is intentional? (y/n) ").lower()
        if confirm != "y": 
            print("Aborting.")
            return players
        
    # We'll ask the user whether or not this is an off-spec roll, but only if the player is not on the reserves list.
    # If they are, it's a soft-reserve roll. 
    if player.name in [r[0] for r in reserves]: 
        log = Log(player.name, item_match, "SR", datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        player._soft_reserve_plusses += 1

        if not raiding: 
            confirm = input("We do not appear to be raiding. Add this to the log manually? (y/n): ").lower()
            if confirm == "y":
                player._history[slot_names[int(item_match.slot)]].append(log)
                # If the item level is 277, we'll also add the 264 version to the history, but only if it's not already there.
                if item_match.ilvl == 277: 
                    if not any([item_match.name == log.item.name and log.item.ilvl == 264 for log in player._history[slot_names[int(item_match.slot)]]]):
                        player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 264, item_match.slot), "SR", datetime.now().strftime("%Y-%m-%d"), "auto"))

        else: 
            player._history[slot_names[int(item_match.slot)]].append(log)
            # If the item level is 277, we'll also add the 264 version to the history, but only if it's not already there.
            if item_match.ilvl == 277: 
                if not any([item_match.name == log.item.name and log.item.ilvl == 264 for log in player._history[slot_names[int(item_match.slot)]]]):
                    player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 264, item_match.slot), "SR", datetime.now().strftime("%Y-%m-%d"), "auto"))
    else: 
        off_spec = input("Is this an off-spec roll? (y/n) ").lower()
        if off_spec == "y": roll_type = "OS"
        else: roll_type = "MS"
    
        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        if not off_spec: player._regular_plusses += 1

        if not raiding: 
            confirm = input("We do not appear to be raiding. Add this to the log manually? (y/n): ").lower()
            if confirm == "y":
                player._history[slot_names[int(item_match.slot)]].append(log)
                # If the item level is 277, we'll also add the 264 version to the history, but only if it's not already there.
                if item_match.ilvl == 277: 
                    if not any([item_match.name == log.item.name and log.item.ilvl == 264 for log in player._history[slot_names[int(item_match.slot)]]]):
                        player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 264, item_match.slot), roll_type, datetime.now().strftime("%Y-%m-%d"), "auto"))

        else: 
            player._history[slot_names[int(item_match.slot)]].append(log)
            # If the item level is 277, we'll also add the 264 version to the history, but only if it's not already there.
            if item_match.ilvl == 277: 
                if not any([item_match.name == log.item.name and log.item.ilvl == 264 for log in player._history[slot_names[int(item_match.slot)]]]):
                    player._history[slot_names[int(item_match.slot)]].append(Log(player.name, Item(item_match.name, 264, item_match.slot), roll_type, datetime.now().strftime("%Y-%m-%d"), "auto"))
        
    return players
        
def add_players_manual(players):
    # Ask the user to enter the name of the new player. This can be done in any case; but partial matching is not supported.
    new_players = input("Enter the names of up to 25 new players: ")
    
    # We'll check to see how many players there are, by splitting with spaces. 
    if ' ' in new_players: new_players = new_players.split(" ")
    else: new_players = [new_players]

    for new_player in new_players: 
        
        if not regular_keyboard(new_player):
            print(f"Player name {new_player} is not valid. Please input the name manually.")
            new_player = input("Name: ")

        # Convert to sentence case. 
        new_player = new_player.title()
        if len(new_player) > 12: 
            print(f"ERROR: {new_player} is too long. Please enter a name that is 12 characters or less.")
            continue

        # Check if the player already exists. If so, print out an error message and continue.
        found = False
        for p in players:
            if p.name == new_player:
                found = True
                continue
        
        if not found: 
            # If not, create a new player object and add it to the list of players.
            players.append(Player(new_player, []))
            print(f"ADDED: {new_player}")

        else: 
            print(f"ERROR: {new_player} already exists.")
    
    return players

def add_players_details(players):
    print("")
    with open("details.txt", "r") as file: 
        lines = file.readlines()

    import re
    new_players = []

    for ind,val in enumerate(lines):
        if ind == 0: continue
        else: 
            name = re.search(r"\d. (.*) \.* \d.*", val).group(1)
            new_players.append(name)

    for new_player in new_players: 
        
        if not regular_keyboard(new_player):
            print(f"Player name {new_player} is not valid. Please input the name manually.")
            new_player = input("Name: ")

        new_player = new_player.title()
        if len(new_player) > 12: 
            print(f"ERROR: {new_player} is too long. Please enter a name that is 12 characters or less.")
            continue

        found = False
        for p in players:
            if p.name == new_player:
                found = True
                continue
        
        if not found: 
            players.append(Player(new_player, []))
            print(f"ADDED: {new_player}")

        else: 
            print(f"ERROR: {new_player} already exists.")
    print("")
    return players

def print_history(): 
    print("----------------------------------------")
    # Ask the user to input the name of the player.
    name = input("Whose history are we checking? ").lower()

    player_matches = []
    for p in players:
        if name in p.name.lower(): 
            player_matches.append(p)
    
    if len(player_matches) == 0:
        print("No matches found. Please double-check the player name and try again.")
        return
    
    elif len(player_matches) == 1:
        # We'll select this match, and then move on.
        player = player_matches[0]

    elif len(player_matches) > 1:
        # We'll print all of the matches, and ask them to select one.
        print("Multiple matches found. Please select one of the following:")
        for i in range(len(player_matches)):
            print(f"{i+1}. {player_matches[i].name}")

        # We'll ask the user to select a number.
        sel = input("Select a number: ")
        try:
            sel = int(sel)
            if sel < 1 or sel > len(player_matches):
                print("Invalid integer input.")
                return
            
        except:
            print("Invalid non-convertible input.")
            return

        # We'll select this match, and then move on.
        player = player_matches[sel-1]

    # First, check if the player has received ANY items. Check the number of items in all their different _history lists. If not, print a message and exit.
    if sum([len(player._history[x]) for x in player._history]) == 0: 
        print(f"{player.name} has not received any items.")
        return
    
    # Otherwise, print out the history of the player. Print out the total number of items they've received, and then print out the items in each slot. Skip slots that are empty, or items that have the note "auto" attached to them. 

    num_items = []
    for slot in player._history:
        if len(player._history[slot]) == 0: continue
        for item in player._history[slot]: 
            # if item.note == "auto": continue
            num_items.append(item)
    print(f"{player.name} has received {len(num_items)} items.")

    print("")
    for slot in player._history:
        if len(player._history[slot]) == 0: continue
        print(f"{slot}:")
        for item in player._history[slot]: 
            # if item.note == "auto": continue
            print(f"  - {item.item.name} ({item.item.ilvl}) ({item.roll}) ({item.date})")

def export_history(): 
    with open("history.txt", "w") as file:
        for player in players: 
            if sum([len(player._history[x]) for x in player._history]) == 0: 
                continue
            
            num_items = []
            for slot in player._history:
                if len(player._history[slot]) == 0: continue
                for item in player._history[slot]: 
                    if item.note == "auto": continue
                    num_items.append(item)
            file.write(f"{player.name}: {len(num_items)} items.\n")

            file.write("\n")
            for slot in player._history:
                if len(player._history[slot]) == 0: continue
                file.write(f"{slot}:\n")
                for item in player._history[slot]: 
                    if item.note == "auto": continue
                    file.write(f"  - {item.item.name} ({item.item.ilvl}) ({item.roll}) ({item.date})\n")
            file.write("----------------------------------------\n")

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

    players.sort(key=lambda x: (-x._soft_reserve_plusses, -x._regular_plusses, x.name))

    with open("loot.txt", "w") as f:
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
            f.write(f"{p.name} (+{p._regular_plusses} MS) (+{p._soft_reserve_plusses} SR)\n")

            for l in p._raid_log:
                if l.roll == "MS":
                    f.write(f"- {l.item.name} (MS)\n")

            for l in p._raid_log:
                if l.roll == "OS":
                    f.write(f"- {l.item.name} (OS)\n")

            for l in p._raid_log:
                if l.roll == "SR":
                    f.write(f"- {l.item.name} (SR)\n")

            for l in p._raid_log:
                if l.roll == "ETC":
                    f.write(f"- {l.item.name} (ETC)\n")

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
    player = input("Enter the name of the player who we're removing loot from: ").lower()
    player_matches = []
    for p in players:
        if player in p.name.lower(): 
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
    
    # We want to confirm that the user wants to remove this item.
    confirm = input(f"Are you sure you want to remove {player._raid_log[sel-1].item.name} ({player._raid_log[sel-1].item.ilvl}) ({player._raid_log[sel-1].roll}) from {player.name}'s log? (y/n) ").lower()
    if confirm != "y": 
        print("Aborting.")
        return players
    
    # Remove the item from the player's log.
    item = player._raid_log[sel-1]
    player._raid_log.remove(item)

    # Remove the item from the player's history. If it's a 277 item, remove the 264 version as well -- but only if the note is "auto". 

    # We'll check if the item is 277. If so, we'll remove the 264 version as well.
    if item.item.ilvl == 277:
        # First, check if there exists a 264 version of the item in the history; and if so, if the note is "auto". 

        if any([item.item.name == log.item.name and log.item.ilvl == 264 and log.note == "auto" for log in player._history[slot_names[int(item.item.slot)]]]):
            # If so, find the index of the 264 version, and use that to remove it. 
            index = [item.item.name == log.item.name and log.item.ilvl == 264 and log.note == "auto" for log in player._history[slot_names[int(item.item.slot)]]].index(True)
            player._history[slot_names[int(item.item.slot)]].pop(index)

    index = player._history[slot_names[int(item.item.slot)]].index(item)
    player._history[slot_names[int(item.item.slot)]].pop(index)

def weekly_reset(players):
    confirm = input("Are you sure you want to reset the weekly loot? (y/n) ").lower()
    if confirm != "y":
        print("Aborting.")
        return players

    for p in players: 
        p._raid_log = []
        p._regular_plusses = 0
        p._soft_reserve_plusses = 0

    return players 

while(True): 
    print("----------------------------------------")
    print("Asylum of the Immortals Loot Tracker")
    print("1) Award loot")
    print("2) Add players, manually or from details.txt")
    print("3) Print out the history of a given player")
    print("4) Export the loot history to a file")
    print("5) Export THIS RAID's loot to a file")
    print("6) Remove loot, or weekly reset")
    print("7) Log a trade")

    print("")

    try: sel = int(input("Select an option: "))
    except: break

    if sel == 1: players = award_loot(players)
    elif sel == 2: 
        print("Choose an option: ")
        print("a) Add one or more players manually")
        print("b) Add all players from the details.txt file")
        sel = input("Select an option: ").lower()

        if sel == "a": players = add_players_manual(players)
        elif sel == "b": players = add_players_details(players)
        else: print("Invalid option.")
    elif sel == 3: print_history()
    elif sel == 4: export_history()
    elif sel == 5: export_loot()
    elif sel == 6: 
        print("Choose an option: ")
        print("a) Remove one piece of loot from a player")
        print("b) Weekly reset (clear plusses and raid logs, but not history)")

        if sel == "a": remove_loot(players)
        elif sel == "b": players = weekly_reset(players)
        else: print("Invalid option.")
    else: break

    export_pickle(players)