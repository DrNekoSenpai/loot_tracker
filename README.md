# Asylum of the Immortals Loot Tracker

This program is designed to be used alongside the master looter when raiding. By tracking both regular and soft-reserve plusses, when an item is rolled for, it aims to eliminate (or, at least, vastly reduce) confusion by eliminating the necessity for the master looter to manually track this information. 

This program requires installation of [Python](https://www.python.org/downloads/), as well as a virtual environment as well as all packages listed in `requirements.txt`. To manually install a virtual environment, run the following commands in order through a console such as Command Prompt or PowerShell: 

1. `python -m venv .venv`
2. `.venv\Scripts\activate` -- assuming you're on Windows, like I am
3. `pip install -r requirements.txt`

This program is designed to be easily run by someone who is not a programmer, by simply running the command `python soft-reserve.py`, assuming that you've correctly installed the virtual environment. 

The full set of functions is as so: 
1. Award loot
2. Manually add a new player
3. Clear ALL plusses
4. Log a trade
5. Export loot to console output

To the best of my knowledge, this program is complete; let me know if you think this needs an additional function, or if it doesn't work as expected. 