import pickle
from typing import List,Union
import requests
import re
import argparse
import os

parser = argparse.ArgumentParser()

# Add an argument called "--force-new", "-f" to force the script to create a new pickle file.
parser.add_argument("--force-new", "-f", help="Force the script to create a new pickle file.", action="store_true")

# Add an argument called "--force-manual", "-m" to force the script to create a new manual file. 
parser.add_argument("--force-manual", "-m", help="Force the script to create a new manual file.", action="store_true")

# Add an argument called "--debug", "-d" to enable debug mode.
parser.add_argument("--debug", "-d", help="Enable debug mode.", action="store_true")

args = parser.parse_args()

class Log: 
    def __init__(self, name, item, roll_type): 
        """
        Create a log entry.
        - Name: The name of the player
        - Item: The name of the item
        - Roll: Roll type (MS, OS, soft reserve)
        """

        self.name = name
        self.item = item
        self.roll = roll_type

class Player: 
    def __init__(self, name:str,  soft_reserve:List[str], regular_plusses:int=0, soft_reserve_plusses:int=0):
        self.name = name
        self.soft_reserve = soft_reserve

        self._regular_plusses = regular_plusses
        self._soft_reserve_plusses = soft_reserve_plusses

        self._log = []

def import_pickle() -> list: 
    # Import the pickle file
    try: 
        with open('players.pickle', 'rb') as f:
            players = pickle.load(f)

    except FileNotFoundError:
        print('No pickle file found. Creating a new one.')
        players = []

    return players

def import_manual() -> list: 
    try: 
        with open('manual.pickle', 'rb') as f: 
            manual = pickle.load(f)

    except FileNotFoundError:
        print('No manual file found. Skipping.')
        manual = []

    return manual
    
def export_pickle(players, manual):
    # Export the pickle file
    with open('players.pickle', 'wb') as f:
        pickle.dump(players, f)

    with open('manual.pickle', 'wb') as f:
        pickle.dump(manual, f)

# We'll import the pickle if the "--force-new" argument is not present.
if not args.force_new:
    players = import_pickle()
else:
    players = []

    # Create a special player called "_disenchanted", for items that were not awarded to anyone.
    # This is used when no one rolls. 
    players.append(Player("_disenchanted", []))

# We'll import the manual if the "--force-manual" argument is not present.
if not args.force_manual:
    manual = import_manual()
else:
    manual = []

# In either case, we'll append the manual onto the end of the players list, but only if they don't already exist.
for m in manual:
    # Check if the player is in the list of players.
    player_exists = False
    for p in players: 
        if p.name == m.name: 
            player_exists = True
            break
    
    if not player_exists: 
        # Create a new player object and append it the list. 
        players.append(Player(m.name, []))

def import_softreserve(players): 
    # We'll attempt to import soft reserve data from the CSV file. 
    if not os.path.exists("soft_reserves.csv"):
        print("No soft reserve file found. Skipping.")
        return players

    with open("soft_reserves.csv", "r") as f: 
        sr_data = f.readlines()

    # We'll truncate the debug-sr.txt file, but only if debug mode is enabled. 
    if args.debug:
        with open("debug-sr.txt", "w") as f:
            f.truncate()

    # Parse the data. 
    for soft_res in sr_data: 
        # Split the string into a list.
        soft_res = soft_res.split(",")

        # We'll check if the second column is a number. If it's not, then this item has a comma in it; and we'll join the first two elements together with a comma. 
        if not soft_res[1].isdigit():
            soft_res[0:2] = [",".join(soft_res[0:2])]

        # We'll remove all the quotes from the string. 
        soft_res = [x.replace('"', "") for x in soft_res]

        # Write this to debug-sr.txt, but only if debug mode is enabled.
        if args.debug:
            with open("debug-sr.txt", "a") as f:
                f.write(f"{soft_res}\n")

        # Format the strings.
        # Item,ItemId,From,Name,Class,Spec,Note,Plus,Date
        # We care about: Item, Name, Class, Spec
        
        # Item
        item = soft_res[0]
        name = soft_res[3]

        # Exception: If the name is "Annathalcyon", skip it. 
        if name == "Annathalcyon":
            continue

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

