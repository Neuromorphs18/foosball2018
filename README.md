Repo for storing code related to the foosball table at Telluride 2018.  AKA the best foosball table ever!

## Table API

### Requirements

You must install *pyserial* to communicate with the Foosball table:
```sh
pip install pyserial
```
This package is known to interfere with the package *serial*. Uninstall the latter to avoid issues:
```sh
pip uninstall serial
```

### Importing the API from another directory

To import the API from another directory, use the following code:
```py
import sys
sys.path.insert(0, 'relative/path/to/table_api')
from sensiball import Sensiball
```

### Examples

*table_api/examples* provides several examples showing how to use the python API to communicate with the Foosball table.

### Flashing the Arduinos

- To flash the Arduino Nanos, open `table_api/slave/slave.ino` and edit the lines:
```c
#define SLAVE_ADDRESS 14 // 8/10/12/14 for Goalie/Defender/Midfield/Forward
#define SLAVE_MODE    1  // 0/1 for Translation/Rotation
```

- To flash the Arduino Mega, open `table_api/master/master.ino`. Master can be flashed without editing.
