import pickle, re, argparse, os, time, pyautogui, subprocess, pyperclip
from typing import List, Union
from datetime import datetime, timedelta
from contextlib import redirect_stdout as redirect
from io import StringIO

parser = argparse.ArgumentParser()

# Add an argument called "--force-new", "-f" to force the script to create a new pickle file.
parser.add_argument("--force-new", "-f", help="Force the script to create a new pickle file.", action="store_true")

args = parser.parse_args()

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
    def __init__(self, id:int, name:str, ilvl:int, classes:Union[list, str], category:str, bind_type:str, version:str): 
        """
        Create a log entry. ID;Item;Item Level;Classes;Category;Bind;Version
        """
        self.id = id
        self.name = name
        self.ilvl = ilvl
        self.classes = classes 
        self.category = category
        self.bind_type = bind_type
        self.version = version

class Log: 
    def __init__(self, name, item:Item, roll_type, date:str, note:str = None): 
        """
        Create a log entry.
        - Name: The name of the player
        - Item: The Item object of what was awarded
        - Roll: Roll type (MS, OS)
        - Date: The date the item was awarded
        """

        self.name = name
        self.item = item
        self.roll = roll_type
        self.date = date
        self.note = note

class Player: 
    def __init__(self, name:str, alias:str, pclass:str):
        self.name = name
        self.alias = alias
        self._player_class = pclass

        self._regular_plusses = 0
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

all_items = {}

def match_category(category:str): 
    valid_categories = ["ETC", "Head", "Neck", "Shoulder", "Back", "Chest", "Wrist", "Hands", "Waist", "Legs", "Feet", "Ring", "Trinket", "Main-Hand", "Off-Hand", "Two-Hand", "Ranged", "Relic"]
    
    if re.match(r"(Cloth|Leather|Mail|Plate)", category, re.IGNORECASE): category = category.split(" ")[1]
    elif re.match(r"(One-Hand|Daggers|Fist Weapons)", category, re.IGNORECASE): category = "Main-Hand"
    elif re.match(r"(Two-Hand|Staves|Polearms)", category, re.IGNORECASE): category = "Two-Hand"
    elif re.match(r"(Held In Off-hand|Off hand)", category, re.IGNORECASE): category = "Off-Hand"
    elif re.match(r"(Bows|Thrown|Crossbows|Guns|Wands)", category, re.IGNORECASE): category = "Ranged"
    elif re.match(r"Finger", category, re.IGNORECASE): category = "Ring"
    elif re.match(r"Back", category, re.IGNORECASE): category = "Back"
    elif re.match(r"Neck", category, re.IGNORECASE): category = "Neck"
    elif re.match(r"Trinket", category, re.IGNORECASE): category = "Trinket"
    elif re.match(r"Relic", category, re.IGNORECASE): category = "Relic"

    if category not in valid_categories: category = "ETC"

    return category

def armor_subtype(text, base_type): 
    text = text.lower()

    if "spirit" in text and "intellect" in text: return f"{base_type} (Healing)"

    elif "hit" in text:
        if "intellect" in text: return f"{base_type} (Caster)" 
        else: return f"{base_type} (Damage)"

    elif "expertise" in text: 
        if "agility" in text: return f"{base_type} (Melee Agility)"
        elif "strength" in text: return f"{base_type} (Melee Strength)"

    elif "dodge" in text or "parry" in text: return f"{base_type} (Tank)"

    elif "intellect" in text: return f"{base_type} (Intellect)"
    elif "agility" in text: return f"{base_type} (Agility)"
    elif "strength" in text: return f"{base_type} (Strength)"

    else: return f"{base_type}"

