import os
import sys
import cv2
import numpy as np
import re

# video_name=sys.argv[1].strip()
# path_annotation=sys.argv[2].strip()
# path_ndg=sys.argv[3].strip()
# path_retine=sys.argv[4].strip()
# nb_img=int(sys.argv[5].strip())

video_name = 'toto.avi'
path = '/home/a007021/Documents/DEEP/foosball_datatset_tobi/'
filename = 'Single_team1'
filename = 'shot4'
filename = 'Both_teams1'
imagePath = path + 'JPEGImages/'
annotPath = path + 'Annotations/'

nb_img = 50000000000
# Borne :
xmax = 240
ymax = 180
validNb = 20000
testNb = 30000

# Load labels
f = open(path + filename + '-targetLocations.txt', 'r')
x = f.readlines()
f.close()

labelArray = np.zeros([len(x) - 15, 3], dtype=np.int16)
for i in range(15, len(x), 1):
    line = x[i]
    s = re.split(r'[ ]+', line)
    labelArray[i - 15, 0] = np.int16(s[0])
    # labelArray[i - 15, 1] = np.int16(s[3])/2
    # labelArray[i - 15, 2] = np.int16(s[4])/2
    labelArray[i - 15, 1] = np.int16(s[3])
    labelArray[i - 15, 2] = np.int16(s[4])

# Create missing directories
if not os.path.exists(imagePath):
	os.makedirs(imagePath)
if not os.path.exists(imagePath + 'train/'):
	os.makedirs(imagePath + 'train/')
if not os.path.exists(imagePath+ 'val/'):
	os.makedirs(imagePath + 'val/')
if not os.path.exists(imagePath + 'test/'):
	os.makedirs(imagePath + 'test/')

if not os.path.exists(annotPath):
	os.makedirs(annotPath)
if not os.path.exists(annotPath + 'train/'):
	os.makedirs(annotPath + 'train/')
if not os.path.exists(annotPath + 'val/'):
	os.makedirs(annotPath + 'val/')
if not os.path.exists(annotPath + 'test/'):
	os.makedirs(annotPath + 'test/')

# Load Images
cap = cv2.VideoCapture(path + filename + '.avi')
cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
cv2.namedWindow('lab', cv2.WINDOW_NORMAL)
cv2.namedWindow('ori', cv2.WINDOW_NORMAL)
imgRet = np.zeros([90, 120], dtype=np.uint8)
imgGray = np.zeros([90, 120], dtype=np.uint8)
imgNet = np.zeros([90, 120, 3], dtype=np.uint8)
posLabel = 0
posFrame = 0
imgLabel = np.zeros([90, 120], dtype=np.uint8)
fWTrain = open(path + 'train.txt', 'w')
fWVal = open(path + 'val.txt', 'w')
fWAno = open(path + 'test.txt', 'w')
while(cap.isOpened()):
    if posFrame >= labelArray[posLabel, 0]:
        while posFrame == labelArray[posLabel, 0]:
            posLabel +=1
        posLabel -= 1
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        imgGray = gray[:,:120]
        imgRet = gray[:, 120:]
        imgNet[:, :, 0] = imgGray
        imgNet[:, :, 1] = imgRet
        x = labelArray[posLabel, 1]
        y = 90 - labelArray[posLabel, 2]
        print(str(posFrame) + " " + str(labelArray[posLabel, 0]) + " " + str(x) + " " + str(y))
        if x > 5 and y > 5:
        # make label image
            imgLabel[:, :] = 0
            imgLabel[y-5:y+5, x-5:x+5] = 1
            if posFrame < validNb:
                filenameImg = imagePath + 'train/' + str(posFrame) + '.png'
                filenameAno = annotPath + 'train/' + str(posFrame) + '.png'
                fWTrain.write(filenameImg + " " + filenameAno + '\n')
            elif posFrame < testNb:
                filenameImg = imagePath + 'val/' + str(posFrame) + '.png'
                filenameAno = annotPath + 'val/' + str(posFrame) + '.png'
                fWVal.write(filenameImg + " " + filenameAno + '\n')
            else:
                filenameImg = imagePath + 'test/' + str(posFrame) + '.png'
                filenameAno = annotPath + 'test/' + str(posFrame) + '.png'
                fWAno.write(filenameImg + " " + filenameAno + '\n')

            cv2.imwrite(filenameImg, imgRet)
            cv2.imwrite(filenameAno, imgLabel)

        cv2.rectangle(imgRet, (x-5, y-5), (x+5, y+5), (255, 0, 0), 2)
        cv2.imshow('frame', gray)
        cv2.imshow('ori', imgRet)
        cv2.imshow('lab', imgLabel*255)
        cv2.waitKey(1)
        posLabel += 1
    posFrame += 1
fWAno.close()
fWVal.close()
fWTrain.close()
cap.release()



