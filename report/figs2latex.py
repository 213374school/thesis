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
	filenames = [filename for filename in os.listdir(path) if filename.split('.')[-1] in ['png'] and '#' not in filename]	

	out = '%\n'
	for filename in filenames:
		print filename
		# filename = filename.replace('#','\#')
		caption = 'caption'
		# out += '%\n'
		out += '\\begin{figure}[!ht]\n'
		out += '\t\\centering\n'
		out += '\t\\includegraphics[width=0.5\\textwidth]{img/p1figs/%s}\n' % filename
		out += '\t\\caption{%s}\n' % caption
		# out += '\t\\label{fig:%s}\n' % filename
		out += '\\end{figure}\n'
		out += '%\n'
	print out

	f = open('p1figs.tex','w')	
	f.write(out)
	f.close()	

	print 'graphs out: %d' % len(filenames)

if __name__ == '__main__':
    main()    	