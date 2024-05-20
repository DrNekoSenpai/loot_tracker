import requests, os, re
from tqdm import tqdm

# Read IDs from file and split based on comma
with open("cata-ids.txt", "r", encoding="utf-8") as ids_file:
    cata_ids = [i.strip() for i in ids_file.read().split(",")]

# Read items from file and process quotes and concatenations
with open("cata-items.txt", "r", encoding="utf-8") as items_file:
    cata_items = [i.strip() for i in items_file.read().split(",")]
    i = 0
    while i < len(cata_items):
        if '"' in cata_items[i]:
            cata_items[i] = cata_items[i].replace('"', '') + ", " + cata_items[i+1].replace('"', '')
            cata_items.pop(i + 1)
        i += 1

# Assert that both lists are of the same length
assert len(cata_ids) == len(cata_items)
print(f"Number of items: {len(cata_items)}")

# Create directory if it doesn't exist
if not os.path.exists("./items/"):
    os.makedirs("./items/")

else: 
    # Delete everything in the directory
    for file in os.listdir("./items/"):
        os.remove(f"./items/{file}")

# Sort cata_items and cata_ids based on the items; by item name ascending, then by ID ascending
cata_items, cata_ids = zip(*sorted(zip(cata_items, cata_ids)))

if not os.path.exists("all-items-cata.txt"):
    with open("all-items-cata.txt", "w", encoding="utf-8") as all_items_file:
        all_items_file.write("ID;Item;Item Level;Classes;Category;Bind;Version\n")

else: 
    # Open the file and figure out where we left off
    with open("all-items-cata.txt", "r", encoding="utf-8") as all_items_file:
        lines = all_items_file.readlines()
        last_item_id = lines[-1].split(";")[0]
        last_item_index = cata_ids.index(last_item_id)
        cata_ids = cata_ids[last_item_index + 1:]
        cata_items = cata_items[last_item_index + 1:]

# ilvl_pattern = re.compile(r"item level(?: of)? (\d+)", re.IGNORECASE)
ilvl_pattern = re.compile(r"Item Level <!--ilvl-->(\d+)", re.IGNORECASE)
cat_pattern = re.compile(r"In the (.+?) category", re.IGNORECASE)
slot_pattern = re.compile(r"goes in the &quot;(.+?)&quot; slot", re.IGNORECASE)
armor_type_pattern = re.compile(r"<span class=\"q1\">(Cloth|Leather|Mail|Plate)<\/span>")

# <div class="wowhead-tooltip-item-classes">Classes: <a href="/cata/class=4/rogue" class="c4">Rogue</a>, <a href="/cata/class=6/death-knight" class="c6">Death Knight</a>, <a href="/cata/class=8/mage" class="c8">Mage</a>, <a href="/cata/class=11/druid" class="c11">Druid</a></div>
# Capture the classes that can use the item
classes_pattern = re.compile(r'<a href="/cata/class=\d+/.*?" class="c\d+">(.*?)</a>')

boe_pattern = re.compile(r"<br>Binds when equipped<br>")
boa_pattern = re.compile(r"<br>Binds to account<br>")

unique_items = sorted(list(set(cata_items)))

