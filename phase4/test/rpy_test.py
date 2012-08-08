import numpy as np
from rpy import *
import random
import json

friedman = r.friedman_test

# y = range(24)
# random.shuffle(y)
# y[random.randint(0,len(y))] = None
# y[random.randint(0,len(y))] = None
# y[random.randint(0,len(y))] = None

y1 = [1,2,5,3,2,1,1,3,2,1]
y2 = [4,3,6,5,2,6,1,6,5,4]
y3 = [9,6,7,7,5,1,8,9,6,5]

def to_matrix(ys):

	# compute length of each pseudo-row
	lens = [len(y) for y in ys]
	# print lens
	# get the longest
	max_len = max(lens)

	for i, y in enumerate(ys):
		ys[i] += [None] * (max_len - len(y))

	nys = []
	for y in ys:
		nys += y
	return r.matrix(nys, nrow=max_len)

y = to_matrix([y1, y2, y3])
print y
f = friedman(y=y)

# print json.dumps(f, sort_keys=True, indent=4)

# DoF
df = f.get('parameter').get('df')
# p-value
p = f.get('p.value')
method = f.get('method')
statistic = f.get('statistic')

print method
print 'degrees of freedom: ', df
print 'p-value: ', p
k = statistic.keys()[0]
print '%s: %2.2f' % (k, statistic.get(k))

print 'Friedman chi-squared = 15.6216, df = 2, p-value = 0.0004053'
