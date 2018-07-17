{\rtf1\ansi\ansicpg1252\cocoartf1348\cocoasubrtf170
{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;}
\paperw11900\paperh16840\margl1440\margr1440\vieww10800\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural

\f0\fs24 \cf0 # Environment\
\
Yellow = motorised, Blue = human.\
\
## State\
\
use get_state() to return ball x position, ball y position and y offset of rods \
\
use get_full_state() to get ball position, velocity and position and velocity (rotational and sliding) of all rods (human and computer)\
\
## Actions\
\
use step() with categorical=True to pass 0,1,2,3 = do nothing, move left, move right, kick for each yellow team rod from goalie \'97> strikers e.g. Goalie: nothing, defenders left, midfielders right, strikers nothing = \
\
\pard\pardeftab720

\f1 \cf2 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 ```\
step([0,1,2,0], categorical=True) \
```
\f0 \cf0 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 \
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural
\cf0 \
use step() with categorical=False to pass rotation and slide velocities to the yellow team \
\
## Reward\
\
reward returned by step() is +1 if yellow team just scored, -1 if blue team just scored and 0 otherwise. Score is also returned by step function if you want to make a different reward structure}