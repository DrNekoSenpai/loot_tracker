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

def armor_subtype(text, base_type): 
    text = text.lower()

    if "resilience" in text: return f"{base_type} (PvP)"
    if "random enchantment" in text: return f"{base_type} (Random)"
    
    if "spirit" in text and "intellect" in text: return f"{base_type} (Healing)"

    elif "hit rating" in text:
        if "intellect" in text: return f"{base_type} (Caster)" 
        else: return f"{base_type} (Damage)"

    elif "expertise rating" in text: 
        if "agility" in text: return f"{base_type} (Melee Agility)"
        elif "strength" in text: return f"{base_type} (Melee Strength)"

    elif "dodge" in text or "parry" in text: return f"{base_type} (Tank)"

    elif "intellect" in text: return f"{base_type} (Intellect)"
    elif "agility" in text: return f"{base_type} (Agility)"
    elif "strength" in text: return f"{base_type} (Strength)"

    else: return f"{base_type}"

# <h1 class="heading-size-1">Alysra's Razor</h1>
# <noscript><table><tr><td><!--nstart--><!--nend--><!--ndstart--><!--ndend--><span class="q"><br>Item Level <!--ilvl-->378</span><!--bo--><br>Binds when picked up<!--ue--><table width="100%"><tr><td>One-Hand</td><th><!--scstart2:15--><span class="q1">Dagger</span><!--scend--></th></tr></table><!--rf--><table width="100%"><tr>
#     <td><span><!--dmg-->540 - 1,004 Damage</span></td>
#     <th>Speed <!--spd-->1.40</th>
# </tr></table><!--dps-->(551.43 damage per second)<br><span><!--stat3-->+155 Agility</span><br><span><!--stat7-->+262 Stamina</span><!--ebstats--><!--egstats--><!--eistats--><!--nameDescStats--><!--rs--><!--e--><br /><br><a href="/cata/items/gems?filter=81;3;0" class="socket-yellow q0">Yellow Socket</a><!--ps--><br><!--sb--><span class="q0">Socket Bonus: +10 Agility</span><br /><br />Durability 75 / 75</td></tr></table><table><tr><td>Requires Level <!--rlvl-->85<br><!--rr--><span class="q2">Equip: Improves haste rating by <!--rtg36-->113.</span><br><span class="q2">Equip: Increases your expertise rating by <!--rtg37-->98.</span><!--itemEffects:1--><div class="whtt-sellprice">Sell Price: <span class="moneygold">36</span> <span class="moneysilver">51</span> <span class="moneycopper">89</span></div><div class="whtt-extra whtt-droppedby">Dropped by: Alysrazor</div></td></tr></table><!--i?70733:1:85:85--></noscript>

# Search only in this part of the text, beginning with the h1 and ending with the noscript tag
item_pattern = re.compile(r"<h1 class=\"heading-size-1\">(.*?)</h1>.*?<noscript>(.*?)</noscript>", re.DOTALL)

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
            text = item_pattern.search(text).group(2)

            subcategory = armor_subtype(text, category)
            try: 
                if "Unknown" in subcategory: print(f"{item} -- {subcategory}")
            except: 
                continue

            if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
            else: classes = None

            if boe_pattern.search(text): bind = "Binds when equipped"
            elif boa_pattern.search(text): bind = "Binds to account"
            else: bind = "Binds when picked up"
                    
            all_items_file.write(f"{item_id};{item};{item_level};{classes};{subcategory};{bind};{difficulty}\n")
            
        else: 
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
            text = item_pattern.search(text).group(2)

            subcategory = armor_subtype(text, category)
            try: 
                if "Unknown" in subcategory: print(f"{item} -- {subcategory}")
            except: 
                continue

            if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
            else: classes = None

            if boe_pattern.search(text): bind = "Binds when equipped"
            elif boa_pattern.search(text): bind = "Binds to account"
            else: bind = "Binds when picked up"

            # Sort item_ids and ilvls by item level in descending order
            item_ids, ilvls = zip(*sorted(zip(item_ids, ilvls), key=lambda x: x[1], reverse=True))

            # Identify unique item levels and sort them in descending order
            unique_ilvls = sorted(set(ilvls), reverse=True)

            # Create a mapping of item levels to difficulties
            difficulty_map = {}
            if len(unique_ilvls) == 1:
                difficulty_map[unique_ilvls[0]] = "Normal"
            elif len(unique_ilvls) == 2:
                difficulty_map[unique_ilvls[0]] = "Heroic"
                difficulty_map[unique_ilvls[1]] = "Normal"
            elif len(unique_ilvls) >= 3:
                difficulty_map[unique_ilvls[0]] = "Heroic"
                difficulty_map[unique_ilvls[1]] = "Normal"
                difficulty_map[unique_ilvls[2]] = "LFR"

            # Assign difficulties to each item based on the item level
            difficulties = [difficulty_map[ilvl] for ilvl in ilvls]

            if len(item_ids) > 3: 
                # Print difficulties and ilvls
                print(f"Number of items: {len(item_ids)}")
                for i, item_id in enumerate(item_ids):
                    print(f"{item_id}: {difficulties[i]} -- {ilvls[i]}")

            for i, item_id in enumerate(item_ids):
                all_items_file.write(f"{item_id};{item};{ilvls[i]};{classes};{subcategory};{bind};{difficulties[i]}\n")

#         with open(f"./items/{item_id}_{item_url}.html", "w", encoding="utf-8") as item_file:
#             item_file.write(text)