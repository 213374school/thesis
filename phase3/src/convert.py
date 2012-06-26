#!/usr/bin/python

import urllib2
import json
import os
import sys

datasetFactoryPath = './'

def getListOfDownloadedVideoFilenames():

	path = datasetFactoryPath + 'DataSet/Originals/'
	listOfFiles = os.listdir(path)
	listOfFilenames = []
	for aFile in listOfFiles:
		if not aFile == '' and not aFile == 'youtube-dl.py' and not aFile == '.DS_Store' and not aFile[-4:] == 'part':
			listOfFilenames.append(aFile)
	return listOfFilenames

def convertVideoWithFilename(filename):

	ID = filename.split('.')[0]
	convertedFilePath = datasetFactoryPath + 'DataSet/Converted/' + ID + '.m4v'
	if not os.path.isfile(convertedFilePath):
		command = 'ffmpeg -v quiet -n -i DataSet/Originals/' + filename + ' -vcodec mpeg4 -r 24 -s 640x360 -b:v 1600k DataSet/Converted/' + ID + '.m4v'
		os.system(command)
		command = 'cp DataSet/Converted/' + ID + '.m4v DataSet/Inbox/' + ID + '.m4v'
		os.system(command)



def convertAllDownloadedVideos():
	
	filesToConvert = getListOfDownloadedVideoFilenames()

	for thisFile in filesToConvert:
		convertVideoWithFilename(thisFile)


def main(argv=None):

	print 'Converting all videos in ./DataSet/Originals/'
	convertAllDownloadedVideos()


if __name__ == '__main__': 
	main()