def award_loot(item_name, player_name, roll_type):
    # First, we'll check the list of players. 
    # This function assumes the roll has already been done; we're just awarding the loot and keeping track of plusses. 

    # Check if the player is in the list of players.
    # Since players is a list of player objects, we'll need to iterate through it and check the name of each player.
    # If the player is not in the list, we'll output an error message and return.

    for p in players: 
        # Check the name.
        if player_name == p.name:
            # Check if the roll type is "MS", "main-spec", "OS", "off-spec", "SR", or "soft-reserve". 
            # If it's MS or main-spec, we'll add a plus to the player's regular plusses.
            # If it's SR or soft-reserve, we'll add a plus to the player's soft-reserve plusses.
            # If it's OS or off-spec, we'll award the item but not add a plus.
            # Finally, if it's not any of those, we'll print an error message and return.
            if roll_type.lower() == "ms" or roll_type.lower() == "main-spec":
                # Add this to the log, using the Log class.
                p._log.append(Log(player_name, item_name, "MS"))
            
                # Add a plus to the player's regular plusses.
                p._regular_plusses += 1

            elif roll_type.lower() == "os" or roll_type.lower() == "off-spec":
                # Add this to the log, using the Log class.
                p._log.append(Log(player_name, item_name, "OS"))

            elif roll_type.lower() == "sr" or roll_type.lower() == "soft-reserve":
                # Add this to the log, using the Log class.
                p._log.append(Log(player_name, item_name, "SR"))

                # Add a plus to the player's soft-reserve plusses.
                p._soft_reserve_plusses += 1

            elif roll_type.lower() == "etc" or roll_type.lower() == "other":
                # Add this to the log, using the Log class.
                p._log.append(Log(player_name, item_name, "ETC"))

            elif roll_type.lower() == "disenchant" or roll_type.lower() == "de":
                # Add this to the log, using the Log class.
                p._log.append(Log(player_name, item_name, "DE"))

            else:
                print("Invalid roll type.")
                
            return
        
    # If we get here, the player wasn't found in the list of players.
    print("Player not found. Please create the player manually before trying again.")

def export_loot(mode="console"): 
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

    if mode == "console":
        with open("loot.txt", "w") as f:

            # Print out the list of players.
            for p in players: 
                # First, check if the player has not won any items; that is, their log is empty. 
                # If so, we'll skip them.
                if len(p._log) == 0:
                    continue

                # We'll print out the disenchanted player last. 
                if p.name == "_disenchanted": 
                    continue

                # Print out the player's name, and then the number of plusses they have; of both types. 
                print_write(f"{p.name} (+{p._regular_plusses} MS)", f)

                for l in p._log: 
                    if l.roll == "MS":
                        print_write(f"- {l.item} (MS)", f)

                for l in p._log: 
                    if l.roll == "OS":
                        print_write(f"- {l.item} (OS)", f)

                for l in p._log: 
                    if l.roll == "SR":
                        print_write(f"- {l.item} (SR)", f)

                for l in p._log: 
                    if l.roll == "ETC": 
                        print_write(f"- {l.item} (ETC)", f)

                print_write("", f)

            # Print out "_disenchanted" last, but only if they have items.
            for p in players:
                if p.name == "_disenchanted":
                    # Check if the player has not won any items; that is, their log is empty.
                    # If so, we'll skip them.
                    if len(p._log) == 0:
                        continue

                    # Print out the player's name. 
                    print_write(f"{p.name}", f)

                    for l in p._log:
                        print_write(f"- {l.item}", f)

    # If the mode is "file", output to file only, using the same format as above, but using f.write() instead of print_write().
    elif mode == "file":
        with open("loot.txt", "w") as f:
            # Print out the list of players.
            for p in players:
                # First, check if the player has not won any items; that is, their log is empty.
                # If so, we'll skip them.
                if len(p._log) == 0:
                    continue

                # We'll print out the disenchanted player last.
                if p.name == "_disenchanted":
                    continue

                # Print out the player's name, and then the number of plusses they have; of both types.
                f.write(f"{p.name} (+{p._regular_plusses} MS)\n")

                for l in p._log:
                    if l.roll == "MS":
                        f.write(f"- {l.item} (MS)\n")

                for l in p._log:
                    if l.roll == "OS":
                        f.write(f"- {l.item} (OS)\n")

                for l in p._log:
                    if l.roll == "SR":
                        f.write(f"- {l.item} (SR)\n")

                for l in p._log:
                    if l.roll == "ETC":
                        f.write(f"- {l.item} (ETC)\n")

                f.write("\n")

            # Print out "_disenchanted" last, but only if they have items.
            for p in players:
                if p.name == "_disenchanted":
                    # Check if the player has not won any items; that is, their log is empty.
                    # If so, we'll skip them.
                    if len(p._log) == 0:
                        continue

                    # Print out the player's name.
                    f.write(f"{p.name}\n")

                    for l in p._log:
                        f.write(f"- {l.item}\n")

