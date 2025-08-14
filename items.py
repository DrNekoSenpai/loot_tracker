import requests, os, re, argparse, html
from tqdm import tqdm
from bs4 import BeautifulSoup

def parse_item_data(html): 
    out = {}
    
    soup = BeautifulSoup(html, 'html.parser')

    valid_slots = {
        'two-hand', 'one-hand', 'main hand', 'off hand',
        'chest', 'head', 'legs', 'feet', 'hands',
        'shoulder', 'waist', 'wrist', 'finger', 'neck', 'back', 'trinket'
    }
    armor_types = {
        'cloth', 'leather', 'mail', 'plate'
    }

    out['category'] = ''

    if re.search(r"Chest of the Shadowy (Conqueror|Protector|Vanquisher)", html):
        out['category'] = "Tier Set Token"

    else: 
        if re.search(r"({})".format('|'.join(armor_types)), html, re.IGNORECASE):
            armor_match = re.search(r"({})".format('|'.join(armor_types)), html, re.IGNORECASE)
            if armor_match:
                out['category'] = f"{armor_match.group(0).strip().title()}"

        if re.search(r"({})".format('|'.join(valid_slots)), html, re.IGNORECASE):
            slot_match = re.search(r"({})".format('|'.join(valid_slots)), html, re.IGNORECASE)
            if slot_match:
                out['category'] = f"{out['category']} {slot_match.group(0).strip().title()}".strip()

    if out['category'] == ' ':
        out['category'] = 'None'

    # Item level
    out['item_level'] = None
    ilvl_match = re.search(r'Item Level <!--ilvl-->(\d+)', html)
    if ilvl_match:
        out['item_level'] = int(ilvl_match.group(1))

    # Classes

    out['classes'] = []
    classes_div = soup.find('div', class_='wowhead-tooltip-item-classes')
    if classes_div:
        classes_links = classes_div.find_all('a')
        for link in classes_links:
            class_name = link.get_text(strip=True)
            out['classes'].append(class_name)

    if not out['classes']: out['classes'] = ['None']

    # Primary stat -- Intellect, Agility, Strength 

    out['primary_stats'] = ""
    
    if re.search(r"\d+\s+(Intellect|Agility|Strength)", html):
        stat_match = re.search(r"\d+\s+(Intellect|Agility|Strength)", html)
        out['primary_stats'] = f"{stat_match.group(1)}"

    if not out['primary_stats']: 
        stamina_match = re.search(r"\d+\s+Stamina", html)

        # Only list stamina if no other primary stat is found
        if stamina_match: out['primary_stats'] = "Stamina"
        else: out['primary_stats'] = 'None'

    # Secondary stats -- Haste, Mastery, Crit, Hit, Expertise, Dodge, Parry, Spirit -- we need to find all stats present

    out['secondary_stats'] = set()

    if re.search(r"\d+\s+(Haste|Mastery|Crit|Hit|Expertise|Dodge|Parry|Spirit)", html, re.IGNORECASE):
        secondary_stats = re.findall(r"\d+\s+(Haste|Mastery|Crit|Hit|Expertise|Dodge|Parry|Spirit)", html, re.IGNORECASE)
        for stat in secondary_stats:
            out['secondary_stats'].add(f"{stat}")

    # Special case: trinket proc/use effects

    if out['category'] == 'Trinket': 
        use_trinket_match = re.search(r'(Use: .*)', html)
        if use_trinket_match:
            use_line = use_trinket_match.group(0)

            use_match = re.search(r'Increases your (Intellect|Agility|Strength|Stamina|Haste|Mastery|Critical Strike|Hit|Expertise|Dodge|Parry|Spirit) by .* for \d+ sec.', use_line, re.IGNORECASE)
            if use_match:
                out['secondary_stats'].add(f"Use: {use_match.group(1).title()}")

        proc_trinket_match = re.search(r'(Equip: .*)', html)
        if proc_trinket_match:
            stat_line = proc_trinket_match.group(0)
            # print(f"Stat line: {stat_line}")

            stat_match = re.search(r'chance to .* (Intellect|Agility|Strength|Stamina|Haste|Mastery|Critical Strike|Hit|Expertise|Dodge|Parry|Spirit) for \d+ sec.', stat_line, re.IGNORECASE)
            if stat_match:
                out['secondary_stats'].add(f"Equip: {stat_match.group(1).title()}")

    if not out['secondary_stats']: out['secondary_stats'] = ['None']
    else: 
        out['secondary_stats'] = list(out['secondary_stats'])
        # Replace all instances of 'Critical Strike' with 'Crit'
        out['secondary_stats'] = [stat.replace('Critical Strike', 'Crit') for stat in out['secondary_stats']]

        # If there is a Use or Equip effect in secondary stats, it should be the last item in the list 
        use_effects = [stat for stat in out['secondary_stats'] if stat.startswith('Use:')]
        equip_effects = [stat for stat in out['secondary_stats'] if stat.startswith('Equip:')]

        if use_effects:
            out['secondary_stats'].remove(use_effects[0])
            out['secondary_stats'].append(use_effects[0])

        if equip_effects:
            out['secondary_stats'].remove(equip_effects[0])
            out['secondary_stats'].append(equip_effects[0])

    # Sockets

    out['sockets'] = []
    # First, search for the socket hrefs
    socket_links = re.findall(r'<a href="/mop-classic/items/gems\?filter=81;\d+;\d+" class="socket-.*? q0">(.+?) Socket</a>', html)
    for socket_type in socket_links:
        out['sockets'].append(socket_type)

    if len(out['sockets']) == 0:
        out['sockets'] = ['None']

    else: 
        # If sockets are there, then check for socket bonus. It could be a primary stat or a secondary stat 
        socket_bonus_match = re.search(r'<span class="q0">Socket Bonus: \+<!--ee\d+:\d+:\d+:\d+:\d+:\d+-->\d+\s+(Intellect|Agility|Strength|Haste|Mastery|Crit|Hit|Expertise|Dodge|Parry|Spirit)</span>', html)
        if socket_bonus_match:
            out['socket_bonus'] = socket_bonus_match.group(1)

    if 'socket_bonus' not in out:
        out['socket_bonus'] = 'None'

    # Binding 

    out['binding'] = 'None'
    binding_match = re.search(r'Binds when (picked up|equipped)', html)
    if binding_match:
        out['binding'] = f"Binds when {binding_match.group(1)}"

    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape item data from WoWHead.")
    parser.add_argument("--force", "-f", action="store_true")
    parser.add_argument("--output", "-o", default="all-items-mop.scsv")
    parser.add_argument("--html", "-t", action="store_true", help="Save HTML files for each item.")
    args = parser.parse_args()

    with open("mop-ids.txt", "r", encoding="utf-8") as ids_file:
        mop_ids = [i.strip() for i in ids_file.read().split(",")]

    with open("mop-items.txt", "r", encoding="utf-8") as items_file:
        mop_items = [i.strip() for i in items_file.read().split(",")]
        i = 0
        while i < len(mop_items):
            if '"' in mop_items[i]:
                mop_items[i] = mop_items[i].replace('"', '') + ", " + mop_items[i+1].replace('"', '')
                mop_items.pop(i + 1)
            i += 1

    assert len(mop_ids) == len(mop_items)
    mop_items, mop_ids = zip(*sorted(zip(mop_items, mop_ids)))

    tier_set_tokens = [
        "Helm of the Shadowy Conqueror", "Helm of the Shadowy Protector", "Helm of the Shadowy Vanquisher",
        "Shoulders of the Shadowy Conqueror", "Shoulders of the Shadowy Protector", "Shoulders of the Shadowy Vanquisher",
        "Chest of the Shadowy Conqueror", "Chest of the Shadowy Protector", "Chest of the Shadowy Vanquisher",
        "Gauntlets of the Shadowy Conqueror", "Gauntlets of the Shadowy Protector", "Gauntlets of the Shadowy Vanquisher",
        "Leggings of the Shadowy Conqueror", "Leggings of the Shadowy Protector", "Leggings of the Shadowy Vanquisher",
    ]

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("ID;Item;Item Level;Classes;Category;Binding;Primary Stats;Secondary Stats;Sockets;Socket Bonus\n")
        # Item: Grasps of Serpentine Might, ID: 89843, Data: {'category': 'Plate Hands', 'item_level': 496, 'classes': ['None'], 'primary_stats': 'Strength', 'secondary_stats': ['Parry', 'Expertise'], 'sockets': ['Blue'], 'socket_bonus': 'Parry', 'binding': False}

    unique_items = sorted(set(mop_items))

    selected_items = [
        # "Arrow Breaking Windcloak"
    ]

    if not os.path.exists("html"): 
        os.makedirs("html")

    for item in tqdm(unique_items):
        # Debug to print entire HTML
        if len(selected_items) > 0 and not item in selected_items: continue 

        item_indices = [i for i, x in enumerate(mop_items) if x == item]
        item_ids = [mop_ids[i] for i in item_indices]
        item_url = item.replace(" ", "-").replace(",", "").lower()
        item_data = []

        for item_id in item_ids:
            url = f"https://www.wowhead.com/mop-classic/item={item_id}/{item_url}"
            item_html = requests.get(url).text
            # Find line in HTML that contains the following: 
            # g_items[89237].tooltip_enus, replace 89237 with actual item_id 
            # Delete everything else in the HTML, we only need to keep this line 

            item_html = re.search(r'g_items\[' + re.escape(item_id) + r'\]\.tooltip_enus\s*=\s*"(.*?)";', item_html, re.DOTALL)
            if item_html: item_html = item_html.group(1)

            item_html = item_html.replace("\\", "").replace("\\'", "'").replace('\\/', '/')
            item_html = html.unescape(item_html)
            
            # print(f"\nProcessing {item} (ID: {item_id})...")
            # parse_item_data(item_html)

            item_data = parse_item_data(item_html)
            # print(f"Item: {item}, ID: {item_id}, Data: {item_data}")
            
            # f.write("ID;Item;Item Level;Classes;Category;Binding;Primary Stats;Secondary Stats;Sockets;Socket Bonus\n")
            # Item: Grasps of Serpentine Might, ID: 89843, Data: {'category': 'Plate Hands', 'item_level': 496, 'classes': ['None'], 'primary_stats': 'Strength', 'secondary_stats': ['Parry', 'Expertise'], 'sockets': ['Blue'], 'socket_bonus': 'Parry', 'binding': False}

            with open(args.output, "a", encoding="utf-8") as f:
                f.write(f"{item_id};{item};{item_data['item_level']};{', '.join(item_data['classes'])};{item_data['category']};{item_data['binding']};{item_data['primary_stats']};{', '.join(item_data['secondary_stats'])};{', '.join(item_data['sockets'])};{item_data['socket_bonus']}\n")

            if args.html: 
                with open(f"./html/{item_id}.html", "w", encoding="utf-8") as html_file:
                    html_file.write(item_html)