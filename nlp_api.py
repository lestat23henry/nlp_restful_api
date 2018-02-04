#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, url_for,request,jsonify,make_response
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import RotatingFileHandler

import nlp_impl

app = Flask(__name__)
nlp_impl.init_process()
nlp_impl.init_update()

''' setup time rotate logging for web api service'''
formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')

log_file_handler = TimedRotatingFileHandler(filename="nlp_api.log",when='W0',interval=5,backupCount=2)
log_file_handler.setFormatter(formatter)  # 可以通过setFormatter指定输出格式
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
logger.addHandler(log_file_handler)

'''statistics on nlp processing'''
success_count = 0
fail_count = 0
exception_count = 0

@app.route('/')
def api_root():
	info = {}
	info['description'] = 'nlp restful api'
	info['input'] = 'json object contains news content or title'
	info['output'] = 'top keywords about input news and sentiment score of the news'
	return jsonify(info)

@app.route('/stats')
def api_statistics():
	info = {}
	info['success_count'] = success_count
	info['fail_count'] = fail_count
	info['exception_count'] = exception_count
	return jsonify(info)


def log_error(remote_ip,error):
	return logger.error("remote ip %s revoke error : %s " % (remote_ip,error))

@app.errorhandler(500)
def internal_error(remote_ip,error):
	log_error(remote_ip,error)
	return make_response(jsonify({'error': error}), 500)

@app.errorhandler(415)
def not_found(remote_ip,error):
	log_error(remote_ip,error)
	return make_response(jsonify({'error': error}), 415)

@app.errorhandler(400)
def bad_request(remote_ip,error):
	log_error(remote_ip,error)
	return make_response(jsonify({'error': error}), 400)


@app.route('/nlp_update', methods=['POST'])
def api_nlp_update():
	remote_ip = request.remote_addr
	try:
		logger.debug('remote %s revoke nlp update with %r' % (remote_ip,request))
		if request.headers['Content-Type'] == 'application/json':
			if 'update_end' not in request.json and 'update_start' not in request.json:
				return bad_request(remote_ip,'Invalid Json Parameters')

			update_start = request.json['update_start']
			update_end = request.json['update_end']

			update_res,reason = nlp_impl.update_on_demand(update_start,update_end)
			if update_res:
				logger.debug('nlp update success')
			else:
				logger.error('nlp update failed with reason %s' % reason)
				
			resp_json = { 'update_res': update_res }

			return jsonify(resp_json)

	except Exception,e:
		logger.error('Exception in nlp_update : %s' % e.message)
		return internal_error(remote_ip,'Exception: %s' % e.message)

	return not_found('Unsupported Media Type')


@app.route('/nlp_process',methods=['POST'])
def api_nlp_process():
	global success_count
	global fail_count
	global exception_count

	remote_ip = request.remote_addr
	try:
		logger.debug('remote %s revoke nlp process with %r' % (remote_ip,request))
		if request.headers['Content-Type'] == 'application/json':
			kw_topK = 5
			news_content = None
			news_title = None
			if 'kw_topK' in request.json:
				kw_topK = request.json['kw_topK']

			if 'news_content' in request.json:
				news_content = request.json['news_content']

			if 'news_title' in request.json:
				news_title = request.json['news_title']

			if not news_content and not news_title:
				fail_count += 1
				return bad_request(remote_ip,'Invalid Json Parameters')

			process_res,reason,keywords,sentiment = nlp_impl.process_on_demand(news_content,news_title,kw_topK)
			if process_res:
				success_count += 1
				logger.debug('nlp process success')
			else:
				fail_count += 1
				logger.error('nlp process failed with reason %s' % reason)
				
			resp_json = { 'process_res':process_res, 'reason':reason, 'keywords': keywords,'sentiment':sentiment }
			return jsonify(resp_json)

	except Exception,e:
		exception_count += 1
		logger.error('Exception in nlp_process : %s' % e.message)
		return internal_error(remote_ip,'Exception: %s' % e.message)

	fail_count += 1
	return not_found(remote_ip,'Unsupported Media Type')

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=5555,debug=True)