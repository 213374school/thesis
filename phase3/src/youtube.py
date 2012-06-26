#!/usr/bin/python

import urllib2
import json
import os
import sys
import time
import Queue
import threading
import string

help_message = '''
SEARCH:            youtube.py search [<tags>] [<categories>] [maxResult>]
DOWNLOAD:          youtube.py download [<tags>] [<categories>] [maxResult>]
DELETE VIDEOS:     youtube.py delete [<tags>] [<categories>]
ADVANCED SEARCH:   youtube.py asearch [<query>] [<requiredWordsInTitle>] [<tags>] [<categories>] [maxResult>]
ADVANCED DOWNLOAD: youtube.py adownload [<query>] [<requiredWordsInTitle>] [<tags>] [<categories>] [maxResult>]
ADVANCED DELETE:   youtube.py adownload [<query>] [<requiredWordsInTitle>] [<tags>] [<categories>]
BOOK KEEPING:      youtube.py book
'''

datasetFactoryPath = './'

class MyThread(threading.Thread):

	def __init__(self, queue):
		threading.Thread.__init__(self)

		self.queue = queue

	def run(self):

		while True:

			video = self.queue.get()
			
			# Start downloading the video
			fetchVideo(video)

			stillDownloading = True
			while stillDownloading:

				downloadedVideos = getListOfDownloadedVideos()
				stillDownloading = False
				for thisVideo in downloadedVideos:
					elements = thisVideo.split('.')
					if len(elements) == 3 and elements[0] == video.get('id') and elements[2] == 'part':
						stillDownloading = True
						time.sleep(10)
						break

            #signals to queue job is done
			self.queue.task_done()

def searchForVideos(_query, requiredInTitle, tags, categories, maxResults):

	# Set additional parameters
	apiVersion = '2'
	startIndex = '1'
	maxNumberOfResults = str(maxResults)
	orderBy = 'relevance'
	safeSearch = 'none'
	alt = 'json'

	if _query:
		query = '?q=' + _query.replace(' ', '+') + '&'
	else:
		query = '?'

	# Format tags string
	tagsStr = ''
	for tag in tags:
		tagsStr += tag + '%2C'

	# Format categories string
	categoriesStr = ''
	for category in categories:
		categoriesStr += category + '%7C'
	categoriesStr = categoriesStr[0:-3]
		


	# Do search on youtube
	searchURL = 'https://gdata.youtube.com/feeds/api/videos' + query + 'v=' + apiVersion + '&start-index=' + startIndex + '&max-results=' + maxNumberOfResults + '&orderby=' + orderBy + '&safeSearch=' + safeSearch + '&category=' + tagsStr + categoriesStr + '&alt=' + alt

	print searchURL

	response = urllib2.urlopen(searchURL)
	resultString = response.read()
	result = json.loads(resultString)


	# Process the result
	feed = result.get('feed')
	entries = feed.get('entry')
	videos = []
	for entry in entries:

		mediaGroup = entry.get('media$group')
		uploadedTime = mediaGroup.get('yt$uploaded').get('$t')
		title = mediaGroup.get('media$title').get('$t')
		length = int(mediaGroup.get('yt$duration').get('seconds'))
		videoID = mediaGroup.get('yt$videoid').get('$t')
		keywords = mediaGroup.get('media$keywords').get('$t')
		category = mediaGroup.get('media$category')[0].get('$t')

		video = {'id':videoID, 'title': title, 'length':length, 'uploaded': uploadedTime, 'category': category, 'keywords':keywords}

		if requiredInTitle and len(requiredInTitle) > 0:
			allExists = True
			for word in requiredInTitle:
				if string.find(title, word) == -1:
					allExists = False
					break
			if allExists:
				videos.append(video)
		else:
			videos.append(video)

	return videos



