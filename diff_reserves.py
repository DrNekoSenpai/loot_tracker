local_file = "loot_reserves.csv"
remote_file = "softresit.csv"
item_database_file = "all-items-mop.scsv"

with open(local_file, "r") as f:
    local_reserves = f.readlines()

with open(remote_file, "r") as f:
    remote_reserves = f.readlines()

with open(item_database_file, "r") as f:
    item_database = f.readlines()

# Remote reserve format; 
# Item,ItemId,From,Name,Class,Spec,Note,Plus,Date
# "Elegion, the Fanged Crescent",86130,Elegon,Snedcharos,Deathknight,Frost,,0,"2025-08-28 21:53:33"
# "Lei Shen's Final Orders",86144,"Will of the Emperor",Snedcharos,Deathknight,Frost,,0,"2025-08-28 21:53:33"
# "Light of the Cosmos",86133,Elegon,Snedarashi,Shaman,Elemental,,0,"2025-08-28 21:54:00"
# "Tihan, Scepter of the Sleeping Emperor",86148,"Will of the Emperor",Snedarashi,Shaman,Elemental,,0,"2025-08-28 21:54:00"

# Local reserve format;
# Player,Class,Plus,ExtraReserves,RollBonus,Item,Count
# Snedcharos,DEATHKNIGHT,0,0,0,89249,1
# Snedcharos,DEATHKNIGHT,0,0,0,89258,1

# We want to write a function that takes reserves written in remote format, and converts them into local format; overwriting if necessary

class remote_reserve: 
    def __init__(self, line):
        parts = line.split(",")

        if len(parts) > 9: # Handle quoted item names
            self.item_name = ",".join(parts[0:2])  # Remove quotes
            self.item_id = parts[2]
            self.player_name = parts[4]
            self.player_class = parts[5].upper()
            print(f"Parsed quoted item name: '{self.item_name}', {self.item_id}, {self.player_name}, {self.player_class}")

        else: 
            self.item_name = parts[0]
            self.item_id = parts[1]
            self.player_name = parts[3]
            self.player_class = parts[4].upper()
            print(f"Parsed unquoted item name: '{self.item_name}', {self.item_id}, {self.player_name}, {self.player_class}")

    def to_local_format(self, item_database):
        return f"{self.player_name},{self.player_class},0,0,0,{self.item_id},1\n"

# Update local reserves, overwriting everything that's there. Keep the header, but nothing else 

def update_reserves(local_file, remote_file, item_database):
    with open(local_file, "r") as f:
        local_lines = f.readlines()
    
    header = local_lines[0]
    new_reserves = [header]

    for line in remote_file[1:]:  # Skip header
        rr = remote_reserve(line)
        local_line = rr.to_local_format(item_database)
        if local_line:
            new_reserves.append(local_line)

    with open(local_file, "w") as f:
        f.writelines(new_reserves)

update_reserves(local_file, remote_reserves, item_database)