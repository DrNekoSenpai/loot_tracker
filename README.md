# Asylum of the Immortals / Dark Rising Loot Tracker

This program is designed to be used alongside the master looter when raiding. By tracking both regular and soft-reserve plusses, when an item is rolled for, it aims to eliminate (or, at least, vastly reduce) confusion by eliminating the necessity for the master looter to manually track this information. 

This program requires installation of [Python](https://www.python.org/downloads/). 

This program is designed to be easily run by someone who is not a programmer, by simply running the command `python loot.py`. This program will automatically keep loot history for you, across multiple raids; allowing you to remember who won what several raids back, as well as determine if someone has won a reserved N25 or N10 version of an item that drops in H25 or H10 modes. 

That is, if a 277 version of an item drops, the program will tell you if someone who has soft-reserved it has also won the 264 version of that item. 

## You must set the name of the guild when you initiate the program for the first time. This is done by using option 2, to import soft-reserves (if we're raiding with Asylum), or to import TMB (if we're raiding with Dark Rising). 

The full set of functions is as so: 
1) Award loot
2) Import soft-reserve or TMB (or change guild)
3) Add players, manually or from details.txt
4) Print out the history of a given player
5) Export the loot history to a file
6) Export THIS RAID's loot to a file
7) Remove loot, or weekly reset
8) Log a trade

To the best of my knowledge, this program is complete; let me know if you think this needs an additional function, or if it doesn't work as expected. 