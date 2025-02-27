import os
from collections import defaultdict

def combine_logs(directory):
    logs_by_date = defaultdict(list)

    # Fetch file list dynamically
    files = os.listdir(directory)

    for file in files:
        if file.startswith("WoWCombatLog") and file.endswith(".txt"):
            try:
                date_part = file.split('-')[1].split('_')[0]
                logs_by_date[date_part].append(file)
            except IndexError:
                continue  # Skip improperly named files

    for date, log_files in logs_by_date.items():
        # Sort files by timestamp numerically
        log_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))

        combined_content = ""

        for log_file in log_files:
            with open(os.path.join(directory, log_file), 'r', encoding='utf-8') as f:
                combined_content += f.read() + '\n'  # Ensure separation between logs

        # Rearrange date to be in YYYY-MM-DD format, but this is in DDMMYY format; assume we are in the 21st century
        date = f"20{date[4:6]}-{date[2:4]}-{date[0:2]}"

        # Save as a new file to avoid modifying existing logs
        combined_filename = f"WoWCombatLog-{date}.txt"
        with open(os.path.join(directory, combined_filename), 'w', encoding='utf-8') as f:
            f.write(combined_content)

        # Delete old log files
        for log_file in log_files:
            os.remove(os.path.join(directory, log_file))

combine_logs("C:\\Program Files (x86)\\World of Warcraft\\_classic_\\Logs")