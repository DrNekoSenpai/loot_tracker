# Asylum of the Immortals Loot Tracker

This program is designed to be used alongside the master looter when raiding. By tracking both regular and soft-reserve plusses, when an item is rolled for, it aims to eliminate (or, at least, vastly reduce) confusion by eliminating the necessity for the master looter to manually track this information. 

This program requires installation of Python, as well as a virtual environment as well as all packages listed in `requirements.txt`. To manually install a virtual environment, run the following commands in order through a console such as Command Prompt or PowerShell: 

1. `python -m venv .venv`
2. `.\env\Scripts\activate` -- assuming you're on Windows, like I am
3. `pip install -r requirements.txt`

This program is designed to be easily run by someone who is not a programmer, by simply running the command `python soft-reserve.py`, assuming that you've correctly installed the virtual environment. 

Currently a work in progress. The full set of functions is as so: 
1. Award loot -- complete
2. Manually add a new player -- incomplete
3. Clear ALL plusses -- incomplete
4. Log a trade -- incomplete
5. Export loot to console output -- complete