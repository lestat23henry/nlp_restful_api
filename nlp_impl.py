#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

import split_word
from textrank_withpref import TextRank
from sentiment_analysis_mock import sentiment_analysis

''' global variables '''
logger_impl = None
ds = None

def set_impl_logger(logger):
	global logger_impl
	logger_impl = logger

def init_process():
	global ds
	logger_impl.debug('init_process begin')
	ds = split_word.doc_splitter(None,None,'/home/lc/ht_work/nlp_restful_api/stopwords_wz.txt','/home/lc/ht_work/nlp_restful_api/userdict_wz.txt',True)
	#TextRank.set_stopwords('/home/lc/ht_work/nlp_restful_api/stopwords_wz.txt')
	sentiment_analysis.init_resource('/home/lc/ht_work/nlp_restful_api/stopwords_wz.txt','/home/lc/ht_work/nlp_restful_api/userdict_wz.txt')
	logger_impl.debug('init_process end')


def process_keyw_on_demand(request_dict,topK=5):
	'''
	process input news info on demand:
	step1. clean all data
	step2. split news content to first/mid/last
	step3. split all words and pos , form them in word/pos ... string
	step4. get keywords
	:param request_json: news dict
	:param topK:  topK keywords
	:return:  keywords, err
	'''
	logger_impl.debug('process_sent_on_demand get request %r' % request_dict)

	keywords = []

	try:
		processed_dict = request_dict
		if 'title' in request_dict:
			processed_dict['TITLE'] = ds.split_one_string(request_dict['title'])

		if 'content' in request_dict:
			text = request_dict['content']
			processed_dict['FIRST_SENTENCE'], processed_dict['MID_SENTENCE'], processed_dict['LAST_SENTENCE'] = ds.split_content(text)

	except Exception,e:
		logger_impl.error('process_on_demand: split caught exception %s' % e.message)
		return None,e.message

	try:
		tr = TextRank()
		ret,err = tr.calc_wordpairs(processed_dict)
		if not ret:
			logger_impl.error('process_on_demand: textrank calc_wordpairs return err :%s' % err)
			return None,err

		tr.calc_preference()

		keywords,err = tr.textrank(processed_dict,topK=topK)
		if not keywords:
			logger_impl.error('process_on_demand: textrank return err :%s' % err)

		return keywords,err

	except Exception,e:
		logger_impl.error('process_on_demand: textrank caught exception %s' % e.message)
		return keywords,e.message


def process_sent_on_demand(request_dict):
	logger_impl.debug('process_sent_on_demand get request %r' % request_dict)

	try:
		sa = sentiment_analysis()
		sentiment_score,err = sa.analyze(request_dict)
		if not sentiment_score:
			logger_impl.error('process_on_demand: sentiment_analysis return err: %s' % err)
			return None,err

		return sentiment_score,None

	except Exception,e:
		logger_impl.error('process_on_demand: sentiment_analysis caught exception %s' % e.message)
		return None,e.message











def init_update():
	pass

'''update_res,reason = nlp_impl.update_on_demand(update_start,update_end)'''
def update_on_demand(update_start,update_end):
	pass