def getListOfDownloadedVideos():

	path = datasetFactoryPath + 'DataSet/Originals/'
	listOfFiles = os.listdir(path)
	listOfIDs = []
	for aFile in listOfFiles:
		ID = aFile.split('.')[0]
		if not ID == '' and not ID == 'youtube-dl': 
			listOfIDs.append(ID)
	return listOfIDs


def getListOfConvertedVideos():

	path = datasetFactoryPath + 'DataSet/Converted/'
	listOfFiles = os.listdir(path)
	listOfIDs = []
	for aFile in listOfFiles:
		ID = aFile.split('.')[0]
		if not ID == '':
			listOfIDs.append(ID)
	return listOfIDs


def getVideosInListThatNeedsToBeDownloaded(listOfVideos):

	downloaded = getListOfDownloadedVideos()
	missing = [x for x in listOfVideos if x not in downloaded]
	return missing


def getVideosInListThatNeedsToBeConverted(listOfVideos):

	converted = getListOfConvertedVideos()
	missing = [x for x in listOfVideos if x not in converted]
	return missing


def fetchVideo(video):

	ID = video.get('id')

	# Ignore ID's beginning with '-' since the download script can't handle them
	if not ID[0] == '-':

		# Attempt to download in mp4 format
		if not ID in getListOfDownloadedVideos():
			command = 'cd ' + datasetFactoryPath + 'DataSet/Originals/;python ./youtube-dl.py -f 22 "' + ID + '" &'
			os.system(command)
			time.sleep(10)

		# If file wasn't downloaded, get any version there is
		if not ID in getListOfDownloadedVideos():
			command = 'cd ' + datasetFactoryPath + 'DataSet/Originals/;python ./youtube-dl.py "' + ID + '" &'
			os.system(command)
	


def createKeyFromTagsAndCategories(tags, categories):

	key = ''
	if len(tags) > 0:
		key += 'TAGS'
		for tag in tags:
			key += ':' + tag
	if len(categories) > 0:
		key += '&&CATEGORIES'
		for category in categories:
			key += ':' + category

	return key


def loadBookKeepingFromDisk():
	
	# Does the book keeping file exist?
	bookKeepingFilePath = datasetFactoryPath + 'bookkeeping.json'
	if os.path.isfile(bookKeepingFilePath):
		
		# Load the files JSON content into an object
		f = open(bookKeepingFilePath, 'r')
		content = f.read()
		bookKeeping = json.loads(content)
		f.close()
		
		return bookKeeping
	else:

		# File doesn't exist return empty dictionary
		return {}


def saveBookKeepingToDisk(bookKeeping):

	bookKeepingFilePath = datasetFactoryPath + 'bookkeeping.json'

	# Only write if the JSON parse was succesful
	content = json.dumps(bookKeeping)
	if content:
		
		f = open(bookKeepingFilePath, 'w')
		f.write(content)
		f.close()


def bookKeepVideos(videos, tags, categories):

	# Load book keeping file if it exists
	bookKeeping = loadBookKeepingFromDisk()

	# Create key from tags and categories
	key = createKeyFromTagsAndCategories(tags, categories)

	# Acquire the videolist to keep these videos in
	videolist = []
	if bookKeeping.get(key):
		videolist = bookKeeping.get(key)

	# Add videos to dataset
	for video in videos:

		ID = video.get('id')
		if not ID in videolist:
			videolist.append(ID)

	# Store the new video list in the book keeping file
	bookKeeping[key] = videolist
	saveBookKeepingToDisk(bookKeeping)


def removeSearchFromBookKeeping(tags, categories):

	# Load book keeping file if it exists
	bookKeeping = loadBookKeepingFromDisk()

	# Create key from tags and categories
	key = createKeyFromTagsAndCategories(tags, categories)

	# Delete the search from the book keeping file
	del bookKeeping[key]
	saveBookKeepingToDisk(bookKeeping)


def getVideosForSearch(tags, categories):

	# Load book keeping file if it exists
	bookKeeping = loadBookKeepingFromDisk()

	# Create key from tags and categories
	key = createKeyFromTagsAndCategories(tags, categories)

	return bookKeeping.get(key)


