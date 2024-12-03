# Asylum of the Immortals Loot Tracker

This program is designed to be used alongside the master looter when raiding. By tracking plusses, when an item is rolled for, it aims to eliminate (or, at least, vastly reduce) confusion by eliminating the necessity for the master looter to manually track this information. 

This program requires installation of [Python](https://www.python.org/downloads/), as well as a virtual environment as well as all packages listed in requirements.txt. To manually install a virtual environment, run the following commands in order through a console such as Command Prompt or PowerShell:

1. `python -m venv .venv`
2. `.venv\Scripts\activate` -- assuming you're on Windows, like I am
3. `pip install -r requirements.txt`

This program is designed to be easily run by someone who is not a programmer, by simply running the command `python loot.py`. This program will automatically keep loot history for you, across multiple raids; allowing you to remember who won what several raids back.