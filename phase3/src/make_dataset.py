#!/usr/bin/python

import os

def main(argv=None):

	# download + convert + segment 

	commands = []
	commands.append('./youtube.py download "%s" "%s" %d' % ('cop15', '', 30))
	commands.append('./youtube.py download "%s" "%s" %d' % ('acta copenhagen', '', 26))
	
	commands.append('./convert.py')
	commands.append('./batch_segmenter.py "./DataSet/Inbox/" loop')

	for command in commands:
		print 'executing: %s' % command
		os.system(command)
	


if __name__ == '__main__': 
	main()