#!/usr/bin/python

import os
import threading
import time
import Queue
import sys
import cv2

help_message = '''
USAGE: batch_segmenter.py <video_source_folder> [cycle-wait]'''

# DEFAULT_PATH = '/Users/spaelling/Downloads/Converted/'

class MyThread(threading.Thread):

	def __init__(self, queue, path):
		threading.Thread.__init__(self)

		self.path = path
		self.queue = queue

	def run(self):

		while True:

            #grabs filename from queue
			filename = self.queue.get()
			# print 'starting segmentation on %s' % filename
        	
			metadata_filename = self.path + filename + '_metadata.txt'
        	# attempt to copy metadata
        	# print 'hej'
        	# print './DataSet/Metadata/%s' % (filename + '_metadata.txt')

        	# if os.path.isfile('./DataSet/Metadata/%s' % (filename + '_metadata.txt')):
        	# 	cmd = 'cp ./DataSet/Metadata/%s %s' % (filename + '_metadata.txt', metadata_filename)
        	# 	print cmd
        	# 	os.system(cmd)

			command = 'python ./vid_segmenter.py "%s%s" &' % (self.path, filename)
			os.system(command)
			# wait for metadata file to be created
			
			while not os.path.isfile(metadata_filename):
				# check every two seconds
				time.sleep(2)

			os.system('mv %s ./DataSet/Metadata/%s' % (metadata_filename, filename + '_metadata.txt'))
			os.system('rm %s%s' % (self.path, filename))

            #signals to queue job is done
			self.queue.task_done()

def main():
	try:
		path = sys.argv[1]
	except:
		print help_message
		return
		# path = DEFAULT_PATH

	try:
		loop = sys.argv[2]
	except:
		loop = False

	while True:
		listing = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['m4v','avi']]
		# for filename in listing:
		# 	print filename

		queue = Queue.Queue()
		#spawn a pool of threads, and pass them queue instance 
		for i in range(min(4, len(listing))):
			# print 'spawning thread #%d' % i
			t = MyThread(queue, path)
			t.setDaemon(True)
			t.start()
	      
		#populate queue with data   
		for filename in listing:
			# only add filename to queue if there is no existing metadata
			if not os.path.isfile('./DataSet/Metadata/%s' % (filename + '_metadata.txt')):
				print 'adding %s to queue' % filename
				queue.put(filename)
			else:
				os.system('rm ./DataSet/Inbox/%s' % (filename))
	   
		#wait on the queue until everything has been processed     
		queue.join()

		if not loop:
			break
		else:
			print 'waiting for data... ctrl+c to break'
			time.sleep(5)
		
if __name__ == '__main__':
    main()