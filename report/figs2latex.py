#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from matrix2latex_lib import matrix2latex

# def main():

# 	filenames = [filename for filename in os.listdir('./figs') if filename.split('.')[-1] in ['png']]	

# 	# header row
# 	# hr = ['', '$\\nu$', 'p-value', '$\\chi^2$']
# 	hr = ['', '$\\nu$', 'p-value']
# 	# format column
# 	# fc = ['%s', '$%d$', '$%1.4f$', '$%1.4f$']
# 	fc = ['%s', '$%d$', '$%1.4f$']
# 	alignment = 'lcc'

# 	m = []
# 	for filename in filenames:
# 		print filename
# 		m.append([])
# 	caption = 'Friedman rank sum test for recipies'
# 	label = 'tab:fried_recip'
# 	t = matrix2latex(m, 'recipies', headerRow=hr, caption=caption, label=label, formatColumn=fc, alignment=alignment)

# %
# \begin{figure}
#      \centering
#      \includegraphics[width=1\textwidth]{img/triangle_smooth.png}
#      \caption{An example of triangular smoothing being applied to arbitary data for various values of $w$.}
#      \label{fig:triangularsmoothing}
# \end{figure}
# %

def main():

	path = './img/p1figs'
	filenames = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['png'] and '#' not in filename and 'computeFrameStateAnders' not in filename and 'computeFrameStateCubic' not in filename]	

	def get_caption(filename):

		if 'computeFrameStateContrastOnly' in filename:
			caption = 'CO'
		elif 'computeFrameStateCummulative' in filename:
			caption = 'CCSM'
		elif 'computeFrameStateLauge' in filename:
			caption = 'ICSM '
		elif 'computeFrameStateMagnitudeOnly' in filename:
			caption = 'MO'

		if 'sectionCompareBetter' in filename:
			if 'smooth0' in filename:
				if 'tol12' in filename:
					caption += '7'
				if 'tol24' in filename:
					caption += '3'
				if 'tol48' in filename:
					caption += '4'					
			elif 'smooth12' in filename:
				if 'tol24' in filename:
					caption += '5'
				if 'tol48' in filename:
					caption += '6'	

		elif 'simpleCompare' in filename:
			if 'smooth0' in filename:
				caption += '1'
			elif 'smooth12' in filename:
				caption += '2'
		if 'AUC' in filename:
			caption += ' (AUC)'
		return caption

	sortme = [(get_caption(f),f) for f in filenames]
	sortme = sorted(sortme)
	filenames = [f for c,f in sortme]

	subfigs_per_fig = 4
	subfigs_per_row = 2

	out = '%\n'
	for i, filename in enumerate(filenames):
		# if i > 0 and i % 6 == 0:
		# 	out += '\FloatBarrier\n'

		print filename
		caption = get_caption(filename)
		print caption

		if i > 0 and i % subfigs_per_fig == 0:
			out += '\\end{figure}\n'
			out += '%\n'		
		if i % subfigs_per_fig == 0:
			out += '\\begin{figure}[!ht]\n'
			out += '\t\\centering\n'
		
		out += '\t\\subfigure[%s]{\n' % caption
		# out += '\t\t\\label{fig:%s}\n' % filename
		out += '\t\t\\includegraphics[width=0.45\\textwidth]{img/p1figs/%s}\n' % filename
		# out += '\t\t\\caption{%s}\n' % caption
		out += '\t}'
		if i > 0 and (i+1) % subfigs_per_row == 0:
			out += '\\\\'
		out += '\n'

	out += '\\end{figure}\n'
	out += '%\n'		

	# print out

	f = open('p1figs.tex','w')	
	f.write(out)
	f.close()	

	print 'graphs out: %d' % len(filenames)

if __name__ == '__main__':
    main()    	