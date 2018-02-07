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
	userdict_files = [os.path.join(dict_wd,"userdicts/nr_words.txt"),os.path.join(dict_wd,"userdicts/ns_words.txt"),
					  os.path.join(dict_wd,"userdicts/nt_words.txt"),os.path.join(dict_wd,"userdicts/nz_words.txt"),
					  os.path.join(dict_wd,"userdicts/i_words.txt"),os.path.join(dict_wd,"userdicts/c_words.txt"),
					  os.path.join(dict_wd,"userdicts/r_words.txt"),os.path.join(dict_wd,"userdicts/neu_v_words.txt"),
					  os.path.join(dict_wd,"userdicts/stm_n_words.txt"),os.path.join(dict_wd,"userdicts/stm_v_words.txt"),
					  os.path.join(dict_wd,"userdicts/stm_a_words.txt"),os.path.join(dict_wd,"userdicts/not_words.txt"),
					  os.path.join(dict_wd,"userdicts/d_words.txt")]


	ds = split_word.doc_splitter(None,None,stopwordfiles=stopword_files,userdicts=userdict_files,parallel=True)
	#TextRank.set_stopwords('/home/lc/ht_work/nlp_restful_api/stopwords_wz.txt')
	sentiment_analysis.init_resource(stopword_file_list=stopword_files,userdict_file_list=userdict_files)
	logger_impl.debug('init_process_resource end')


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
	global ds
	global logger_impl
	logger_impl.debug('process_keyw_on_demand get request %r' % request_dict)

	keywords = []

	try:
		processed_dict = request_dict
		if 'title' in request_dict:
			processed_dict['TITLE'],err = ds.split_one_string(request_dict['title'])
			if err:
				logger_impl.error('process_keyw_on_demand split_one_string on title return err :%s' % err)

		if 'content' in request_dict:
			text = request_dict['content']
			processed_dict['FIRST_SENTENCE'], processed_dict['MID_SENTENCE'], processed_dict['LAST_SENTENCE'],err = ds.split_content(text)
			if err:
				logger_impl.error('process_keyw_on_demand split_one_string on content return err :%s' % err)

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
	global logger_impl

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









def init_update_resource():
	pass

'''update_res,reason = nlp_impl.update_on_demand(update_start,update_end)'''
def update_on_demand(update_start,update_end):
	pass