def match_suffix(item_name, base_type): 
    item_name = item_name.lower()
    if "fireflash" in item_name: return armor_subtype("Stamina, Intellect, Critical Strike, Haste", base_type)
    elif "feverflare" in item_name: return armor_subtype("Stamina, Intellect, Haste, Mastery", base_type)
    elif "faultline" in item_name: return armor_subtype("Stamina, Strength, Haste, Mastery", base_type)
    elif "landslide" in item_name: return armor_subtype("Stamina, Strength, Hit, Expertise", base_type)
    elif "earthshaker" in item_name: return armor_subtype("Stamina, Strength, Hit, Critical Strike", base_type)
    elif "earthfall" in item_name: return armor_subtype("Stamina, Strength, Critical Strike, Haste", base_type)
    elif "undertow" in item_name: return armor_subtype("Stamina, Intellect, Haste, Spirit", base_type)
    elif "wavecrest" in item_name: return armor_subtype("Stamina, Intellect, Mastery, Spirit", base_type)
    elif "earthbreaker" in item_name: return armor_subtype("Stamina, Strength, Critical Strike, Mastery", base_type)
    elif "wildfire" in item_name: return armor_subtype("Stamina, Intellect, Hit, Critical Strike", base_type)
    elif "flameblaze" in item_name: return armor_subtype("Stamina, Intellect, Mastery, Hit", base_type)
    elif "zephyr" in item_name: return armor_subtype("Stamina, Agility, Haste, Mastery", base_type)
    elif "windstorm" in item_name: return armor_subtype("Stamina, Agility, Critical Strike, Mastery", base_type)
    elif "stormblast" in item_name: return armor_subtype("Stamina, Agility, Hit, Critical Strike", base_type)
    elif "galeburst" in item_name: return armor_subtype("Stamina, Agility, Hit, Expertise", base_type)
    elif "windflurry" in item_name: return armor_subtype("Stamina, Agility, Critical Strike, Haste", base_type)
    elif "bouldercrag" in item_name: return armor_subtype("Stamina, Strength, Dodge, Parry", base_type)
    elif "rockslab" in item_name: return armor_subtype("Stamina, Strength, Mastery, Dodge", base_type)
    elif "bedrock" in item_name: return armor_subtype("Stamina, Strength, Mastery, Parry", base_type)
    elif "mountainbed" in item_name: return armor_subtype("Stamina, Strength, Mastery, Expertise", base_type)
    else: return "Unknown"

with open("all-items-cata.scsv", "r", encoding="utf-8") as cata_file: 
    cata_items = cata_file.readlines()
    for ind,item in enumerate(cata_items):
        if ind == 0: continue # Header 
        # ID;Item;Item Level;Classes;Category;Bind;Version
        item = item.strip().split(";")
        item_id = int(item[0])
        name = item[1]
        item_level = int(item[2])
        classes = item[3].split(", ") if "," in item[3] else item[3]
        category = item[4]
        bind_type = item[5]
        version = item[6]

        all_items[item_id] = Item(item_id, name, item_level, classes, category, bind_type, version)

def import_pickle(): 
    # Import the pickle file
    try: 
        with open('players_cata.pickle', 'rb') as f:
            players = pickle.load(f)

    except FileNotFoundError:
        print('No pickle file found. Creating a new one.')
        players = []
        players.append(Player("_disenchanted", "_disenchanted", ""))

    return players

def export_pickle(players):
    # Export the pickle file
    with open('players_cata.pickle', 'wb') as f:
        pickle.dump(players, f)

# We'll import the pickle if the "--force-new" argument is not present.
if not args.force_new:
    players = import_pickle()
else:
    players = []

    # Create a special player called "_disenchanted", for items that were not awarded to anyone.
    # This is used when no one rolls. 
    players.append(Player("_disenchanted", "_disenchanted", ""))

with open("known-players.scsv", "r", encoding="utf-8") as f:
    known_players = [line.strip().split(";") for ind,line in enumerate(f.readlines()) if ind > 0]
    known_aliases = {x[0]: x[1] for x in known_players}
    known_players = {x[0]: x[2] for x in known_players}

    # Check if these players are in the list of players. If not, add them.
    for player in known_players.keys():
        found = False
        for p in players:
            if p.name == player:
                found = True
                break

        if not found:
            players.append(Player(player, known_aliases[player], known_players[player]))

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

    if "Random" in item_match.category: 
        prefix = input("Item subcategory is random. What's the prefix? ")
        item_match.category = match_suffix(prefix, item_match.category)
        item_match.name = f"{item_match.name} of the {prefix}"

    slot_category = match_category(item_match.category)
    item_match.category = item_match.category.replace(" (Random)", "")

    for p in players: 
        # Skip this person if they're not here.
        if p._attendance == False: continue

    print(f"Item: {item_match.name} ({item_match.ilvl}) -- {item_match.category}")
    if item_match.classes != "": print(f"Classes: {', '.join(item_match.classes)}")

    ready = input("Ready to announce? (y/n): ").lower()
    if ready == "y": 
        pyautogui.moveTo(1920/2, 1080/2)
        pyautogui.click()
        time.sleep(0.25)

        pyautogui.write("/")
        time.sleep(0.1)
        pyautogui.write("rw")
        time.sleep(0.1)
        pyautogui.press("space")
        time.sleep(0.1)
        pyautogui.write(f"Item: {item_match.name} ({item_match.ilvl}) -- {item_match.category}")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.25)

        if item_match.classes != "":
            pyautogui.write("/")
            time.sleep(0.1)
            pyautogui.write("rw")
            time.sleep(0.1)
            pyautogui.press("space")
            time.sleep(0.1)
            pyautogui.write(f"Classes: {', '.join(item_match.classes)}")
            time.sleep(0.1)
            pyautogui.press("enter")
            time.sleep(0.25)

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
        print(f"{item_match.name} ({item_match.ilvl}) has been disenchanted.")
        # Find the disenchanted player. 
        for p in players:
            if p.name == "_disenchanted":
                # Add the item to the player's history list.
                p._raid_log.append(Log(player.name, item_match, "DE", datetime.now().strftime("%Y-%m-%d")))
                p._history[slot_category].append(Log(player.name, item_match, "DE", datetime.now().strftime("%Y-%m-%d")))
                return players

    exceptions = [
        "Mantle of the Forlorn Protector",
        "Mantle of the Forlorn Vanquisher",
        "Mantle of the Forlorn Conqueror",
        "Helm of the Forlorn Protector",
        "Helm of the Forlorn Vanquisher",
        "Helm of the Forlorn Conqueror",
    ]

    if "(PvP)" in item_match.category:
        roll_type = "OS"

        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        player._history[slot_category].append(log)

    elif slot_category != "ETC" or item_match.name in exceptions: 
        off_spec = input("Is this an off-spec roll? (y/n): ").lower()
        if off_spec == "y": roll_type = "OS"
        else: roll_type = "MS"
    
        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        if not off_spec == "y": player._regular_plusses += 1

        player._history[slot_category].append(log)

    else: 
        roll_type = "OS"
        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)

        player._history[slot_category].append(log)

    print(f"{player.name} has been awarded {item_match.name} ({item_match.ilvl}) as an {roll_type} item.")
        
    return players

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
                players.append(Player(new_player, alias, pclass))

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

                players.append(Player(new_player, alias, pclass))

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
                num_items = []

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

