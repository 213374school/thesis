#!/usr/bin/python

import urllib2
import json
import os
import sys
import time
import Queue
import threading
import string
import numpy as np


def loadAllAnswers():
	f = open('data_dump.json','r')
	video_answers = json.loads(f.read())
	f.close()
	return video_answers



def ytid2filename(ytid):
	yt2file = {'2C7Y5Shw5p8': 'd370ccc56c', '48QPI1wz1QY': 'bf7dc9f5ca', '5swFsRKsI7I': '2806c14722', '75IHEvP7An4': '9891596ecf', '7sao2_7sKms': '2f7a25e921', '8sk2HWj4zhU': '3b95a67d38', 'BbS0GQLp4CQ': 'a8d1de1e81', 'E1v6_GvB3j4': '913eef2ed2', 'G9YeDzzwyVQ': '143a413f62', 'HlOIeCzXSCI': '77baa022f1', 'MLzAuBHSiTU': '57d23634ac', 'Mu7JJEHonGE': 'c23777fd98', 'XYHr6gZqkTs': '48b62f11dc', 'ZFSYWB1BcxE': '3f79a5f7f1', 'a7k7gemEwsE': '80a451d4c2', 'ho1CjPB02F8': '90fe6adcd2', 'hrxbQNTBqNQ': 'dd7d1998f8', 'j_pkzYcJ8j0': '625838c2b1', 'pBw6UJa6-_w': '7babfd31c4', 'rEFkglQCcXg': '14e177dd42', 'yrfnIujswX8': '98b1d02056'}
	return yt2file.get(ytid)

def filename2ytid(filename):
	file2yt = {'d370ccc56c': '2C7Y5Shw5p8', 'bf7dc9f5ca': '48QPI1wz1QY', '2806c14722': '5swFsRKsI7I', '9891596ecf': '75IHEvP7An4', '2f7a25e921': '7sao2_7sKms', '3b95a67d38': '8sk2HWj4zhU', 'a8d1de1e81': 'BbS0GQLp4CQ', '913eef2ed2': 'E1v6_GvB3j4', '143a413f62': 'G9YeDzzwyVQ', '77baa022f1': 'HlOIeCzXSCI', '57d23634ac': 'MLzAuBHSiTU', 'c23777fd98': 'Mu7JJEHonGE', '48b62f11dc': 'XYHr6gZqkTs', '3f79a5f7f1': 'ZFSYWB1BcxE', '80a451d4c2': 'a7k7gemEwsE', '90fe6adcd2': 'ho1CjPB02F8', 'dd7d1998f8': 'hrxbQNTBqNQ', '625838c2b1': 'j_pkzYcJ8j0', '7babfd31c4': 'pBw6UJa6-_w', '14e177dd42': 'rEFkglQCcXg', '98b1d02056': 'yrfnIujswX8'}
	return file2yt.get(filename)

def filenames2ytid(filenames):
	new = []
	for f in filenames:
		new.append(filename2ytid(f))
	return new



def showScoresForAnswers(video_answers):

	content = []
	editing = []
	clip_len = []
	video_len = []

	for va in video_answers:
		answers = va.get('answers')
		for answer in answers:
			if answer.get('question_title') == 'content':
				content.append(answer.get('answer_value'))
			if answer.get('question_title') == 'editing':
				editing.append(answer.get('answer_value'))
			if answer.get('question_title') == 'clip len':
				clip_len.append(answer.get('answer_value'))
			if answer.get('question_title') == 'video len':
				video_len.append(answer.get('answer_value'))

	print 'Content:      %.2f (std: %.2f)' % (np.mean(content), np.std(content))
	print 'Editing:      %.2f (std: %.2f)' % (np.mean(editing), np.std(editing))
	print 'Clip Length:  %.2f (std: %.2f)' % (np.mean(clip_len), np.std(clip_len))
	print 'Video Length: %.2f (std: %.2f)' % (np.mean(video_len), np.std(video_len))

def showNotesForAnswers(video_answers):

	for va in video_answers:
		note = va.get('note')
		session = va.get('session_key')
		ytid = va.get('ytid')
		filename = ytid2filename(ytid)
		
		if note and note != '':
			print 'f: %s, s: %s :: %s' % (filename, session, note)



def trimAnswersToLocale(video_answers, locale):

	new = []
	for va in video_answers:
		if va.get('locale') == locale:
			new.append(va)
	return new

def trimAnswersToYTIDs(video_answers, ytids):

	new = []
	for va in video_answers:
		if va.get('ytid') in ytids:
			new.append(va)
	return new

def trimAnswersToSessionIDs(video_answers, ses_ids):

	new = []
	for va in video_answers:
		if va.get('session_key') in ses_ids:
			new.append(va)
	return new

def trimAnswersToThoseWithNotes(video_answers):

	new = []
	for va in video_answers:
		if va.get('note') and va.get('note') != '':
			new.append(va)
	return new



def main(argv=None):

	# Get answer data
	video_answers = loadAllAnswers()

	#video_answers = trimAnswersToLocale(video_answers, 'en')
	#video_answers = trimAnswersToYTIDs(video_answers, ['hrxbQNTBqNQ'])
	#video_answers = trimAnswersToSessionIDs(video_answers, ['6e06ae2034b228eL'])
	#video_answers = trimAnswersToThoseWithNotes(video_answers)

	print 'NUMBER OF VIDEO-WATCHES: %d' % len(video_answers)

	#showNotesForAnswers(video_answers)
	showScoresForAnswers(video_answers)

if __name__ == '__main__': 
	main()