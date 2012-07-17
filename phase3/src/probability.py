#!/usr/bin/python
import random

def main(argv=None):

	candidatesProbabilty = [.2,.1,.3,.25,.15]
	intervals = []
	previous = 0
	for c in candidatesProbabilty:
		current = c+previous
		intervals.append(current)
		previous = current

	rnd = random.random()
	previous = 0
	for i in range(len(intervals)):
		if rnd > previous and rnd < intervals[i]:
			break

	print i


if __name__ == '__main__': 
	main()