def export_loot(): 
    # Sort the list of players by regular plusses. 
    # We will sort in descending order; so higher plusses should come first. 
    # If there is a tie, we will sort alphabetically by name. 
    # Names should be sorted alphabetically. 

    # If the mode is "console", output to both console and file.
    # If the mode is "file", output to file only.

    players.sort(key=lambda x: (-x._regular_plusses, x.name))
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
            f.write(f"{p.name} (+{p._regular_plusses} MS)\n")

            for l in p._raid_log:
                if l.roll == "MS":
                    if re.match(r"(Conqueror|Protector|Vanquisher)", l.item.name):
                        f.write(f"- {l.item.name} (MS) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")
                    else: 
                        f.write(f"- {l.item.name} ({l.item.ilvl}) (MS) -- received on")
                        date_string = f"{l.date}" if l.date != last_raid else f"**{l.date}**"
                        f.write(f" {date_string}\n")

            for l in p._raid_log:
                if l.roll == "OS":
                    if re.match(r"(Conqueror|Protector|Vanquisher)", l.item.name):
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
    if player._raid_log[sel-1].roll == "MS":
        player._regular_plusses -= 1
    
    # Remove the item from the player's log.
    item = player._raid_log[sel-1]
    player._raid_log.remove(item)

    # We can only check the logs if the item was not disenchanted. 
    if not player.name == "_disenchanted": 
        slot_category = match_category(item.item.category)

        index = player._history[slot_category].index(item)
        player._history[slot_category].pop(index)

    return players

def weekly_reset(players):
    players_with_plusses = [p for p in players if p._regular_plusses > 0]
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

    return players 

