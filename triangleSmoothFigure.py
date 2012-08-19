#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pylab

def triangleSmooth(lst=[], degree=1):

	if degree < 1:
		print 'degree must be > 1'
		return

	triangle = np.array(range(degree)+[degree]+range(degree)[::-1])+1
	lst = np.array(lst)
	lst_lenght = len(lst)
	tri_len = len(triangle)
	_max = lst_lenght - degree
	triangle_normal_sum = float(sum(triangle))
	
	smoothed_lst = []
	for i in range(lst_lenght):

		if i > degree and i < _max:
			new_value = sum(triangle * lst[i-degree:i+degree+1]) / triangle_normal_sum
		else:
			left = degree - min(i, degree)
			right = degree + min(degree, lst_lenght - 1 - i) + 1			
			tri = triangle[left:right]
			triangle_sum = sum(tri)

			new_value = 0.0
			for j in range(len(tri)):

				pos = j + i + left - degree
				new_value += tri[j] * lst[pos]
		
			new_value /= triangle_sum

		smoothed_lst.append(new_value)

	return smoothed_lst


def loadPhase1MetaData(ytid):

	return (loadFinalMetadata(ytid)).get('phase1')

	filepath = os.path.dirname(os.path.realpath(__file__)) + '/phase1/DataSet/Metadata/' + ytid + '_metadata.txt'
	if os.path.isfile(filepath):
		f = open(filepath, 'r+')
		return json.loads(f.read())
	else:
		print 'Metadata file: \'%d\', doesnt exist.' % filepath
		return



def main():
	
	
	pylab.subplot2grid((10,1), (4,0), rowspan=2)
	pylab.bar(range(len(volume)),volume)

if __name__ == '__main__':
	main()