url = "https://www.wowhead.com/wotlk/zone=4273/ulduar"

# If the file called "ulduar.html" exists, read it. Otherwise, access the site and download it. 
# Ignore errors. 
if not os.path.exists("ulduar.html") or os.path.getsize("ulduar.html") == 0 or args.force_new:
    # Get the HTML from the URL 
    html = requests.get(url).text

    with open("ulduar.html", "w", errors="ignore") as f:
        f.write(html)

else:
    with open("ulduar.html", "r", errors="ignore") as f:
        html = f.read()

# Parse the data. 
# Example string: 
# "name":"Rising Sun","quality":4
# We want to extract the name and the quality. 

# Create a list to store the items.
all_items = []

# use a regular expression to search for the name of each item, using re.findall(). 
pattern = r'"name":"(.+?)","quality":(\d+)'
matches = re.findall(pattern, html)

# Add each item to the list of items, but only if the level is >= 80 and the quality is 4 or higher (epic and legendary).
for m in matches:
    if int(m[1]) >= 4:
        all_items.append(m[0])

url = "https://www.wowhead.com/wotlk/zone=4722/trial-of-the-crusader"

# If the file called "trial-of-the-crusader.html" exists, read it. Otherwise, access the site and download it.
# Ignore errors.

if not os.path.exists("trial-of-the-crusader.html") or os.path.getsize("trial-of-the-crusader.html") == 0 or args.force_new:
    # Get the HTML from the URL
    html = requests.get(url).text

    with open("trial-of-the-crusader.html", "w", errors="ignore") as f:
        f.write(html)

else:
    with open("trial-of-the-crusader.html", "r", errors="ignore") as f:
        html = f.read()

# Parse the data.
# Example string:
# "name":"Rising Sun","quality":4

# We want to extract the name and the quality.

# use a regular expression to search for the name of each item, using re.findall().
pattern = r'"name":"(.+?)","quality":(\d+)'
matches = re.findall(pattern, html)

# Add each item to the list of items, but only if the quality is 4 or higher (epic and legendary).
# In addition, only add items that are not in the list already.
for m in matches:
    if m[0] not in all_items:
        all_items.append(m[0])

# If the debug flag is set, write the list of items to a file.
if args.debug:
    with open("debug-items.txt", "w") as f:
        for i in all_items:
            f.write(i + "\n")

import requests
import datetime

def up_to_date(): 
    # Get repository details from the GitHub API.
    url = "https://api.github.com/repos/DrNekoSenpai/loot_tracker"
    response = requests.get(url)
    data = response.json()

    # Get the date of the latest commit.
    last_commit_date = datetime.datetime.strptime(data['pushed_at'], "%Y-%m-%dT%H:%M:%SZ")

    # Grab the current date, and adjust for UTC time. 
    current_date = datetime.datetime.utcnow()

    if args.debug: 
        print("Last commit date", last_commit_date)
        print("Current date", current_date)

    return last_commit_date < current_date

