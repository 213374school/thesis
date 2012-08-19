import math
import vid_segmenter as segmenter
smoothTriangle = segmenter.smoothTriangle

def computeFrameStateAnders(magnitudes, contrast, p=0.015):
	
	states = []
	state_values = []
	
	T1 = 1.0 # contrast treshold
	# T2 = 0.015 # displacement vector treshold
	T2 = p
	T = (T1+T2)/2.0 # cumulative treshold

	# weights
	a = T / T1
	b = T / T2

	# print 'a: %2.2f, b: %2.2f' % (a,b)

	for i in range(0,len(magnitudes)):
		state_value = float(sum([a * contrast[i], b * magnitudes[i]]))
		state_values.append(state_value)		
	states = [int(v <= T) for v in state_values]

	return states, state_values

def computeFrameStateAnders2(magnitudes, contrast, p=0.045):
	
	states = []
	state_values = []
	
	T1 = 1.0 # contrast treshold
	T2 = p # displacement vector treshold
	T = (T1+T2)/2.0 # cumulative treshold

	# weights
	a = T / T1
	b = T / T2

	# print 'a: %2.2f, b: %2.2f' % (a,b)

	for i in range(0,len(magnitudes)):
		state_value = sum([a * contrast[i]**3, b * magnitudes[i]**3])**(1.0/3)
		state_values.append(state_value)		
	states = [int(v <= T) for v in state_values]

	return states, state_values

def computeFrameStateSquare(magnitudes, contrast, p=0.4):
	
	states = []
	state_values = []
	
	T = p

	for i in range(0,len(magnitudes)):
		state_value = math.sqrt(contrast[i]**2 + magnitudes[i]**2)
		state_values.append(state_value)		
	states = [int(v <= T) for v in state_values]

	return states, state_values	

def computeFrameStateCubic(magnitudes, contrast, p=0.4):
	
	states = []
	state_values = []
	
	T = p

	for i in range(0,len(magnitudes)):
		state_value = (sum([contrast[i]**3, magnitudes[i]**3]) / 2.0)**(1.0/3.0)
		state_values.append(state_value)		
	states = [int(v <= T) for v in state_values]

	return states, state_values	

# def computeFrameStateX(magnitudes, contrast, x=2.0, T=1.0):
	
# 	states = []
# 	state_values = []

# 	for i in range(0,len(magnitudes)):
# 		state_value = (contrast[i]**x + magnitudes[i]**x)**(1.0/x)
# 		state_values.append(state_value)		
# 	states = [v <= T for v in state_values]

# 	return states, state_values


def computeFrameStateLauge(magnitudes, contrast, p=(0.01, 0.75)):
	
	states = []
	state_values = []
	
	x,y = p
	magnitudes_lim = x
	contrast_lim = y

	for i in range(0,len(magnitudes)):
		state_value = max([contrast[i] * (1 / contrast_lim), magnitudes[i] * (1 / magnitudes_lim)])
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)


	return states, state_values


def computeFrameStateCummulative(magnitudes, contrast, p):

	states = []
	state_values = []
	
	weight,threshold = p

	for i in range(0,len(magnitudes)):
		state_value = (1-weight) * [contrast[i] + weight * magnitudes[i]
		if state_value > threshold:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)


	return states, state_values



def computeFrameStateNaiive(magnitudes, contrast, p=-1):
	
	states = []
	state_values = []
	
	for i in range(0,len(magnitudes)):
		states.append(1)
		state_values.append((contrast[i] + magnitudes[i])/2)

	return states, state_values


def computeFrameStateMagnitudeOnly(magnitudes, contrast, p=0.45):
	
	states = []
	state_values = []

	magnitudes_lim = p
	
	for i in range(0,len(magnitudes)):
		state_value = magnitudes[i] * (1 / magnitudes_lim)
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)
		
	return states, state_values


def computeFrameStateContrastOnly(magnitudes, contrast, p=0.72):
	
	states = []
	state_values = []

	contrast_lim = p
	
	for i in range(0,len(contrast)):
		state_value = contrast[i] * (1 / contrast_lim)
		if state_value > 1.0:
			states.append(0)
		else:
			states.append(1)
		state_values.append(state_value)
		
	return states, state_values

if __name__ == '__main__':
    main() 	