def deleteVideos(videos):

	filesToDelete = []

	# Get video IDs
	IDs = []
	for video in videos:
		IDs.append(video.get('id'))

	# Get list of all Original videos to delete
	path = datasetFactoryPath + 'DataSet/Originals/'
	listOfFiles = os.listdir(path)
	for aFile in listOfFiles:
		ID = aFile.split('.')[0]
		if not ID == '' and not ID == 'youtube-dl' and ID in IDs: 
			filesToDelete.append(path + aFile)

	# Get list of all Converted videos to delete
	path = datasetFactoryPath + 'DataSet/Converted/'
	listOfFiles = os.listdir(path)
	for aFile in listOfFiles:
		ID = aFile.split('.')[0]
		if not ID == '' and ID in IDs: 
			filesToDelete.append(path + aFile)

	# Delete the files
	for thisFile in filesToDelete:
		os.remove(thisFile)


def main(argv=None):

	bookKeep = True
	maxResults = 20
	
	if True:
		command = sys.argv[1]

		if command == 'search' or command == 'download' or command == 'delete' or command == 'asearch' or command == 'adownload' or command == 'adelete':

			videos = []
			if command == 'search' or command == 'download' or command == 'delete':

				tags = sys.argv[2].split(' ')
				categories = sys.argv[3].split(' ')

				if len(sys.argv) == 5:
					maxResults = int(sys.argv[4])
				else:
					if not command == 'delete':
						print 'Defaulting to maxResult = ' + str(maxResults)

				# Search for videos
				videos = searchForVideos(None, None, tags, categories, maxResults)
			
			if command == 'asearch' or command == 'adownload' or command == 'adelete':

				query = sys.argv[2]
				requiredInTitle = sys.argv[3].split(' ')
				tags = sys.argv[4].split(' ')
				categories = sys.argv[5].split(' ')

				if len(sys.argv) == 7:
					maxResults = int(sys.argv[6])
				else:
					if not command == 'adelete':
						print 'Defaulting to maxResult = ' + str(maxResults)

				# Search for videos
				videos = searchForVideos(query, requiredInTitle, tags, categories, maxResults)


			# Bookkeep videos under these tags and categories
			if bookKeep:
				bookKeepVideos(videos, tags, categories)

			if command == 'search' or command == 'asearch':
				# Print a dump of the videos
				print json.dumps(videos, sort_keys=True, indent=4) + '\nListed ' + str(len(videos)) +' results\n'

			if command == 'download' or command == 'adownload':
				# Download the videos
				print 'Attempting to download ' + str(len(videos)) + ' videos:\n'

				queue = Queue.Queue()
				#spawn a pool of threads, and pass them queue instance 
				for i in range(min(4, len(videos))):
					# print 'spawning thread #%d' % i
					t = MyThread(queue)
					t.setDaemon(True)
					t.start()
			      
				#populate queue with data   
				for video in videos:
					queue.put(video)
			   
				#wait on the queue until everything has been processed     
				queue.join()

			if command == 'delete' or command == 'adelete':

				# Delete all these videos
				deleteVideos(videos)

				# Clean up book keeping file
				removeSearchFromBookKeeping(tags, categories)


		elif command == 'book':

			book = loadBookKeepingFromDisk()
			print str(len(book)) + ' sets:'
			for key in book.keys():

				videos = book.get(key)
				missingDownload = getVideosInListThatNeedsToBeDownloaded(videos)
				missingConverted = getVideosInListThatNeedsToBeConverted(videos)

				print '\t' + key + ':'
				print '\t\t' + str(len(videos)) + ' videos total'
				print '\t\t' + str(len(missingDownload)) + ' videos needs to be downloaded'
				print '\t\t' + str(len(missingConverted)) + ' videos needs to be converted'

		else:
			print help_message
	else:
		print help_message
	
	return


if __name__ == '__main__': 
	main()