if not up_to_date():
    print("Error: the local repository is not up to date. Please pull the latest changes before running this script.")
    print("To pull the latest changes, simply run the command 'git pull' in this terminal.")
    exit(1)

if args.debug:
    print("The local repository is up to date.")

# Main loop.
while(True): 
    export_pickle(players, manual)
    export_loot("file")
    print("")
    print("Asylum of the Immortals Loot Tracker")
    print("1) Award loot")
    print("2) Manually add new players")
    print("3) Clear ALL plusses")
    print("4) Log a trade")
    print("5) Export loot")
    print("6) Remove a piece of loot")
    print("7) Print out all players in the database")
    print("8) Manual input from loot text file")
    print("9) Export plusses in Gargul style")
    print("10) Exit")
    
    try: sel = int(input("Select an option: "))
    except: break

    print("")

    if sel == 1: 
        item_name = input("Enter the name of the item to be awarded. Partial matching and case insensitivity are supported: ")
        if item_name == "": continue

        print("")

        # Go through the list of items and check if there is a matching item. If so, print out the item's name. 
        # If there are no matches, print out an error message. 
        
        # Create a list to store the matches.
        matches = []

        # Go through the list of items and check if there is a matching item. If so, add it to the list of matches.
        for i in all_items:
            if item_name.lower() in i.lower():
                matches.append(i)

        # If there are no matches, print out an error message.
        if len(matches) == 0:
            print("No matches found. Please double-check the item name and try again.")
            continue

        # If there is only one match, we'll use that item.
        elif len(matches) == 1:
            item_name = matches[0]

        # If there are multiple matches, we'll print out the list of matches and ask the user to select one, using a numbered list. 
        else:
            print("Multiple matches found.") 
            for ind,val in enumerate(matches):
                print(f"{ind+1}) {val}")

            # Ask the user to select one.
            try:
                sel = int(input("Select an item: "))
                item_name = matches[sel-1]
            except:
                print("Invalid selection.")
                continue

        player_name = input("Enter the name of the player to be awarded the item. Partial matching and case insensitivity are supported: ")
        if player_name == "": continue
        elif player_name.lower() in "_disenchanted":
            # Award the item to the "_disenchanted" player.
            # Find the player with the name "_disenchanted" and award the item to them.
            # Starts with and case insensitivity are supported.
            for p in players:
                if p.name.lower().startswith("_disenchanted"):
                    # award_loot(item_name, player_name.name, "ETC")
                    award_loot(item_name, p.name, "DE")
                    print(f"No one rolled; {item_name} has been disenchanted.")

        # Go through the list of players and check if there is a matching player. If so, print out the player's name.
        # If there are no matches, print out an error message.

        # Create a list to store the matches.
        matches = []

        # Go through the list of players and check if there is a matching player. If so, add it to the list of matches.
        # Use partial matching and case insensitivity.
        for p in players:
            if player_name.lower() in p.name.lower():
                matches.append(p)

        # If there are no matches, print out an error message.
        if len(matches) == 0:
            print("No matches found. Please double-check the player name and try again.")
            continue

        # If there is only one match, we'll use that player.
        elif len(matches) == 1:
            player_name = matches[0].name

        # If there are multiple matches, we'll print out the list of matches and ask the user to select one, using a numbered list.
        else:
            print("Multiple matches found.") 
            for ind,val in enumerate(matches):
                print(f"{ind+1}) {val.name}")

            # Ask the user to select one.
            try:
                sel = int(input("Select a player: "))
                player_name = matches[sel-1].name
            except:
                print("Invalid selection.")
                continue

        # At this point, we've got the item name and the player name.
        # We'll get the player object from the list of players.
        for p in players:
            if p.name == player_name:
                player_name = p

        # We'll check if this item is a pattern, or the Fragment of Val'anyr. If so, we'll call award_loot with the loot type set to "ETC".
        # It's a pattern if it starts with "Plans: ", "Schematic: ", "Pattern: ", or "Formula: ".
        # It's the Fragment of Val'anyr if it's "Fragment of Val'anyr".
        if item_name.startswith("Plans: ") or item_name.startswith("Schematic: ") or item_name.startswith("Pattern: ") or item_name.startswith("Formula: ") or item_name == "Fragment of Val'anyr":
            award_loot(item_name, player_name.name, "ETC")
            print(f"{player_name.name} has been awarded {item_name} as an ETC item.")
            continue

        # If the player name is "_disenchanted", we'll do nothing. 
        if player_name.name == "_disenchanted":
            continue

        # First, we'll check if this is an off-spec item. If so, we'll call award_loot with the loot type set to "OS". 
        offspec = input("Is this an off-spec item? (y/n): ")
        if offspec.lower() == "y":
            award_loot(item_name, player_name.name, "OS")
            print(f"{player_name.name} has been awarded {item_name} as an off-spec item.")

        else:
            # If not, we'll check the corresponding soft-reserve list to see if the player has soft-reserved the item.
            # If so, we'll call award_loot with the loot type set to "SR".
            # Otherwise, we'll call award_loot with the loot type set to "MS".

            if item_name in player_name.soft_reserve: 
                award_loot(item_name, player_name.name, "SR")
                print(f"{player_name.name} has been awarded {item_name} as a soft-reserve item.")
            else:
                award_loot(item_name, player_name.name, "MS")
                print(f"{player_name.name} has been awarded {item_name} as a main-spec item.")

    elif sel == 2:
        # Ask the user to enter the name of the new player. This can be done in any case; but partial matching is not supported.
        new_players = input("Enter the names of up to 25 new players: ")
        
        # We'll check to see how many players there are, by splitting with spaces. 
        if ' ' in new_players: new_players = new_players.split(" ")
        else: new_players = [new_players]

        for new_player in new_players: 
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
                manual.append(Player(new_player, []))
                print(f"ADDED: {new_player}")

            else: 
                print(f"ERROR: {new_player} already exists.")

    elif sel == 3: 
        # Ask for confirmation, as this is irreversible.
        confirm = input("Are you sure you want to clear ALL plusses? This is irreversible. (y/n): ")
        if confirm.lower() == "y": 
            for p in players: 
                p._regular_plusses = 0
                p._soft_reserve_plusses = 0
                p._log = []
            print("All plusses have been cleared.")

    elif sel == 4: 
        # Ask the user to enter the name of the sending player. 
        sending_player = input("Enter the name of the player who is trading the item. Partial matching and case insensitivity are supported: ")

        # Go through the list of players and check if there is a matching player. If so, print out the player's name.
        # If there are no matches, print out an error message.

        # Create a list to store the matches.
        matches = []

        # Go through the list of players and check if there is a matching player. If so, add it to the list of matches.
        # Use partial matching and case insensitivity.

        for p in players:
            if sending_player.lower() in p.name.lower():
                matches.append(p)

        # If there are no matches, print out an error message.
        if len(matches) == 0:
            print("No matches found. Please double-check the player name and try again.")
            continue

        # If there is only one match, we'll use that player.
        elif len(matches) == 1:
            sending_player = matches[0].name

        # If there are multiple matches, we'll print out the list of matches and ask the user to select one, using a numbered list.
        else:
            print("Multiple matches found.") 
            for ind,val in enumerate(matches):
                print(f"{ind+1}) {val.name}")

            # Ask the user to select one.
            try:
                sel = int(input("Select a player: "))
                sending_player = matches[sel-1].name
            except:
                print("Invalid selection.")
                continue
        
        # At this point, we've got the name of the sending player.
        # We'll get the player object from the list of players.
        # First, we'll check if the player has any items in the log. 
        # If not, we'll print out an error message and return to the main menu.

        for p in players:
            if p.name == sending_player:
                sending_player = p

        if len(sending_player._log) == 0:
            print(f"No items have been awarded to {sending_player.name} yet.")
            continue

        # If so, we'll print out the list of items in the log and ask the user to select one, using a numbered list.
        else:
            print(f"Items awarded to {sending_player.name}:")
            for ind,val in enumerate(sending_player._log):
                print(f"{ind+1}) {val.item}")

            # Ask the user to select one.
            try:
                sel = int(input("Select an item: "))
                item_name = sending_player._log[sel-1]
            except:
                print("Invalid selection.")
                continue

        # First, check if the item is a main-spec item. If so, decrement regular plusses. 
        if item_name.roll == "MS":
            sending_player._regular_plusses -= 1

        # If not, check if the item is a soft-reserve item. If so, decrement soft-reserve plusses.
        elif item_name.roll == "SR":
            sending_player._soft_reserve_plusses -= 1

        # Remove the item from the player's log.
        sending_player._log.remove(item_name)

        # Now, we'll ask the user to enter the name of the receiving player.
        receiving_player = input("Enter the name of the player who is receiving the item. Partial matching and case insensitivity are supported: ")

        # Go through the list of players and check if there is a matching player. If so, print out the player's name.
        # If there are no matches, print out an error message.

        # Create a list to store the matches.
        matches = []

        # Go through the list of players and check if there is a matching player. If so, add it to the list of matches.
        # Use partial matching and case insensitivity.

        for p in players:
            if receiving_player.lower() in p.name.lower():
                matches.append(p)

        # If there are no matches, print out an error message.
        if len(matches) == 0:
            print("No matches found. Please double-check the player name and try again.")
            continue

        # If there is only one match, we'll use that player.
        elif len(matches) == 1:
            receiving_player = matches[0].name

        # If there are multiple matches, we'll print out the list of matches and ask the user to select one, using a numbered list.
        else:
            print("Multiple matches found.") 
            for ind,val in enumerate(matches):
                print(f"{ind+1}) {val.name}")

            # Ask the user to select one.
            try:
                sel = int(input("Select a player: "))
                receiving_player = matches[sel-1].name
            except:
                print("Invalid selection.")
                continue

        # At this point, we've got the name of the receiving player.
        # We'll get the player object from the list of players.

        for p in players:
            if p.name == receiving_player:
                receiving_player = p

        # First, we'll check if this is an off-spec item. If so, we'll call award_loot with the loot type set to "OS". 
        offspec = input("Is this an off-spec item? (y/n): ")
        if offspec.lower() == "y":
            award_loot(item_name.item, receiving_player.name, "OS")
            print(f"{receiving_player.name} has been awarded {item_name.item} as an off-spec item.")
        else:
            # If not, we'll check the corresponding soft-reserve list to see if the player has soft-reserved the item.
            # If so, we'll call award_loot with the loot type set to "SR".
            # Otherwise, we'll call award_loot with the loot type set to "MS".

            if item_name.item in receiving_player.soft_reserve: 
                award_loot(item_name.item, receiving_player.name, "SR")
                print(f"{receiving_player.name} has been awarded {item_name.item} as a soft-reserve item.")
            else:
                award_loot(item_name.item, receiving_player.name, "MS")
                print(f"{receiving_player.name} has been awarded {item_name.item} as a main-spec item.")

    elif sel == 5: 
        export_loot("console")

    elif sel == 6: 
        # Ask the user to enter the name of the sending player. 
        sending_player = input("Enter the name of the player who we need to remove the item from. Partial matching and case insensitivity are supported: ")

        # Go through the list of players and check if there is a matching player. If so, print out the player's name.
        # If there are no matches, print out an error message.

        # Create a list to store the matches.
        matches = []

        # Go through the list of players and check if there is a matching player. If so, add it to the list of matches.
        # Use partial matching and case insensitivity.

        for p in players:
            if sending_player.lower() in p.name.lower():
                matches.append(p)

        # If there are no matches, print out an error message.
        if len(matches) == 0:
            print("No matches found. Please double-check the player name and try again.")
            continue

        # If there is only one match, we'll use that player.
        elif len(matches) == 1:
            sending_player = matches[0].name

        # If there are multiple matches, we'll print out the list of matches and ask the user to select one, using a numbered list.
        else:
            print("Multiple matches found.") 
            for ind,val in enumerate(matches):
                print(f"{ind+1}) {val.name}")

            # Ask the user to select one.
            try:
                sel = int(input("Select a player: "))
                sending_player = matches[sel-1].name
            except:
                print("Invalid selection.")
                continue
        
        # At this point, we've got the name of the sending player.
        # We'll get the player object from the list of players.
        # First, we'll check if the player has any items in the log. 
        # If not, we'll print out an error message and return to the main menu.

        for p in players:
            if p.name == sending_player:
                sending_player = p

        if len(sending_player._log) == 0:
            print(f"No items have been awarded to {sending_player.name} yet.")
            continue

        # If so, we'll print out the list of items in the log and ask the user to select one, using a numbered list.
        else:
            print(f"Items awarded to {sending_player.name}:")
            for ind,val in enumerate(sending_player._log):
                print(f"{ind+1}) {val.item}")

            # Ask the user to select one.
            try:
                sel = int(input("Select an item: "))
                item_name = sending_player._log[sel-1]
            except:
                print("Invalid selection.")
                continue

        # First, check if the item is a main-spec item. If so, decrement regular plusses. 
        if item_name.roll == "MS":
            sending_player._regular_plusses -= 1

        # If not, check if the item is a soft-reserve item. If so, decrement soft-reserve plusses.
        elif item_name.roll == "SR":
            sending_player._soft_reserve_plusses -= 1

        # Remove the item from the player's log.
        sending_player._log.remove(item_name)

    elif sel == 7: 
        # Print out all players in the database; their name, number of plusses, and total number of items awarded.
        for p in players:
            print(f"{p.name} (+{p._regular_plusses} MS, +{p._soft_reserve_plusses} SR)")
            print(f"Total items awarded: {len(p._log)}")
            print("")

    elif sel == 8: 
        # First, confirm that the user does want to overwrite all entries in the database, as this cannot be undone. 
        # If not, return to the main menu.

        confirm = input("Are you sure you want to overwrite the database? This cannot be undone. (y/n): ")
        if confirm.lower() != "y":
            continue

        # Read in from "loot_raw.txt" file, and print to console. This is not the same file as "loot.txt", which is the output file. 
        # This is done to prevent against accidental overwrites. 
        # If the file doesn't exist, print out an error message.

        try:
            with open("loot_raw.txt", "r") as f:
                loot_raw = f.read()
            loot_raw = loot_raw.split("\n\n")

        except:
            print("Error: loot_raw.txt does not exist.")
            continue

        for line in loot_raw:
            name = line.split("\n")[0].split(' ')[0]

            # Split plusses by this following regular expression, capturing both numbers: 
            # (+1 MS, +1 SR)
            # If the pattern is not present, continue instead of throwing an error.
            
            try:
                # plusses = re.findall(r'\(\+(\d+) MS, \+(\d+) SR\)', line)[0]
                plusses = re.findall(r'\(\+(\d+) MS\)', line)[0]
                print(f"{name} (+{plusses[0]} MS")
            except:
                print(f"{name}")
                continue

            # Find the corresponding Player object in the list of players.
            # If the player does not exist, create it and add it to the list of players.
            # If the player does exist, update the player's plusses.

            player_exists = False
            for p in players:
                if p.name == name:
                    p._regular_plusses = int(plusses[0])
                    p._soft_reserve_plusses = int(plusses[1])
                    player_exists = True
                    break

            if not player_exists:
                p = Player(name, int(plusses[0]), int(plusses[1]))
                players.append(p)
        
            # Split the rest of the line, capturing the item name and roll type.
            # Regular expression: 
            # Item name (MS/OS/SR)

            # Reset the player's item log 
            p._log = []
            
            items = line.split("\n")[1:]
            for item in items:
                item_name = re.findall(r'- (.*) \((MS|OS|SR)\)', item)
                # Add the item to the log 
                p._log.append(Log(p.name, item_name[0][0], item_name[0][1]))

        print("") # Move onto next person

    elif sel == 9: 
        # Loop through each player in the list of players.
        for p in players: 
            # Print out their name, then the number of main-spec plusses. Ignore soft-reserve plusses.
            if p._regular_plusses > 0: 
                print(f"{p.name} {p._regular_plusses}")

    elif sel == 10:
        break