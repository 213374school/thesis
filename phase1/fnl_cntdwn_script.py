#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np

import os

def main():

	# CORE 0
	# os.system('./fnl_cntdwn.py simple 0 0')
	# os.system('./fnl_cntdwn.py simple 12 0')
	# os.system('./fnl_cntdwn.py simple 0 0 > simple_smooth0.txt')
	# os.system('./fnl_cntdwn.py simple 12 0 > simple_smooth12.txt')

	# CORE 1
	# os.system('./fnl_cntdwn.py temporal 0 24')
	# os.system('./fnl_cntdwn.py temporal 0 48')
	# os.system('./fnl_cntdwn.py temporal 0 24 > better_smooth0_tol24.txt')
	# os.system('./fnl_cntdwn.py temporal 0 48 > better_smooth0_tol48.txt')

	# CORE 2
	# os.system('./fnl_cntdwn.py temporal 12 24')
	# os.system('./fnl_cntdwn.py temporal 0 12')
	# os.system('./fnl_cntdwn.py temporal 12 24 > better_smooth12_tol24.txt')
	# os.system('./fnl_cntdwn.py temporal 0 12 > better_smooth0_tol12.txt')

	# # CORE 3
	# os.system('./fnl_cntdwn.py temporal 12 48')
	# os.system('./fnl_cntdwn.py temporal 12 48 > better_smooth12_tol48.txt')

if __name__ == '__main__':
    main()    	