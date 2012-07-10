#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

def main():
	
	f = open('database.json','r')
	database = json.loads(f.read())
	f.close()

	stats = {}
	for segment in database:
		label = segment.get('l')
		(start, end) = segment.get('s')
		duration = end - start
		if stats.get(label):
			stats[label] += duration
		else:
			stats[label] = duration

	print stats


						

if __name__ == '__main__':
	main()