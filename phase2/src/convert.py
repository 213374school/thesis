#!/usr/bin/python

import urllib2
import json
import os
import sys

datasetFactoryPath = './'

def getListOfDownloadedVideoFilenames():

	path = datasetFactoryPath + '../processed/'
	listOfFiles = os.listdir(path)
	listOfFilenames = []
	for aFile in listOfFiles:
		if not aFile == '' and not aFile == 'youtube-dl.py' and not aFile == '.DS_Store':
			listOfFilenames.append(aFile)
	return listOfFilenames

def convertVideoWithFilename(filename):

	ID = filename.split('.')[0]
	convertedFilePath = datasetFactoryPath + '../converted/' + ID + '.m4v'
	if not os.path.isfile(convertedFilePath):
		command = 'ffmpeg -v quiet -n -i ../processed/' + filename + ' -vcodec mpeg4 -r 24 -s 640x360 -b:v 1600k ../converted/' + ID + '.m4v'
		os.system(command)
		#command = 'mv ../processed/' + ID + '.m4v ../converted/' + ID + '.m4v'
		#os.system(command)



def convertAllDownloadedVideos():
	
	filesToConvert = getListOfDownloadedVideoFilenames()

	for thisFile in filesToConvert:
		convertVideoWithFilename(thisFile)


def main(argv=None):

	print 'Converting all videos in ../processed/'
	convertAllDownloadedVideos()


if __name__ == '__main__': 
	main()