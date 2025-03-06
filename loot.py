import pickle, re, argparse, os, time, pyautogui, subprocess, pytesseract
from typing import List, Union
from datetime import datetime, timedelta
from contextlib import redirect_stdout as redirect
from io import StringIO
from items import armor_subtype, match_category

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
    def __init__(self, id:int, name:str, ilvl:int, classes:Union[list, str], category:str, binding:str, version:str): 
        """
        Create a log entry. ID;Item;Item Level;Classes;Category;Bind;Version
        """
        self.id = id
        self.name = name
        self.ilvl = ilvl
        self.classes = classes 
        self.category = category
        self.binding = binding
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
            "Main-Spec": [], 
            "Off-Spec": [], 
        }

all_items = {}

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
        binding = item[5]
        version = item[6]

        all_items[item_id] = Item(item_id, name, item_level, classes, category, binding, version)

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

def award_loot_auto(players):
    left, right, up, down = 1620, 1820, 6, 53
    image = pyautogui.screenshot(region=(left, up, right-left, down-up))

    whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-,:\' "
    loot_text = pytesseract.image_to_string(image, config=f"-c tessedit_char_whitelist=\"{whitelist}\"").strip()

    loot_text = loot_text.replace("’", "'")
    loot_text = loot_text.replace("\n", " ")

    if loot_text: print(f"Item found: {loot_text}")
    else: 
        print("No item found. Please double-check that we are rolling off an item. Aborting.")
        return players

    item_matches = []
    for i in all_items.values(): 
        if i.name.lower() in loot_text.lower() or loot_text.lower() in i.name.lower(): 
            item_matches.append(i)

    if len(item_matches) == 0:
        print(f"No matches found for {loot_text}. Splitting and trying again.")
        loot_text = loot_text.split(" ")
        item_matches = [[] for _ in range(len(loot_text))]
        for word in loot_text: 
            for i in all_items.values(): 
                if word.lower() in i.name.lower() or i.name.lower() in word.lower(): 
                    item_matches[loot_text.index(word)].append(i)

        item_matches = [x for x in item_matches if x]
        if len(item_matches) == 0:
            print("No matches found. Please double-check the item name and try again.")
            return players
        
        elif len(item_matches) > 10: 
            print("Too many matches found. Please try manually.")
            return players
        
        item_matches = list(set(item_matches[0]).intersection(*item_matches))
        print(f"Items found: {len(item_matches)}")
        for i in item_matches: print(f"{i.name} ({i.ilvl}) -- {i.category}")

        if len(item_matches) == 1:
            # We'll select this match, and then move on.
            item_match = item_matches[0]

        elif len(item_matches) > 1:
            item_matches.sort(key=lambda x: (x.ilvl, x.name))

            # We'll print all of the matches, and ask them to select one.z
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

    elif len(item_matches) == 1:
        # We'll select this match, and then move on.
        item_match = item_matches[0]

    elif len(item_matches) > 1:
        item_matches.sort(key=lambda x: (x.ilvl, x.name))
        
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

    return award_loot(players, item_match)

def award_loot_manual(players): 
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

    return award_loot(players, item_match)

