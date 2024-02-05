with open("gargul-export.txt") as f:
    lines = f.readlines()

import datetime
loot_history = {}

# Populate loot history with dates of Wednesdays and Sundays, beginning from 2023-10-15 to now
# 2023-10-15 is a Sunday

loot_history["2023-10-15"] = "No items"
loot_history["2023-10-18"] = "No items"
loot_history["2023-10-22"] = "No items"
loot_history["2023-10-25"] = "No items"
loot_history["2023-10-29"] = "No items"
loot_history["2023-11-01"] = "No items"
loot_history["2023-11-05"] = "No items"
loot_history["2023-11-08"] = "No items"
loot_history["2023-11-12"] = "No items"
loot_history["2023-11-15"] = "No items"
loot_history["2023-11-19"] = "No items"
loot_history["2023-11-22"] = "No items"
loot_history["2023-11-26"] = "No items"
loot_history["2023-11-29"] = "No items"
loot_history["2023-12-03"] = "No items"
loot_history["2023-12-06"] = "No items"
loot_history["2023-12-10"] = "No items"
loot_history["2023-12-13"] = "No items"
loot_history["2023-12-17"] = "No items"
loot_history["2023-12-20"] = "No items"
loot_history["2023-12-24"] = "No items"
loot_history["2023-12-27"] = "No items"
loot_history["2023-12-31"] = "No items"
loot_history["2024-01-03"] = "No items"
loot_history["2024-01-07"] = "No items"
loot_history["2024-01-10"] = "No items"
loot_history["2024-01-14"] = "No items"
loot_history["2024-01-17"] = "No items"
loot_history["2024-01-21"] = "No items"
loot_history["2024-01-24"] = "No items"
loot_history["2024-01-28"] = "No items"
loot_history["2024-01-31"] = "No items"
loot_history["2024-02-04"] = "No items"

shards = 0

for date in loot_history.keys(): 
    # @ID;@ITEM;@ILVL;@SR;@OS;@WINNER;@YEAR-@MONTH-@DAY
    # 49999;Skeleton Lord's Circle;264;1;0;Ferrousblade;2023-10-15

    strpdate = datetime.datetime.strptime(date, "%Y-%m-%d")

    if strpdate.weekday() not in [2, 6]:
        continue # Off night stuff

    # Count the number of items total that dropped on this date 
    total_items = 0
    for l in lines: 
        if l.strip().split(";")[6] == date: 
            total_items += 1

    if total_items > 0: 
        loot_history[date] = 0
        for l in lines: 
            if l.strip().split(";")[6] == date: 
                if "Shadowfrost Shard" in l and l.strip().split(";")[5] == "Artaz":
                    loot_history[date] += 1

        shards += loot_history[date]

for date, loot in loot_history.items():
    # Print the date and the number of Shadowfrost Shards recorded. 
    print(f"{date}: {loot}")

print(f"Total Shadowfrost Shards: {shards}")