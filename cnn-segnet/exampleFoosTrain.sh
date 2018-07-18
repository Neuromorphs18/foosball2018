#!/bin/bash

# for training
#python mainFoos.py --log_dir=./ --image_dir=../FoosballData/train.txt --val_dir=../FoosballData/val.txt --batch_size=20

# for finetune from saved ckpt
# python main.py --finetune=/tmp3/first350/TensorFlow/Logs/model.ckpt-1000  --log_dir=/tmp3/first350/TensorFlow/Logs/ --image_dir=/tmp3/first350/SegNet-Tutorial/CamVid/train.txt --val_dir=/tmp3/first350/SegNet-Tutorial/CamVid/val.txt --batch_size=5

#for testing
 python mainFoos.py --testing=./model.ckpt-19999  --log_dir=./res --test_dir=../FoosballData/test.txt --batch_size=5 --save_image=True