def award_loot(players, item_match):
    if "Random" in item_match.category: 
        prefix = input("Item subcategory is random. What's the prefix? ").title()
        item_match.category = match_suffix(prefix, item_match.category)
        item_match.name = f"{item_match.name} of the {prefix}"

    slot_category = match_category(item_match.category)
    item_match.category = item_match.category.replace(" (Random)", "")

    for p in players: 
        # Skip this person if they're not here.
        if p._attendance == False: continue

    print(f"Item: {item_match.name} ({item_match.ilvl}) -- {item_match.category}")
    if item_match.classes != "None": print(f"Classes: {', '.join(item_match.classes)}")
    if item_match.binding != "Binds when picked up": print(f"WARNING: Item binds when equipped.")

    if item_match.category != "ETC" or re.search(r"(Chest|Crown|Gauntlets|Leggings|Shoulders) of the Corrupted (Conqueror|Protector|Vanquisher)", item_match.name):
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

            if item_match.classes != "None":
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

            if item_match.binding != "Binds when picked up":
                pyautogui.write("/")
                time.sleep(0.1)
                pyautogui.write("rw")
                time.sleep(0.1)
                pyautogui.press("space")
                time.sleep(0.1)
                pyautogui.write("WARNING: Item binds when equipped.")
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
                p._history["ETC"].append(Log(player.name, item_match, "DE", datetime.now().strftime("%Y-%m-%d")))

                return players

    # Do not award plusses to PvP items. 
    elif "(PvP)" in item_match.category:
        roll_type = "OS"

        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        player._history[slot_category].append(log)
        print(f"{player.name} has been awarded {item_match.name} ({item_match.ilvl}) as an {roll_type} item.")

    elif "Plans/Pattern" in item_match.category:
        roll_type = "ETC"

        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)

        item_category = "Main-Spec" if roll_type == "MS" else "Off-Spec" if roll_type == "OS" else "ETC"
        player._history[item_category].append(log)
        print(f"{player.name} has been awarded {item_match.name} ({item_match.ilvl}) as an {roll_type} item.")

    else: 
        off_spec = input("Is this an off-spec roll? (y/n): ").lower()
        if off_spec == "y": roll_type = "OS"
        else: roll_type = "MS"
    
        log = Log(player.name, item_match, roll_type, datetime.now().strftime("%Y-%m-%d"))
        player._raid_log.append(log)
        if not off_spec == "y": player._regular_plusses += 1

        item_category = "Main-Spec" if roll_type == "MS" else "Off-Spec" if roll_type == "OS" else "ETC"
        player._history[item_category].append(log)

        print(f"{player.name} has been awarded {item_match.name} ({item_match.ilvl}) as an {roll_type} item.")

    # random_match = re.compile(r"Flickering (.*) of the (.*)", re.IGNORECASE).match(item_match.name)
    # if random_match: 
    #     # If the item is a random item, we'll remove the suffix. 
    #     item_match.name = random_match.group(1)
        
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
            alias = input("Name: ")

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

    print(f"\n{num_present} players present.")

    print("")
    return players

