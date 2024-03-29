# Asylum of the Immortals Loot Tracker

This program is designed to be used alongside the master looter when raiding. By tracking both regular and soft-reserve plusses, when an item is rolled for, it aims to eliminate (or, at least, vastly reduce) confusion by eliminating the necessity for the master looter to manually track this information. 

This program requires installation of [Python](https://www.python.org/downloads/), as well as a virtual environment as well as all packages listed in requirements.txt. To manually install a virtual environment, run the following commands in order through a console such as Command Prompt or PowerShell:

1. `python -m venv .venv`
2. `.venv\Scripts\activate` -- assuming you're on Windows, like I am
3. `pip install -r requirements.txt`

This program is designed to be easily run by someone who is not a programmer, by simply running the command `python loot.py`. This program will automatically keep loot history for you, across multiple raids; allowing you to remember who won what several raids back, as well as determine if someone has won a reserved N25 version of an item that drops in H25 modes. 

That is, if a 277 version of an item drops, the program will tell you if someone who has soft-reserved it has also won the 264 version of that item.  

The full set of functions is as so: 
1) Award loot
2) Import soft-reserve
3) Mark attendance
4) Export THIS RAID's loot to a file
5) Export the loot history to a file
6) Split up history into paste-sized chunks
7) Remove loot, or weekly reset
8) Export plusses in Gargul style
9) Export plusses to be pasted into chat
10) Enter sudo mode (edit history, enter raiding mode, enter debug mode)