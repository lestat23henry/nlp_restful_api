#!/usr/bin/env python
# -*- coding: utf-8 -*-


from flask import Flask, url_for,request,jsonify,make_response


app = Flask(__name__)
#nlp_mod = xxx()


@app.route('/')
def api_root():
	return u'Nlp Restful Api Service'


@app.errorhandler(415)
def not_found(error):
    return make_response(jsonify({'error': error}), 415)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': error}), 400)

@app.route('/nlp_process',methods=['POST'])
def api_nlp_process():
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
			return bad_request('Invalid Json Parameters')

		'''
		keywords,sentiment = nlp_mod.xxx(news_content,news_title)
		resp_json = { 'keywords': keywords,'sentiment':sentiment }
		return jsonify(resp_json)
		'''
		return jsonify(request.json)

	return not_found('Unsupported Media Type')

if __name__ == '__main__':
    app.run(debug=True)