def export_loot(): 
    # Sort the list of players by regular plusses. 
    # We will sort in descending order; so higher plusses should come first. 
    # If there is a tie, we will sort alphabetically by name. 
    # Names should be sorted alphabetically. 

    # If the mode is "console", output to both console and file.
    # If the mode is "file", output to file only.

    players.sort(key=lambda x: (-x._regular_plusses, x.name))

    loot_dates = []
    for p in players:
        for l in p._raid_log:
            loot_dates.append(l.date)

    loot_dates = sorted(list(set(loot_dates)))

    # Set the days of the week for the loot dates.
    dates = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
    loot_days = [datetime.strptime(x, "%Y-%m-%d").weekday() for x in loot_dates]
    loot_days = [dates[x] for x in loot_days]
    last_raid = max(loot_dates)

    with open("loot.txt", "w", encoding="utf-8") as f:
        f.write(f"# Loot log for ")
        for ind, date, day in zip(range(len(loot_dates)), loot_dates, loot_days):
            last_date = len(loot_dates) - 1
            if len(loot_dates) == 1: f.write(f"**{day}, {date}**:\n\n")
            elif ind == last_date: f.write(f"and **{day}, {date}**:\n\n")
            elif len(loot_dates) == 2: f.write(f"{day}, {date} ")
            else: f.write(f"{day}, {date}, ")

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
            f.write(f"{p.name} (+{p._regular_plusses} MS):\n")

            for l in p._raid_log:
                if l.roll == "MS":
                    if re.match(r"(Conqueror|Protector|Vanquisher)", l.item.name):
                        url = 'https://www.wowhead.com/cata/item=' + str(l.item.id) + '/' + l.item.name.replace(' ', '-').replace('\'', '').lower()
                        f.write(f"- [{l.item.name}](<{url}>) (MS) -- received on")
                        day_of_the_week = dates[datetime.strptime(l.date, "%Y-%m-%d").weekday()]
                        date_string = f"{day_of_the_week}, {l.date}" if l.date != last_raid else f"**{day_of_the_week}, {l.date}**"
                        f.write(f" {date_string}\n")
                    else: 
                        url = 'https://www.wowhead.com/cata/item=' + str(l.item.id) + '/' + l.item.name.replace(' ', '-').replace('\'', '').lower()
                        f.write(f"- [{l.item.name}](<{url}>) ({l.item.ilvl}) (MS) -- received on")
                        day_of_the_week = dates[datetime.strptime(l.date, "%Y-%m-%d").weekday()]
                        date_string = f"{day_of_the_week}, {l.date}" if l.date != last_raid else f"**{day_of_the_week}, {l.date}**"
                        f.write(f" {date_string}\n")

            for l in p._raid_log:
                if l.roll == "OS":
                    if re.match(r"(Conqueror|Protector|Vanquisher)", l.item.name):
                        url = 'https://www.wowhead.com/cata/item=' + str(l.item.id) + '/' + l.item.name.replace(' ', '-').replace('\'', '').lower()
                        f.write(f"- [{l.item.name}](<{url}>) (OS) -- received on")
                        day_of_the_week = dates[datetime.strptime(l.date, "%Y-%m-%d").weekday()]
                        date_string = f"{day_of_the_week}, {l.date}" if l.date != last_raid else f"**{day_of_the_week}, {l.date}**"
                        f.write(f" {date_string}\n")
                    else: 
                        url = 'https://www.wowhead.com/cata/item=' + str(l.item.id) + '/' + l.item.name.replace(' ', '-').replace('\'', '').lower()
                        f.write(f"- [{l.item.name}](<{url}>) ({l.item.ilvl}) (OS) -- received on")
                        day_of_the_week = dates[datetime.strptime(l.date, "%Y-%m-%d").weekday()]
                        date_string = f"{day_of_the_week}, {l.date}" if l.date != last_raid else f"**{day_of_the_week}, {l.date}**"
                        f.write(f" {date_string}\n")

            for l in p._raid_log:
                if l.roll == "ETC":
                    url = 'https://www.wowhead.com/cata/item=' + str(l.item.id) + '/' + l.item.name.replace(' ', '-').replace('\'', '').lower()
                    f.write(f"- [{l.item.name}](<{url}>) (ETC) -- received on")
                    day_of_the_week = dates[datetime.strptime(l.date, "%Y-%m-%d").weekday()]
                    date_string = f"{day_of_the_week}, {l.date}" if l.date != last_raid else f"**{day_of_the_week}, {l.date}**"
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
                f.write(f"Disenchanted items:\n")

                for l in p._raid_log:
                    url = 'https://www.wowhead.com/cata/item=' + str(l.item.id) + '/' + l.item.name.replace(' ', '-').replace('\'', '').lower()
                    f.write(f"- [{l.item.name}](<{url}>) ({l.item.ilvl}) -- disenchanted on")
                    day_of_the_week = dates[datetime.strptime(l.date, "%Y-%m-%d").weekday()]
                    date_string = f"{day_of_the_week}, {l.date}" if l.date != last_raid else f"**{day_of_the_week}, {l.date}**"
                    f.write(f" {date_string}\n")

def paste_loot():  
    # Delete all files in "./history"
    for file in os.listdir("./pastes"):
        os.remove(f"./pastes/{file}")
        
    with open("loot.txt", "r", encoding="utf-8") as file: 
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
            with open(f"./pastes/paste_{index}.txt", "w", encoding="utf-8") as file:
                file.write(paste)
                index += 1
            paste = line
            total_length = len(line)
    
    with open(f"./pastes/paste_{index}.txt", "w", encoding="utf-8") as file:
        file.write(paste)

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
        slot_category = "Main-Spec" if item.roll == "MS" else "Off-Spec" if item.roll == "OS" else "ETC"
        player._history[slot_category].remove(item)

    return players

