Welcome to Alex's Chess AI with No Machine Learning!


The AI currently has the following features:

- alpha-beta pruning
- some asynchronous move calculation

Coming soon are the following:

- hash table for remembering transpositions of move order
- more asynchronous move calculation

The AI is still slightly buggy due to a recent refactoring to make move calculations asynchronous, but fixes are coming soon.

The code that runs the game of chess should be fine. You can play against a friend on it if you want by setting both players as human, or watch the AI play against itself by setting both players as AI.

Moves are made by clicking once on the piece you want to move and then once on the square you want to move to. 
Support for clicking and dragging is coming but has not been implemented yet.
Some moves are illegal, and the engine will not let you make them. This is intended.
All legal moves for any given piece are highlighted when you click on the piece.

A few things are still handled through your Python terminal, so keep an eye out for prompts when promoting pawns and at 
the start of the game. Simply type in things as the program requests. 
Several of your keys on your keyboard will also do things. Controls are listed at the start of each game. 

INSTALLING DEPENDENCIES:

1. `# apt install python3 pip`

2. `# pip install pygame`

Contact me at the email address listed on my profile if you have any questions.

How to run the program:

`$ python Engine.py` 
(A black window should appear if everything has been installed correctly)

Pay attention to your terminal, the program will prompt you for everything else from here!

Controls:

- Z: undo move
- spacebar: flip board to view from the other color's perspective
- L: start/stop music
- M: cycle music track
- V: cycle volume
- P: pause/play music
- C: copy board position to text file
- V: load board position from save


Coming soon:

- Toggle eval bar on/off
- Move timers
- Main menu
- Post-game analysis


