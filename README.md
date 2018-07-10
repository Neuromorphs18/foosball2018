Repo for storing code related to the foosball table at Telluride 2018.  AKA the best foosball table ever!

## Flash instructions

To flash the Arduino Nanos, open `table_api/slave/slave.ino` and edit the lines:
```c
const motion_type motion = translation; // one of 'translation', 'rotation'
const position_type position = goalie; // one of 'goalie', 'defender', 'midfield', 'forward'
```

Master can be flashed without editing.


## Table API

`test.py` shows how to use the `sensiball.py` library.