def weekly_reset(players, override=False):
    players_with_plusses = [p for p in players if p._regular_plusses > 0]
    if len(players_with_plusses) == 0: 
        print("There's nothing to clear!")
        return players

    if not override:
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
    
    print("---- SUDO MODE ----")
    print("a. COMPLETELY wipe the pickle file")
    print("b. Restore history from Gargul export")
    print("c. Create Gargul export")
    print("d. Export list of known players")
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
                if item_name in i.name and i.ilvl == ilvl:
                    item = i
                    item.name = item_name
                    break
                
            if "Gladiator" in item_name:
                roll_type = "OS"
            else:
                roll_type = "OS" if offspec else "MS"

            if re.match(r"(Plans|Pattern)", item_name):
                roll_type = "ETC"
                
            if player is None: 
                if winner in known_players:
                    pclass = known_players[winner]
                    print(f"Player {winner} not found in dictionary, but found in list of known players. Player class auto-selected as {pclass}.")
                    players.append(Player(winner, alias, pclass))
                    player = players[-1]

                else: 
                    pclass = input(f"Could not find player {winner}. Creating from scratch. What class are they? ")
                    # If class is "Death Knight" or "dk", we'll convert it to "Death Knight".
                    if re.match(r"(death knight|dk)", pclass.lower()): pclass = "Death Knight"
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

            if re.match(r"(Chest|Crown|Leggings|Shoulders|Gauntlets) of the Corrupted (Conqueror|Protector|Vanquisher)", item.name):
                # Depending on the suffix, we determine what valid classes are. 
                suffix = item.name.split(" ")[-1]
                if suffix == "Conqueror": item.classes = ["Paladin", "Priest", "Warlock"]
                elif suffix == "Protector": item.classes = ["Warrior", "Hunter", "Shaman"]
                elif suffix == "Vanquisher": item.classes = ["Death Knight", "Druid", "Mage", "Rogue"]

                # We want to make sure that the player's class is in the list of valid classes. 
                # If it's not, this was a disenchanted item. 

                if player._player_class not in item.classes:
                    # Find _disenchanted player and award it to that instead. 
                    for p in players:
                        if p.name == "_disenchanted":
                            player = p
                            break

            item_category = "Main-Spec" if roll_type == "MS" else "Off-Spec" if roll_type == "OS" else "ETC"
            player._history[item_category].append(Log(player.name, item, roll_type, date))
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

                    if re.match(r"Flickering (Cowl|Shoulders|Shoulderpads|Handguards|Wristbands)", item.item.name):
                        suffix = " ".join(item.item.name.split(" ")[2:])
                        item_name = item.item.name.replace(f"{suffix}", "").strip()

                        for key, value in all_items.items():
                            if value.name == item_name:
                                item_id = key
                                break

                    else: 
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

    return players

def export_gargul(players):
    with open("plusses.csv", "w", encoding="utf-8") as file: 
        for p in players: 
            if p.name == "_disenchanted": continue
            if p._regular_plusses > 0: file.write(f"{p.name},{p._regular_plusses}\n")

def last_run(): 
    try:
        with open("last_run.txt", "r", encoding="utf-8") as f:
            last_run = f.readline().strip()

        last_run = datetime.strptime(last_run, "%Y-%m-%d %H:%M:%S")
        return last_run
    
    except:
        return None
    
def write_last_run():
    # Write the current date and time to the file "last_run.txt".
    with open("last_run.txt", "w", encoding="utf-8") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def check_weekly_reset(): 
    # Check if the last run was before the last Tuesday at 8am PST.
    # If so, we should ask if we want to reset the plusses.
    # Return TRUE if weekly reset has occurred, FALSE if it has not.
    last_run_date = last_run()
    if last_run_date is None: return True

    # Get the last Tuesday at 8am PST.
    last_tuesday = datetime.now() - timedelta(days=(datetime.now().weekday() - 1) % 7)
    last_tuesday = last_tuesday.replace(hour=8, minute=0, second=0, microsecond=0)

    return last_run_date < last_tuesday

if __name__ == "__main__":
    players_with_plusses = [p for p in players if p._regular_plusses > 0]

    if check_weekly_reset() and len(players_with_plusses) > 0:
        print("It looks like reset has occurred.")
        reset = input("Reset weekly plusses? (y/n): ").lower()
        if reset == "y": players = weekly_reset(players, override=True)
    
    write_last_run()

    while(True): 
        export_pickle(players)
        
        print("----------------------------------------")
        print(f"Loot Tracker")
        print("1) Roll off the next piece of loot")
        print("2) Manually roll off loot")
        print("3) Mark attendance")
        print("4) Export THIS RAID's loot to a file")
        print("5) Split up loot into paste-sized chunks")
        print("6) Remove loot, or weekly reset")
        print("7) Export plusses in Gargul style")
        print("8) Enter sudo mode")

        print("")

        try: sel = int(input("Select an option: "))
        except: break

        if sel == 1: players = award_loot_auto(players)
        elif sel == 2: players = award_loot_manual(players)
        elif sel == 3: players = mark_attendance(players)
        elif sel == 4: export_loot()
        elif sel == 5: paste_loot()
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