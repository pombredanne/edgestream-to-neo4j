# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Swiss-army classes and functions :)

Requires Python 2.7
"""
#    Copyright (C) 2011 by
#    Sébastien Heymann <sebastien.heymann@lip6.fr>
#    All rights reserved.
#    BSD license.



class CommentedFile:
	def __init__(self, f, commentstring="#"):
		self.f = f
		self.commentstring = commentstring
	def next(self):
		line = self.f.next()
		while line.startswith(self.commentstring) or not line.strip():
			line = self.f.next()
		return line
	def __iter__(self):
		return self



def median(dataList):
	"""Compute median value of a list"""
	dataList.sort()
	l = len(dataList)
	if l % 2 == 1:
		return dataList[l / 2]
	else:
		return dataList[l / 2 - 1]


