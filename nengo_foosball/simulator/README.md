# Environment

Yellow = motorised, Blue = human.

## State

use get_state() to return ball x position, ball y position and y offset of rods

use get_full_state() to get ball position, velocity and position and velocity (rotational and sliding) of all rods (human and computer)\

## Actions

use step() with categorical=True to pass 0,1,2,3 = do nothing, move left, move right, kick for each yellow team rod from goalie \'97> strikers e.g. Goalie: nothing, defenders left, midfielders right, strikers nothing = 
 ```
step([0,1,2,0], categorical=True) 
 ```
use step() with categorical=False to pass rotation and slide velocities to the yellow team

## Reward

reward returned by step() is +1 if yellow team just scored, -1 if blue team just scored and 0 otherwise. Score is also returned by step function if you want to make a different reward structure}
