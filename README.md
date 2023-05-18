# Asylum of the Immortals Loot Tracker

This program is designed to be used alongside the master looter when raiding. By tracking both regular and soft-reserve plusses, when an item is rolled for, it aims to eliminate (or, at least, vastly reduce) confusion by eliminating the necessity for the master looter to manually track this information. 

This program requires installation of Python, as well as a virtual environment as well as all packages listed in `requirements.txt`. The easiest way to do this is by using Visual Studio Code, and using the Command Palette to one-click install a virtual environment as well as the requirements stated. To manually install a virtual environment, run the following commands in order: 

1. `python -m venv .venv`
2. `.\env\Scripts\activate` -- assuming you're on Windows, like I am

This program is designed to be easily run by someone who is not a programmer, by simply running the command `python soft-reserve.py` through a console such as Command Prompt or PowerShell, assuming that you've correctly installed the virtual environment. 

Currently a work in progress. The full set of functions is as so: 
1. Award loot -- complete
2. Manually add a new player -- incomplete
3. Clear ALL plusses -- incomplete
4. Log a trade -- incomplete
5. Export loot to console output -- incomplete