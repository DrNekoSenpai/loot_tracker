import requests, os, re, argparse
from tqdm import tqdm

parser = argparse.ArgumentParser(description="Scrape item data from WoWHead.")
parser.add_argument("--force", action="store_true", help="Force the script to start from the beginning.")
parser.add_argument("--output", default="all-items-cata.scsv", help="Output file name.")
args = parser.parse_args()

def armor_subtype(text, item, base_type): 
    # If the base type is a trinket, just return it as is
    if base_type.strip().lower() == "trinket": 
        if not os.path.exists("trinkets.txt"):
            with open("trinkets.txt", "w", encoding="utf-8") as trinkets_file:
                trinkets_file.write("")

        with open("trinkets.txt", "a", encoding="utf-8") as trinkets_file:
            trinkets_file.write(f"{item}:\n\n{text}\n\n")

        return "Trinket"

    text = text.lower()

    if "resilience" in text: return f"{base_type} (PvP)"
    if "random enchantment" in text: return f"{base_type} (Random)"
    
    if "spirit" in text and "intellect" in text: return f"{base_type} (Intellect w/ Spirit)"
    elif "dodge" in text or "parry" in text: return f"{base_type} (Tank)"

    elif "hit rating" in text:
        if "intellect" in text: return f"{base_type} (Intellect w/ Hit)" 
        elif "agility" in text: return f"{base_type} (Agility w/ Hit)"
        elif "strength" in text: return f"{base_type} (Strength w/ Hit)"

    elif "expertise rating" in text: 
        if "agility" in text: return f"{base_type} (Agility w/ Expertise)"
        elif "strength" in text: return f"{base_type} (Strength w/ Expertise)"

    elif "intellect" in text: return f"{base_type} (Intellect)"
    elif "agility" in text: return f"{base_type} (Agility)"
    elif "strength" in text: return f"{base_type} (Strength)"

    else: return f"{base_type}"

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

if __name__ == "__main__":
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

    # Sort cata_items and cata_ids based on the items; by item name ascending, then by ID ascending
    cata_items, cata_ids = zip(*sorted(zip(cata_items, cata_ids)))

    tier_set_tokens = [
        "Chest of the Forlorn Conqueror", 
        "Chest of the Forlorn Protector",
        "Chest of the Forlorn Vanquisher",
        "Mantle of the Forlorn Conqueror",
        "Mantle of the Forlorn Protector",
        "Mantle of the Forlorn Vanquisher",
        "Leggings of the Forlorn Conqueror",
        "Leggings of the Forlorn Protector",
        "Leggings of the Forlorn Vanquisher",
        "Crown of the Forlorn Conqueror",
        "Crown of the Forlorn Protector",
        "Crown of the Forlorn Vanquisher",
        "Shoulders of the Forlorn Conqueror",
        "Shoulders of the Forlorn Protector",
        "Shoulders of the Forlorn Vanquisher",
    ]

    # If the argparse flag is set, start from the beginning
    if args.force:
        with open(args.output, "w", encoding="utf-8") as all_items_file:
            all_items_file.write("ID;Item;Item Level;Classes;Category;Version\n")

    else: 
        if not os.path.exists(args.output):
            with open(args.output, "w", encoding="utf-8") as all_items_file:
                all_items_file.write("ID;Item;Item Level;Classes;Category;Version\n")

        else: 
            # Open the file and figure out where we left off
            with open(args.output, "r", encoding="utf-8") as all_items_file:
                lines = all_items_file.readlines()
                last_item_id = lines[-1].split(";")[0]
                last_item_index = cata_ids.index(last_item_id)
                cata_ids = cata_ids[last_item_index + 1:]
                cata_items = cata_items[last_item_index + 1:]

    ilvl_pattern = re.compile(r"Item Level <!--ilvl-->(\d+)", re.IGNORECASE)

    # Search only in this part of the text, beginning with the h1 and ending with the noscript tag
    item_pattern = re.compile(r"<h1 class=\"heading-size-1\">(.*?)</h1>.*?<noscript>(.*?)</noscript>", re.DOTALL)
    classes_pattern = re.compile(r'<a href="/cata/class=\d+/.*?" class="c\d+">(.*?)</a>')

    armor_type_pattern = re.compile(r"<span class=\"q1\">(Cloth|Leather|Mail|Plate)<\/span>")
    category_pattern = re.compile(r'<table width="100%"><tr><td>(.*?)</td>(?:<th>.*<span class="q1">(.*?)</span>)?')

    unique_items = sorted(list(set(cata_items)))

    for item in tqdm(unique_items):
        item_written = False
        with open(args.output, "a", encoding="utf-8") as all_items_file:
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

                category = re.findall(category_pattern, text)[0] if category_pattern.search(text) else "ETC"
                if category[1] in ["Cloth", "Leather", "Mail", "Plate"]: category = (category[1], category[0])
                if type(category) is tuple: category = " ".join(category)

                if item in tier_set_tokens: category = "Tier Set Token"

                text = item_pattern.search(text).group(2)

                subcategory = armor_subtype(text, item, category)
                if subcategory is not None: 
                    subcategory = subcategory.replace("  ", " ")

                if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
                else: classes = None
                        
                all_items_file.write(f"{item_id};{item};{item_level};{classes};{subcategory};{difficulty}\n")
                
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

                category = re.findall(category_pattern, text)[0] if category_pattern.search(text) else "ETC"
                if category[1] in ["Cloth", "Leather", "Mail", "Plate"]: category = (category[1], category[0])
                if type(category) is tuple: category = " ".join(category)
                category = category.replace("  ", " ")

                text = item_pattern.search(text).group(2)

                subcategory = armor_subtype(text, item, category)
                try: 
                    if "Unknown" in subcategory: print(f"{item} -- {subcategory}")
                except: 
                    continue

                if classes_pattern.search(text): classes = ', '.join(classes_pattern.findall(text))
                else: classes = None

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

                for i, item_id in enumerate(item_ids):
                    all_items_file.write(f"{item_id};{item};{ilvls[i]};{classes};{subcategory};{difficulties[i]}\n")