for item in tqdm(unique_items):
    with open(f"all-items-cata.txt", "a", encoding="utf-8") as all_items_file:
        count = cata_items.count(item)
        if count == 1: 
            # Find the ID of the matching item
            item_id = cata_ids[cata_items.index(item)]
            item_url = item.replace(" ", "-").replace(",", "").lower()
            url = f"https://www.wowhead.com/cata/item={item_id}/{item_url}"
            difficulty = "Normal"
            text = requests.get(url).text

            if ilvl_pattern.search(text): item_level = ilvl_pattern.search(text).group(1)
            else: item_level = None

            if slot_pattern.search(text): category = slot_pattern.search(text).group(1)
            elif cat_pattern.search(text): category = cat_pattern.search(text).group(1)
            else: category = None

            if category is not None: 
                if armor_type_pattern.search(text): armor_type = armor_type_pattern.search(text).group(1)
                else: armor_type = None

            if armor_type is not None: category = f"{armor_type} {category}"

            if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
            else: classes = None

            if boe_pattern.search(text): bind = "Binds when equipped"
            elif boa_pattern.search(text): bind = "Binds to account"
            else: bind = "Binds when picked up"
                    
            all_items_file.write(f"{item_id};{item};{item_level};{classes};{category};{bind};{difficulty}\n")
            
        elif count == 2: 
            # Find the IDs of the matching items
            item_ids = [cata_ids[i] for i, x in enumerate(cata_items) if x == item]
            item_url = item.replace(" ", "-").replace(",", "").lower()
            ilvls = []

            for item_id in item_ids:
                url = f"https://www.wowhead.com/cata/item={item_id}/{item_url}"
                text = requests.get(url).text

                if ilvl_pattern.search(text): item_level = ilvl_pattern.search(text).group(1)
                else: item_level = None

                ilvls.append(item_level)

            if slot_pattern.search(text): category = slot_pattern.search(text).group(1)
            elif cat_pattern.search(text): category = cat_pattern.search(text).group(1)
            else: category = None

            if category is not None: 
                if armor_type_pattern.search(text): armor_type = armor_type_pattern.search(text).group(1)
                else: armor_type = None

            if armor_type is not None: category = f"{armor_type} {category}"

            if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
            else: classes = None

            if boe_pattern.search(text): bind = "Binds when equipped"
            elif boa_pattern.search(text): bind = "Binds to account"
            else: bind = "Binds when picked up"

            item_ids, ilvls = zip(*sorted(zip(item_ids, ilvls), key=lambda x: x[1], reverse=True))
            if ilvls[0] == ilvls[1]: difficulties = ["Normal", "Normal"]
            else: difficulties = ["Heroic", "Normal"]

            for i, item_id in enumerate(item_ids):
                all_items_file.write(f"{item_id};{item};{ilvls[i]};{classes};{category};{bind};{difficulties[i]}\n")

        elif count == 3: 
            # Find the IDs of the matching items
            item_ids = [cata_ids[i] for i, x in enumerate(cata_items) if x == item]
            item_url = item.replace(" ", "-").replace(",", "").lower()
            ilvls = []

            for item_id in item_ids:
                url = f"https://www.wowhead.com/cata/item={item_id}/{item_url}"
                text = requests.get(url).text

                if ilvl_pattern.search(text): item_level = ilvl_pattern.search(text).group(1)
                else: item_level = None

                ilvls.append(item_level)

            if slot_pattern.search(text): category = slot_pattern.search(text).group(1)
            elif cat_pattern.search(text): category = cat_pattern.search(text).group(1)
            else: category = None

            if category is not None: 
                if armor_type_pattern.search(text): armor_type = armor_type_pattern.search(text).group(1)
                else: armor_type = None

            if armor_type is not None: category = f"{armor_type} {category}"

            if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
            else: classes = None

            if boe_pattern.search(text): bind = "Binds when equipped"
            elif boa_pattern.search(text): bind = "Binds to account"
            else: bind = "Binds when picked up"

            # print(f"{item}", end = "")

            item_ids, ilvls = zip(*sorted(zip(item_ids, ilvls), key=lambda x: x[1], reverse=True))
            if ilvls[0] == ilvls[1] == ilvls[2]: difficulties = ["Normal", "Normal", "Normal"]
            elif ilvls[0] > ilvls[1] == ilvls[2]: difficulties = ["Heroic", "Normal", "Normal"]
            elif ilvls[0] == ilvls[1] > ilvls[2]: difficulties = ["Heroic", "Heroic", "Normal"]
            else: difficulties = ["Heroic", "Normal", "LFR"]

            # print(f" {item_ids} {ilvls} {difficulties}")

            for i, item_id in enumerate(item_ids):
                all_items_file.write(f"{item_id};{item};{ilvls[i]};{classes};{category};{bind};{difficulties[i]}\n")

        # with open(f"./items/{item_id}_{item_url}.html", "w", encoding="utf-8") as item_file:
        #     item_file.write(text)