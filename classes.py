import pickle
from typing import List,Union

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
    def __init__(self, name:str, pclass:str, spec:str, soft_reserve:List[str]):
        self.name = name
        self.pclass = pclass
        self.spec = spec
        self.soft_reserve = soft_reserve

        self._regular_plusses = 0
        self._soft_reserve_plusses = 0

        self._log = []

def import_pickle() -> list: 
    # Import the pickle file
    try: 
        with open('players.pickle', 'rb') as f:
            players = pickle.load(f)
            return players
    except FileNotFoundError:
        print('No pickle file found. Creating a new one.')
        players = {}
        return players
    
def export_pickle(players):
    # Export the pickle file
    with open('players.pickle', 'wb') as f:
        pickle.dump(players, f)

players = import_pickle()

# We'll attempt to import soft reserve data from the CSV file. 
with open("soft-reserves.csv", "r") as sr_file: 
    sr_data = sr_file.readlines()

# Parse the data. 
for soft_res in sr_data: 
    # Split the line into a list of strings. 
    soft_res = soft_res.split(",")

    # Format the strings.
    # Item,ItemId,From,Name,Class,Spec,Note,Plus,Date
    # We care about: Item, From, Name, Class, Spec
    
    # Item
    item = soft_res[0]
    source = soft_res[2]
    name = soft_res[3]
    pclass = soft_res[4]
    spec = soft_res[5]

    # Search for an existing player object. Create it if it doesn't exist. 

    # Check if the player is in the list of players.
    player_exists = False
    current_player = None
    for p in players: 
        if p.name == name: 
            player_exists = True
            current_player = p
            break
    
    if not player_exists: 
        # Create a new player object.
        players.append(Player(name, pclass, spec, []))
        current_player = players[-1]

    # Add the item to the player's soft reserve list.
    current_player.soft_reserve.append((item, source))

def award_loot(item_name, player_name, roll_type):
    """
    Award a piece of loot. We'll cross-check the soft reserve, and the player's number of plusses.

    Input arguments: 
    - The item's name (partial matching and case insensitivity)
    """

    # First, we'll check the list of players. 
    # This function assumes the roll has already been done; we're just awarding the loot and keeping track of plusses. 

    # Check if the player is in the list of players.
    # Since players is a list of player objects, we'll need to iterate through it and check the name of each player.
    # If the player is not in the list, we'll output an error message and return.

    for p in players: 
        # Check the name using partial matching and case insensitivity, but we'll use starts_with() to make sure we don't match "A" to "B".
        if player_name.lower().startswith(p.name.lower()):
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

            else:
                print("Invalid roll type.")
                
            return
        
    # If we get here, the player wasn't found in the list of players.
    print("Player not found.")
    return

def export_loot(): 
    """
    Export loot received as console output. 
    We will sort players by soft-reserve plusses, then by regular plusses. 
    If there is a tie, we will sort alphabetically by name. 
    Under each name, we'll print out what items they received. 
    """

    # Sort the list of players by soft-reserve plusses, then by regular plusses. 
    # If there is a tie, we will sort alphabetically by name. 
    players.sort(key=lambda x: (x._soft_reserve_plusses, x._regular_plusses, x.name))

    # Print out the list of players.
    for p in players: 
        # Print out the player's name, and then the number of plusses they have; of both types. 
        print(f"{p.name} (+{p._regular_plusses} MS, +{p._soft_reserve_plusses} SR)")

        # If the regular plusses is not 0, we'll print out each item that they've received, by going in their log and checking for MS items. 
        if p._regular_plusses != 0:
            print("MS: ", end="")
            for l in p._log: 
                if l.roll == "MS":
                    print(f"- {l.item}")

        # We'll do the same for off-specs, but we'll first check if there are any OS items in the log. 
        # If there are, we'll print out the header.
        if any(l.roll == "OS" for l in p._log):
            print("OS: ", end="")
            for l in p._log: 
                if l.roll == "OS":
                    print(f"- {l.item}")

        # If the soft-reserve plusses is not 0, we'll print out each item that they've received, by going in their log and checking for SR items.
        if p._soft_reserve_plusses != 0:
            print("SR: ", end="")
            for l in p._log: 
                if l.roll == "SR":
                    print(f"- {l.item}")

        # Print a newline.
        print()