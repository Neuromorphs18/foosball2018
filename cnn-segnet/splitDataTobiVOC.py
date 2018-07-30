import os
import sys
import cv2
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from xml.dom import minidom
from lxml import etree
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
annotPath = path + 'Annotations_VOC/'

nb_img = 50000000000
# Borne :
xmax = 240
ymax = 180


# Writer xml :
class PascalVocWriter:
    def __init__(self, foldername, filename, imgSize, databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath

    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

    def genXML(self):
        """
            Return XML root
        """

        top = Element('annotation')
        folder = SubElement(top, 'folder')
        folder.text = self.foldername

        filename = SubElement(top, 'filename')
        filename.text = self.filename

        localImgPath = SubElement(top, 'path')
        localImgPath.text = self.localImgPath

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.databaseSrc

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])
        if len(self.imgSize) == 3:
            depth.text = str(self.imgSize[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'

        return top

    def addBndBox(self, xmin, ymin, xmax, ymax, name):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        bndbox['name'] = name
        self.boxlist.append(bndbox);

    def appendObjects(self, top):
        for each_object in self.boxlist:
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            name.text = str(each_object['name'])
            pose = SubElement(object_item, 'pose')
            pose.text = "Unspecified"
            truncated = SubElement(object_item, 'truncated')
            truncated.text = "0"
            difficult = SubElement(object_item, 'difficult')
            difficult.text = "0"
            bndbox = SubElement(object_item, 'bndbox')
            xmin = SubElement(bndbox, 'xmin')
            xmin.text = str(each_object['xmin'])
            ymin = SubElement(bndbox, 'ymin')
            ymin.text = str(each_object['ymin'])
            xmax = SubElement(bndbox, 'xmax')
            xmax.text = str(each_object['xmax'])
            ymax = SubElement(bndbox, 'ymax')
            ymax.text = str(each_object['ymax'])

    def save(self, targetFile=None):
        root = self.genXML()
        self.appendObjects(root)
        out_file = None
        if targetFile is None:
            out_file = open(self.filename + '.xml', 'w')
        else:
            out_file = open(targetFile, 'w')

        tree = ET.ElementTree(root)
        out_file.write(self.prettify(root))
        out_file.close()

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

# Borne :
xmax = 240
ymax = 180
validNb = 20000
testNb = 30000

# Load Images
cap = cv2.VideoCapture(path + filename + '.avi')
cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
cv2.namedWindow('lab', cv2.WINDOW_NORMAL)
imgRet = np.zeros([90, 120], dtype=np.uint8)
imgGray = np.zeros([90, 120], dtype=np.uint8)
imgNet = np.zeros([90, 120,3], dtype=np.uint8)
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
        # make label
        if x > 5 and y > 5:
        # make label image
            imgLabel[:, :] = 0
            if posFrame < validNb:
                filenameImg = imagePath + 'train/' + str(posFrame) + '.png'
                filenameAno = annotPath + 'train/'
                fWTrain.write(filenameImg + " " + filenameAno + '\n')
            elif posFrame < testNb:
                filenameImg = imagePath + 'val/' + str(posFrame) + '.png'
                filenameAno = annotPath + 'val/'
                fWVal.write(filenameImg + " " + filenameAno + '\n')
            else:
                filenameImg = imagePath + 'test/' + str(posFrame) + '.png'
                filenameAno = annotPath + 'test/'
                fWAno.write(filenameImg + " " + filenameAno + '\n')

            cv2.imwrite(filenameImg, imgRet)
            tmp = PascalVocWriter(annotPath, str(posFrame), (xmax, ymax, 3))
            tmp.addBndBox(x - 5, y-5, x+5, y+5, 'dog')
            tmp.save(os.path.join(tmp.foldername, tmp.filename + '.xml'))
        cv2.rectangle(imgRet, (x-5, y-5), (x+5, y+5), (255, 0, 0), 2)
        cv2.imshow('frame', gray)
        cv2.imshow('lab', imgRet)
        cv2.waitKey(1)
        posLabel += 1
    posFrame += 1
fWAno.close()
fWVal.close()
fWTrain.close()
cap.release()



