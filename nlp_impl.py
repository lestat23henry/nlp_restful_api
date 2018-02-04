#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

''' setup time rotate logging for nlp implement'''
formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')

log_file_handler = TimedRotatingFileHandler(filename="nlp_impl.log",when='W0',interval=5,backupCount=2)
log_file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.addHandler(log_file_handler)


def init_process():
	pass


'''process_res,reason,keywords,sentiment = nlp_impl.process_on_demand(news_content,news_title,kw_topK)'''
def process_on_demand(news_content,news_title,topK=5):
	pass























def init_update():
	pass

'''update_res,reason = nlp_impl.update_on_demand(update_start,update_end)'''
def update_on_demand(update_start,update_end):
	pass

