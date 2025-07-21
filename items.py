import requests, os, re, argparse, html
from tqdm import tqdm
from bs4 import BeautifulSoup

def parse_item_data(html): 
    out = {}

    # g_items[86321].tooltip_enus = "<table><tr><td><!--nstart--><b class=\"q4\">Gao-Rei, Staff of the Legendary Protector<\/b><!--nend--><!--ndstart--><!--ndend--><span class=\"q\"><br>Item Level <!--ilvl-->496<\/span><!--bo--><br>Binds when picked up<!--ue--><table width=\"100%\"><tr><td>Two-Hand<\/td><th><!--scstart2:10--><span class=\"q1\">Staff<\/span><!--scend--><\/th><\/tr><\/table><!--rf--><table width=\"100%\"><tr>\n    <td><span><!--dmg-->11,795 - 17,694 Damage<\/span><\/td>\n    <th>Speed <!--spd-->3.30<\/th>\n<\/tr><\/table><!--dps-->(4,468 damage per second)<br><span><!--stat3-->+1,223 Agility<\/span><br><span><!--stat7-->+1,835 Stamina<\/span><!--ebstats--><br><span class=\"q2\">+<!--rtg37-->828 Expertise<\/span><br><span class=\"q2\">+<!--rtg49-->795 Mastery<\/span><!--egstats--><!--eistats--><!--nameDescStats--><!--rs--><!--e--><br \/><br><a href=\"\/mop-classic\/items\/gems?filter=81;5;0\" class=\"socket-hydraulic q0\">Sha-Touched<\/a><!--ps--><br \/><br \/>Durability 120 \/ 120<\/td><\/tr><\/table><table><tr><td>Requires Level <!--rlvl-->90<br><!--rr--><!--itemEffects:0--><span class=\"q\">&quot;Sha-Touched&quot;<\/span><br><!--pvpEquip--><!--pvpEquip--><div class=\"whtt-sellprice\">Sell Price: <span class=\"moneygold\">73<\/span> <span class=\"moneysilver\">14<\/span> <span class=\"moneycopper\">70<\/span><\/div><div class=\"whtt-extra whtt-droppedby\">Dropped by: Tsulong<\/div><\/td><\/tr><\/table>";

    # g_items[87157].tooltip_enus = "<table><tr><td><!--nstart--><b class=\"q4\">Sunwrought Mail Hauberk<\/b><!--nend--><!--ndstart--><br \/><span style=\"color: #00FF00\">Heroic<\/span><!--ndend--><span class=\"q\"><br>Item Level <!--ilvl-->509<\/span><!--bo--><br>Binds when picked up<!--ue--><table width=\"100%\"><tr><td>Chest<\/td><th><!--scstart4:3--><span class=\"q1\">Mail<\/span><!--scend--><\/th><\/tr><\/table><!--rf--><span><!--amr-->4210 Armor<\/span><br><span><!--stat3-->+1,220 Agility<\/span><br><span><!--stat7-->+2,071 Stamina<\/span><!--ebstats--><br><span class=\"q2\">+<!--rtg31-->684 Hit<\/span><br><span class=\"q2\">+<!--rtg36-->933 Haste<\/span><!--egstats--><!--eistats--><!--nameDescStats--><!--rs--><!--e--><br \/><br><a href=\"\/mop-classic\/items\/gems?filter=81;2;0\" class=\"socket-red q0\">Red Socket<\/a><br><a href=\"\/mop-classic\/items\/gems?filter=81;3;0\" class=\"socket-yellow q0\">Yellow Socket<\/a><!--ps--><br><!--sb--><span class=\"q0\">Socket Bonus: +<!--ee15:0:90:750:0:0-->120 Agility<\/span><br \/><br \/>Durability 165 \/ 165<\/td><\/tr><\/table><table><tr><td>Requires Level <!--rlvl-->90<br><!--rr--><!--itemEffects:0--><!--pvpEquip--><!--pvpEquip--><div class=\"whtt-sellprice\">Sell Price: <span class=\"moneygold\">42<\/span> <span class=\"moneysilver\">47<\/span> <span class=\"moneycopper\">58<\/span><\/div><div class=\"whtt-extra whtt-droppedby\">Dropped by: Tsulong<\/div><\/td><\/tr><\/table>";

    # g_items[89239].tooltip_enus = "<table><tr><td><!--nstart--><b class=\"q4\">Chest of the Shadowy Vanquisher<\/b><!--nend--><!--ndstart--><!--ndend--><span class=\"q whtt-extra whtt-ilvl\"><br>Item Level <!--ilvl-->496<\/span><!--bo--><br>Binds when picked up<!--ue--><!--ebstats--><!--egstats--><!--eistats--><!--nameDescStats--><div class=\"wowhead-tooltip-item-classes\">Classes: <a href=\"\/mop-classic\/class=4\/rogue\" class=\"c4\">Rogue<\/a>, <a href=\"\/mop-classic\/class=6\/death-knight\" class=\"c6\">Death Knight<\/a>, <a href=\"\/mop-classic\/class=8\/mage\" class=\"c8\">Mage<\/a>, <a href=\"\/mop-classic\/class=11\/druid\" class=\"c11\">Druid<\/a><\/div><\/td><\/tr><\/table><table><tr><td>Requires Level <!--rlvl-->90<!--itemEffects:1--><br><!--pvpEquip--><!--pvpEquip--><div class=\"whtt-sellprice\">Sell Price: <span class=\"moneygold\">50<\/span><\/div><div class=\"whtt-extra whtt-droppedby\">Dropped by: Grand Empress Shek'zeer<\/div><\/td><\/tr><\/table>";

    # 1) category
    # <tr><td>Two-Hand<\/td><th><!--scstart2:10--><span class=\"q1\">Staff<\/span>
    
    soup = BeautifulSoup(html, 'html.parser')

    # A list of valid equipment slots to filter the correct <td>
    valid_slots = {
        'two-hand', 'one-hand', 'main hand', 'off hand',
        'chest', 'head', 'legs', 'feet', 'hands',
        'shoulder', 'waist', 'wrist', 'finger', 'neck', 'back', 'trinket'
    }
    armor_types = {
        'cloth', 'leather', 'mail', 'plate'
    }

    if re.search(r"Chest of the Shadowy (Conqueror|Protector|Vanquisher)", html):
        out['category'] = "Tier Set Token"

    else: 
        for table in soup.find_all('table'):
            tds = table.find_all('td')
            span = table.find('span', class_='q1')
            if tds and span:
                td_text = tds[0].get_text(strip=True)
                span_text = span.get_text(strip=True)

                if td_text.lower() in valid_slots and span_text.lower() in armor_types:
                    out['category'] = f"{span_text} {td_text}"
                    
                elif td_text.lower() in valid_slots:
                    out['category'] = f"{td_text} {span_text}"

    print(f"Category: {out.get('category', 'Unknown')}")

    # Item level
    out['item_level'] = None
    ilvl_match = re.search(r'Item Level <!--ilvl-->(\d+)', html)
    if ilvl_match:
        out['item_level'] = int(ilvl_match.group(1))

    print(f'Item level: {out.get("item_level", "Unknown")}')

    # Classes
    # <div class=\"wowhead-tooltip-item-classes\">Classes: <a href=\"\/mop-classic\/class=4\/rogue\" class=\"c4\">Rogue<\/a>, <a href=\"\/mop-classic\/class=6\/death-knight\" class=\"c6\">Death Knight<\/a>, <a href=\"\/mop-classic\/class=8\/mage\" class=\"c8\">Mage<\/a>, <a href=\"\/mop-classic\/class=11\/druid\" class=\"c11\">Druid<\/a><\/div>

    out['classes'] = []
    classes_div = soup.find('div', class_='wowhead-tooltip-item-classes')
    if classes_div:
        classes_links = classes_div.find_all('a')
        for link in classes_links:
            class_name = link.get_text(strip=True)
            out['classes'].append(class_name)

    if not out['classes']: out['classes'] = ['None']

    print(f'Classes: {", ".join(out.get("classes", []))}')

    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape item data from WoWHead.")
    parser.add_argument("--force", "-f", action="store_true")
    parser.add_argument("--output", "-o", default="all-items-mop.scsv")
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
        f.write("ID;Item;Item Level;Classes;Category;Binding;Stats\n")

    unique_items = sorted(set(mop_items))

    selected_items = [
        "Chest of the Shadowy Conqueror", "Chest of the Shadowy Protector", "Chest of the Shadowy Vanquisher",
        "Gao-Rei, Staff of the Legendary Protector", "Sunwrought Mail Hauberk"
    ]

    for item in unique_items: # tqdm(unique_items):
        # Debug to print entire HTML
        if not item in selected_items: continue 
        if not os.path.exists("./html"): os.makedirs("./html")

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
            
            print(f"\nProcessing {item} (ID: {item_id})...")
            parse_item_data(item_html)

            with open(f"./html/{item_id}.html", "w", encoding="utf-8") as html_file:
                html_file.write(item_html)