def sudo_mode(players):
    print("----------------------------------------")
    print("WARNING: Sudo mode is a dangerous mode that allows you to modify a lot of things directly. Use with caution.")
    
    confirm = input("Are you sure you want to enter sudo mode? (y/n): ").lower()
    if confirm != "y":
        print("Aborting.")
        return players
    
    while(True): 
        print("---- SUDO MODE ----")
        print("a. COMPLETELY wipe the pickle file")
        print("b. Restore history from Gargul export")
        print("c. Create Gargul export")
        print("d. Export list of known players")
        print("e. Exit sudo mode")
        sel = input("Select an option: ").lower()
        print("")

        if sel == "a": 
            print("WARNING: This will completely wipe the pickle file. This cannot be undone.")
            print("Removing the pickle file will affect: ")
            print("  - The loot history")
            print("  - The names of ALL players")
            print("  - The plusses of ALL players")

            confirm = input("Are you sure you want to wipe the pickle file? (y/n): ").lower()
            if confirm == "y":
                os.remove("players_cata.pickle")

            players = []
            players.append(Player("_disenchanted", "_disenchanted", ""))

        elif sel == "b":
            with open("gargul-export.scsv", "r", encoding="utf-8") as file: 
                lines = file.readlines()

            for p in players: 
                for slot in p._history: 
                    p._history[slot] = []
                p._raid_log = []
                p._regular_plusses = 0

            for ind,line in enumerate(lines):
                if ind == 0: continue
                line = line.strip().split(";")

                item_id = int(line[0])
                item_name = line[1]
                ilvl = int(line[2])
                offspec = True if line[3] == "1" else False
                winner = line[4]
                date = line[5]

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

                item = None
                for i in all_items.values():
                    if i.name == item_name and i.ilvl == ilvl: 
                        item = i
                        break

                if "Gladiator" in item_name:
                    roll_type = "OS"
                else:
                    roll_type = "OS" if offspec else "MS"
                    
                if player is None: 
                    if winner in known_players:
                        pclass = known_players[winner]
                        print(f"Player {winner} not found in dictionary, but found in list of known players. Player class auto-selected as {pclass}.")
                        players.append(Player(winner, alias, pclass))
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

                        players.append(Player(winner, alias, pclass))
                        player = players[-1]

                player._history[match_category(item.category)].append(Log(player.name, item, roll_type, date))
                print(f"Added {item.name} ({item.ilvl}) [{roll_type}] to {player.name}'s history.")

                # Check if the date is after the last weekly reset, on Tuesday. If so, we must also add this item to their raid log.
                todays_date = datetime.strptime(date, "%Y-%m-%d")
                
                # Take today's date, and subtract the number of days that have elapsed since Tuesday. 
                today = datetime.today()
                days_since_tuesday = (today.weekday() - 1) % 7
                last_tuesday = today - timedelta(days=days_since_tuesday)
                
                if todays_date >= last_tuesday:
                    player._raid_log.append(Log(player.name, item, roll_type, date))
                    if not offspec and not roll_type == "ETC" and not roll_type == "OS": 
                        player._regular_plusses += 1

        elif sel == "c": 
            with open(f"partial-export.scsv", "w", encoding="utf-8") as file: 
                file.write("@ID;@ITEM;@ILVL;@OS;@WINNER;@YEAR-@MONTH-@DAY\n")
                for p in players: 
                    # For each item in their loot log, write out;
                    # @ID;@ITEM;@ILVL;@OS;@WINNER;@YEAR-@MONTH-@DAY
                    # 50274;Shadowfrost Shard;0;0;Pastiry;2024-04-24
                    for item in p._raid_log: 
                        item_id = 0

                        for key, value in all_items.items():
                            if value.name == item.item.name and value.ilvl == item.item.ilvl:
                                item_id = key
                                break

                        offspec = 1 if item.roll == "OS" else 0
                        file.write(f"{item_id};{item.item.name};{item.item.ilvl};{offspec};{p.name};{item.date}\n")

        elif sel == "d": 
            with open("known-players.scsv", "w", encoding="utf-8") as file: 
                file.write("Name,Alias,Class\n")
                for p in players: 
                    if p.name == "_disenchanted": continue
                    file.write(f"{p.name};{p.alias};{p._player_class}\n")

        elif sel == "e":
            print("Exiting sudo mode.")
            return players

def export_gargul(players):
    with open("plusses.csv", "w", encoding="utf-8") as file: 
        for p in players: 
            if p.name == "_disenchanted": continue
            if p._regular_plusses > 0: file.write(f"{p.name},{p._regular_plusses}\n")

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
    index = 1
    threshold = 3800

    for line in lines: 
        if len(line) + total_length < threshold: 
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
    print(f"Loot Tracker")
    print("1) Award loot")
    print("2) Mark attendance")
    print("3) Export THIS RAID's loot to a file")
    print("4) Export the loot history to a file")
    print("5) Split up history into paste-sized chunks")
    print("6) Remove loot, or weekly reset")
    print("7) Export plusses in Gargul style")
    print("8) Enter sudo mode")

    print("")

    try: sel = int(input("Select an option: "))
    except: break

    if sel == 1: players = award_loot(players)
    elif sel == 2: players = mark_attendance(players)
    elif sel == 3: export_loot()
    elif sel == 4: export_history()
    elif sel == 5: paste_history()
    elif sel == 6: 
        print("Choose an option: ")
        print("a) Remove one piece of loot from a player")
        print("b) Weekly reset (clear plusses and raid logs, but not history)")
        sel = input("Select an option: ").lower()

        if sel == "a": remove_loot(players)
        elif sel == "b": players = weekly_reset(players)
        else: print("Invalid option.")
    elif sel == 7: export_gargul(players)
    elif sel == 8: players = sudo_mode(players)
    else: break