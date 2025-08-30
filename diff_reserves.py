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

# We want to write a function that takes players in local_reserves and remote_reserves, and diffs them
# Priority favors local_reserves -- so if a player reserved different items in local_reserves, we want to copy the format given in remote_reserves and update what they reserved

# For example, in the example, Snedcharos reserved item 89249 -- Chest of the Shadowy Vanquisher and 89258 -- Helm of the Shadowy Vanquisher

# We want to update remote reserve to reflect this, so we change the lines for Snedcharos to: 

# "Chest of the Shadowy Vanquisher",89249,,Snedcharos,Deathknight,Frost,,0,"2025-08-28 21:53:33"
# "Helm of the Shadowy Vanquisher",89258,,Snedcharos,Deathknight,Frost,,0,"2025-08-28 21:53:33"