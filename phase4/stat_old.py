#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import numpy as np
import os
import math

std = np.std
var = np.var
mean = np.mean
sqrt = math.sqrt

LoS = """0.005 level of significance: z_a = 3.30\n0.010 level of significance: z_a = 2.33
0.025 level of significance: z_a = 1.96\n0.050 level of significance: z_a = 1.645\n0.100 level of significance: z_a = 1.28"""

def computeZ(x1, x2, delta=0.0):

	# p. 256 

	n1, n2 = float(len(x1)), float(len(x2))
	v1, v2 = var(x1), var(x2)
	Z = ((mean(x1)-mean(x2)) - delta) / sqrt((v1/n1) + (v2/n2))
	return Z

def main():

	# print LoS
	# x1, x2 = [1,1,1,1,1,1,6], [2, 6]
	# # print mean(x1), mean(x2)
	# print 'Z = ', computeZ(x1, x2)

if __name__ == '__main__':
	main()