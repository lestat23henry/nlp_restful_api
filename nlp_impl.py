#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

import split_word
from textrank_withpref import TextRank
from sentiment_analysis_mock import sentiment_analysis

''' global variables '''
logger_impl = None
ds = None

def set_impl_logger(logger):
	global logger_impl
	logger_impl = logger

def init_process_resource():
	global ds
	logger_impl.debug('init_process_resource begin')

	cwd = os.getcwd()

	logger_impl.debug('init_process_resource current workdir %s' % cwd)

	dict_wd = os.path.join(cwd,"extra_lexicon")
	stopword_files = [os.path.join(dict_wd,"stopwords/allstop_words.txt"),os.path.join(dict_wd,"stopwords/nonzhstop_words.txt")]
	userdict_files = []
	'''
	userdict_files = [os.path.join(dict_wd,"userdicts/nr_words.txt"),os.path.join(dict_wd,"userdicts/ns_words.txt"),
					  os.path.join(dict_wd,"userdicts/nt_words.txt"),os.path.join(dict_wd,"userdicts/nz_words.txt"),
					  os.path.join(dict_wd,"userdicts/i_words.txt"),os.path.join(dict_wd,"userdicts/c_words.txt"),
					  os.path.join(dict_wd,"userdicts/r_words.txt"),os.path.join(dict_wd,"userdicts/neu_v_words.txt"),
					  os.path.join(dict_wd,"userdicts/stm_n_words.txt"),os.path.join(dict_wd,"userdicts/stm_v_words.txt"),
					  os.path.join(dict_wd,"userdicts/stm_a_words.txt"),os.path.join(dict_wd,"userdicts/not_words.txt"),
					  os.path.join(dict_wd,"userdicts/d_words.txt")]
					  '''


	ds = split_word.doc_splitter(None,None,stopwordfiles=stopword_files,userdicts=userdict_files,parallel=True)
	#TextRank.set_stopwords('/home/lc/ht_work/nlp_restful_api/stopwords_wz.txt')
	sentiment_analysis.init_resource(stopword_file_list=stopword_files,userdict_file_list=userdict_files)
	logger_impl.debug('init_process_resource end')


def preprocess_common(request_dict):
	'''
	preprocess the original news info, convert to devided word pairs for keywords and sentiment
	:param request_dict:  original infos
	:return: dict contains word pair list
	title :  title word pair list
	content :  content word pair list
	publish_date : date news are published
	catagory :  news catagory
	'''
	ret_dict = {}
	logger_impl.debug('process_keyw_on_demand get request %r' % request_dict)

	if not request_dict:
		logger_impl.error('preprocess_common err :%s','news has no info')
		return (None,'News has no info')

	if 'title' not in request_dict and 'content' not in request_dict:
		logger_impl.error('preprocess_common err :%s','news has no title and content')
		return (None,'News has no content and title')

	if request_dict['title']:
		ret_dict['title'],_ = ds.split_one_string_orig(request_dict['title'])
	else:
		ret_dict['title'] = []


	if request_dict['content']:
		ret_dict['first'],ret_dict['mid'],ret_dict['last'],_ = ds.split_content_orig(request_dict['content'])
	else:
		ret_dict['first'],ret_dict['mid'],ret_dict['last'] = [],[],[]


	ret_dict['publish_date'] = request_dict.get('publish_date',"")
	ret_dict['catagory'] = request_dict.get('catagory',"")

	return ret_dict,None

def process_keyw_on_demand(pre_dict,topK=5):
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
	global ds
	global logger_impl

	keywords = []

	try:
		processed_dict = {}
		if 'title' in pre_dict:
			processed_dict['TITLE'],err = ds.filter_string_wordpair(pre_dict['title'])
			if err:
				logger_impl.error('process_keyw_on_demand split_one_string on title return err :%s' % err)

			processed_dict['FIRST_SENTENCE'],err = ds.filter_string_wordpair(pre_dict['first'])
			if err:
				logger_impl.error('process_keyw_on_demand split_one_string on first return err :%s' % err)
			processed_dict['MID_SENTENCE'],err = ds.filter_string_wordpair(pre_dict['mid'])
			if err:
				logger_impl.error('process_keyw_on_demand split_one_string on mid return err :%s' % err)
			processed_dict['LAST_SENTENCE'],err = ds.filter_string_wordpair(pre_dict['last'])
			if err:
				logger_impl.error('process_keyw_on_demand split_one_string on last return err :%s' % err)

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


def process_sent_on_demand(pre_dict):
	global logger_impl

	try:
		sa = sentiment_analysis()
		sentiment_score,err = sa.analyze(pre_dict)
		if not sentiment_score:
			logger_impl.error('process_on_demand: sentiment_analysis return err: %s' % err)
			return None,err

		return sentiment_score,None

	except Exception,e:
		logger_impl.error('process_on_demand: sentiment_analysis caught exception %s' % e.message)
		return None,e.message









def init_update_resource():
	pass

'''update_res,reason = nlp_impl.update_on_demand(update_start,update_end)'''
def update_on_demand(update_start,update_end):
	pass

