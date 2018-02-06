#!/usr/bin/env python
# -*- coding: utf-8 -*-
# decription : class TextRank extract keywords

from __future__ import absolute_import, unicode_literals
from collections import defaultdict
import numpy as np
from jieba._compat import *


#------- method 0 ---------------
WEIGHT_LOC_RAND = 1.0
WEIGHT_POS_RAND = 0.0

class UndirectWeightedGraph:
	d = 0.85
	model = None

	def __init__(self):
		self.graph = defaultdict(list)

		self.pos_weight = WEIGHT_POS_RAND
		self.loc_weight = WEIGHT_LOC_RAND

	def addEdge(self, start, end, weight):
		# use a tuple (start, end, weight) instead of a Edge object
		self.graph[start].append((start, end, weight))
		self.graph[end].append((end, start, weight))

	def _rand_method_0(self,preference):
		total_pref = {}
		#calc final preference
		if preference:
			for w in list(set(self.graph.keys())):
				total_pref[w]= self.pos_weight * preference['pos'][w] + self.loc_weight * preference['loc'][w]

		ws = defaultdict(float)
		outSum = defaultdict(float)

		wsdef = 1.0 / (len(self.graph) or 1.0)
		for n, out in self.graph.items():
			ws[n] = wsdef
			outSum[n] = sum((e[2] for e in out), 0.0)

		pref={}
		if total_pref:
			s=float(sum(total_pref.values()))
			for k,v in total_pref.items():#偏好概率归一化
				pref[k]=float(v)/float(s)


		sorted_keys = sorted(self.graph.keys())
		for x in xrange(30):  # 30 iters
			for n in sorted_keys:
				s = 0
				for e in self.graph[n]:
					s += e[2] / outSum[e[1]] * ws[e[1]]
				if not pref:
					ws[n] = (1 - self.d) + self.d * s
				else:
					ws[n] = (1 - self.d)*pref[n] + self.d * s

		return ws

	def rank(self,preference=None):
		# method : 0  -->  use
		result = self._rand_method_0(preference)

		(min_rank, max_rank) = (sys.float_info[0], sys.float_info[3])

		for w in itervalues(result):
			if w < min_rank:
				min_rank = w
			if w > max_rank:
				max_rank = w

		for n, w in result.items():
			# to unify the weights, don't *100.
			result[n] = (w - min_rank / 10.0) / (max_rank - min_rank / 10.0)

		return result

class TextRank():

	pos_legal = ("n","ns","nt","nz","a","an","vn","i","I","j")
	stop_words = []

	#all_words_with_pos = {}

	def __init__(self):
		self.span = 5

		self.pos_pref = {}
		self.loc_pref = {}
		self.freq_pref = {}
		self.final_pref = {}

		self.words = []
		self.wordpairs = []

	@classmethod
	def set_stopwords(cls,stopwordfile):
		'''
		class method to generate all stop words
		:param stopwordfile:  file contains all stop words
		:return:  tuple contains result and error message
		'''
		try:
			with open(stopwordfile) as f:
				for line in f:
					cls.stop_words.append(line.strip().decode('utf-8'))

		except Exception,e:
			return (False,e.message)

		return (True,None)

	@classmethod
	def _is_retain(cls,term,pos):
		#if len(term)>1 and term not in cls.stop_word and ( pos in cls.pos_legal  or (pos=="eng" and len(term)>2 and term[0].isupper())):
		if len(term) > 1 and ( pos in cls.pos_legal  or (pos=="eng" and len(term)>2 and term[0].isupper())):
			return True
		else:
			return False

	def calc_wordpairs(self,newsdict):
		try:
			first = newsdict.get('FIRST_SENTENCE',[])
			last = newsdict.get('LAST_SENTENCE',[])
			mid = newsdict.get('MID_SENTENCE',[])
			whole_text = first + mid + last
			if not whole_text:
				return (False,'news is none')

			title_str = ""
			if newsdict.has_key('TITLE') and newsdict['TITLE']:
				title = []
				for term,pos in newsdict['TITLE']:
					title.append(term)
					#if term not in TextRank.all_words_with_pos:
						#TextRank.all_words_with_pos[term] = pos
				title_str = "".join(title)

			for term,pos in whole_text:
				try:
					term_info = {}
					if TextRank._is_retain(term, pos):
						term_info['pos'] = pos
						if first and term in first:
							term_info['first'] = True
						else:
							term_info['first'] = False
						if last and term in last:
							term_info['last'] = True
						else:
							term_info['last'] = False
						if title_str and term in title_str:
							term_info['title'] = True
						else:
							term_info['title'] = False

						#if term not in TextRank.all_words_with_pos:
							#TextRank.all_words_with_pos[term] = pos
						self.wordpairs.append((term,term_info))
						self.words.append(term)
				except Exception,e1:
					print e1.message
					continue
		except Exception,e2:
			return (False,e2.message)

		return (True,None)

	def calc_preference(self):
		for term,info in self.wordpairs:
			try:
				# calc pos preference
				if self.pos_pref.get(term) == None:
					self.pos_pref[term] = []
				self.pos_pref[term].append(self._get_pos_preference(info['pos']))
				# calc loc preference
				if self.loc_pref.get(term) == None:
					self.loc_pref[term] = self._get_loc_preference_method0(term,info['title'],info['first'],info['last'])
			except Exception,e:
				print e.message
				continue

		if self.pos_pref:
			for w in list(set(self.words)):
				self.pos_pref[w] = np.array(self.pos_pref[w]).mean()

		if self.pos_pref:
			self.final_pref['pos'] = self.pos_pref
		if self.loc_pref:
			self.final_pref['loc'] = self.loc_pref
		if self.freq_pref:
			self.final_pref['freq'] = self.freq_pref

		return self.freq_pref

	def _get_pos_preference(self,pos):
		#根据不同的词性给予词汇不同的分数，分数来源参考"基于语义的中文文本关键词提取算法"
		s=0.1
		if pos[0]==("n"):
			s=0.8
		elif pos=="j":
			s=0.7
		elif pos in ("an","i","I","vn","vd","v"):
			s=0.6
		elif pos in ("eng","a"):
			s=0.5
		return s

	def _get_loc_preference_method0(self,term,title,first_sentences,last_sentences):
		#根据词汇出现的位置打分（标题，（段）首句，（段）未句）
		s=0.0
		if title:
			s += 0.8
		if first_sentences:
			s += 0.1
		if last_sentences:
			s += 0.1
		return s

	def textrank(self, newsdict=None,topK=10):
		# final rank
		try:
			if not newsdict:
				raise ValueError('words not given')

			g = UndirectWeightedGraph()
			cm = defaultdict(int)
			for i, w in enumerate(self.words):
				for j in xrange(i + 1, i + self.span):
					if j >= len(self.words):
						break
					cm[(w, self.words[j])] += 1
			for terms, w in cm.items():
				g.addEdge(terms[0], terms[1], w)

			nodes_rank = g.rank(self.final_pref)

			tags = sorted(nodes_rank, key=nodes_rank.__getitem__, reverse=True)
			if len(tags)>topK:
				return (tags[:topK],None)
			else:
				return (tags,None)

		except Exception,e:
			return (None,e.message)

if __name__=="__main__":
	'''
	demo for textrank_withpref
	
	step 1.  revoke class method set_stopwords to set stopwods file
	step 2.  create TextRank instance 
	step 3.  revoke calc_wordpairs to generate all word-pair for this news-dictionary
	step 4.  revoke calc_preference to generate pref infos
	setp 5.  call textrank method on instance to get top keywords list
	
	news-dictionary contains news content: 
	key TITLE/FIRST_SENTENCE/MID_SENTENCE/LAST_SENTENCE will be used
	one piece of news require one new TextRank instance , but the classmethod should only revoke once
	note : if only one sentence in news content , use it as LAST_SENTENCE
			 if only two sentences in content , use them as FIRST and LAST
	'''
		
	text="\u4e0a\u5e02\u516c\u53f8/nt  \u6b63/d  \u8d1f\u9762/n  \u6d88\u606f/n  \u901f\u89c8/n  \uff1a/x  \u8fd1/t  10/m  \u5bb6/m  \u516c\u53f8/n  \u80a1\u4e1c/n  \u589e\u6301/v  \uff0c/x  \u5929\u6daf\u793e\u533a/l  \u5c06/d  \u6b63\u5f0f/ad  \u6302\u724c/v  \n\n\u3000/x  \u3000/x  \u9999\u6e2f/ns  \u4e07/m  \u5f97/ud  \u901a\u8baf\u793e/nt  \u6574\u7406/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u2014/x  \u2014/x  \u2014/x  \u2014/x  \u6b63\u9762/ad  \u6d88\u606f/n  \u2014/x  \u2014/x  \u2014/x  \u2014/x  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6d69\u4e30\u79d1\u6280/nt  \u5b9a/v  \u589e/v  \u4f5c\u4ef7/n  7.45/m  \u4ebf/m  \u5e76\u8d2d/v  \u8def\u5b89/ns  \u4e16\u7eaa/nt  </x  br/eng  >/x  \u3000/x  \u3000/x  \u83b1\u8335\u7f6e\u4e1a/nt  \u63a8/v  1270/m  \u4e07\u4efd/m  \u80a1\u6743/n  \u6fc0\u52b1/v  \u8ba1\u5212/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u9ed1\u829d\u9ebb/nt  \u5b9a/v  \u589e\u52df/v  \u8d44/n  16/m  \u4ebf/m   /x  \u52a0\u7801/n  \u4e3b\u4e1a/n  \u6d89/v  \u4e92\u8054\u7f51/n  +/x  </x  br/eng  >/x  \u3000/x  \u3000/x  \u9752\u677e\u80a1\u4efd/nt  \u63a8/v  6.5/m  \u4ebf\u5143/m  \u5b9a/v  \u589e/v  \u9884\u6848/n   /x  8/m  \u6708/m  3/m  \u65e5/m  \u590d\u724c/v  </x  br/eng  >/x  \u3000/x  \u3000/x  \u7ef4\u5c14\u5229/nt  \u4e2d\u671f/t  \u51c0\u5229/n  \u589e\u8fd1/v  9/m  \u6210/n   /x  \u8bbe/v  \u5362\u68ee\u5821/ns  \u5b50\u516c\u53f8/n  \u5e03\u5c40/n  \u6d77\u5916/ns  \u5e02\u573a/ns  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6052\u987a\u4f17\u6607/nt  \u4e1a\u7ee9/n  \u5927\u589e/v  \u62df/v  10/m  \u8f6c/v  10/m  \u9001/v  5/m  \u6d3e/v  0.5/m   /x  \u5728/p  \u975e/d  \u8bbe/v  \u4e24/m  " \
	"\u5b50\u516c\u53f8/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u4fdd\u9f84\u5b9d/nt  \u7b79\u5212/n  \u6536\u8d2d/v  \u6559\u80b2/ns  \u884c\u4e1a/n  \u516c\u53f8/n   /x  8/m  \u6708/m  3/m  \u65e5/m  \u8d77/v  \u505c\u724c/v  </x  br/eng  >/x  \u3000/x  \u3000/x  \u7d2b\u5149\u80a1\u4efd/nt  \u518d/d  \u83b7/v  \u7d2b\u5149/nr  \u96c6\u56e2/ns  \u53ca/c  \u4e00\u81f4/d  \u884c\u52a8/vn  \u4eba/n  \u65a5\u8d44/v  \u903e/vg  \u5343\u4e07\u5143/m  \u589e\u6301/v  </x  br/eng  >/x  \u3000/x  \u3000/x  \u5343\u5c71\u836f\u673a/nt  \u6df1\u5ea6/ns  \u5e03\u5c40/n  \u201c/x  \u7cbe\u51c6/n  \u533b\u7597/n  \u201d/x   /x  \u63a7\u80a1/v  \u80a1\u4e1c/n  \u589e\u6301/v  \u5f70\u663e/v  \u4fe1\u5fc3/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u4e1c\u6e90\u7535\u5668/nt  \u83b7/v  \u5b9e\u9645/n  \u63a7\u5236/v  \u4eba/n  \u7d2f\u8ba1/v  \u589e\u6301/v  76.5/m  \u4e07\u80a1/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u4f73\u9686\u80a1\u4efd/nt  \u83b7/v  \u5b9e\u9645/n  \u63a7\u5236/v  \u4eba/n  \u589e\u6301/v  388/m  \u4e07\u80a1/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6c38\u5927\u96c6\u56e2/nt  \u62df/v  2/m  \u4ebf\u5143/m  \u524d\u6d77/ns  \u8bbe/v  \u6295\u8d44/vn  \u516c\u53f8/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6842\u4e1c\u7535\u529b/nt  \u5168\u8d44/n  \u5b50\u516c\u53f8/n  \u589e\u6301/v  \u56fd\u6d77\u8bc1\u5238/nt  20/m  \u4e07\u80a1/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u91cd\u9633\u6295\u8d44/nt  \u4e3e\u724c/v  \u4e0a\u6d77\u5bb6\u5316/nt  </x  br/eng  >/x  \u3000/x  \u3000/x  \u987a\u8363\u4e09\u4e03/nt  \u5b50\u516c\u53f8/n  \u4e0e/p  \u661f\u7693/i  \u5f71\u4e1a/vn  \u5408\u4f5c/ns   /x  \u8fdb\u519b/v  " \
	"\u5f71\u89c6/n  \u884c\u4e1a/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6c5f\u4e2d\u836f\u4e1a/nt  \u4e2d\u671f/t  \u51c0\u5229/n  1.39/m  \u4ebf/m   /x  \u540c\u6bd4/j  \u589e\u957f/v  45/m  %/x  </x  br/eng  >/x  \u3000/x  \u3000/x  \u529b\u6e90\u4fe1\u606f/nt  \u4e0a\u534a\u5e74/t  \u51c0\u5229/n  \u540c\u6bd4/j  \u5927\u589e/v  \u903e/vg  \u4e00\u500d/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u65b0\u5357\u6d0b/nt  \u4e94/m  \u9ad8\u7ba1/n  \u589e\u6301/v  5/m  \u4e07\u80a1/m   /x  \u6b63/d  \u7814\u7a76/vn  \u80a1\u6743/n  \u6fc0\u52b1/v  \u8ba1\u5212/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u5929\u55bb\u4fe1\u606f/nt  \u83b7/v  \u63a7\u80a1/v  \u80a1\u4e1c/n  \u589e\u6301/v  107/m  \u4e07\u80a1/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u5965\u514b\u80a1\u4efd/nt  1.3/m  \u4ebf/m  \u8d2d/vg  \u4e1c\u7855/nr  \u73af\u4fdd/j  37/m  %/x  \u80a1\u6743/n   /x  \u63a8\u52a8/v  \u7eff\u8272/n  \u73af\u4fdd/j  \u4e1a\u52a1/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u5927\u4e1c\u65b9/nt  \u7ea6/d  1900/m  \u4e07/m  \u6536\u8d2d/v  \u5b50\u516c\u53f8/n  \u767e\u4e1a/n  \u8d85\u5e02/v  40/m  %/x  \u80a1\u6743/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6c38\u9f0e\u80a1\u4efd/nt  \u63a8/v  \u5458\u5de5/n  \u6301\u80a1/v  \u8ba1\u5212/n   /x  \u5c06/d  \u8d2d\u5165/v  \u7ea6/d  300/m  \u4e07\u80a1/m  \u516c\u53f8\u80a1\u7968/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u795e\u5dde\u6cf0\u5cb3/nt  \u589e\u8d44/v  \u63a7\u80a1/v  \u5b50\u516c\u53f8/n   /x  \u52a0\u7801/n  \u79fb\u52a8/vn  \u4e92\u8054\u7f51/n  \u5927/a  \u6570\u636e/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u534e\u5a92\u63a7\u80a1/nt  \u4e0e/p  \u963f\u91cc/ns  \u6218\u7565/n  " \
	"\u5408\u4f5c/ns   /x  \u6253\u9020/v  \u57ce\u5e02/ns  \u751f\u6d3b/vn  \u670d\u52a1\u5546/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6676\u76db\u673a\u7535/nt  \u5b9a/v  \u589e\u52df/v  \u8d44/n  16/m  \u4ebf\u5143/m   /x  \u52a0\u7801/n  \u84dd\u5b9d\u77f3/nr  \u9879\u76ee/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u94c1\u6c49\u751f\u6001/nt  9600/m  \u4e07/m  \u6536\u8d2d/v  \u73af\u53d1/j  \u73af\u4fdd/j  80/m  %/x  \u80a1\u6743/n   /x  \u52a0\u7801/n  \u73af\u4fdd/j  \u9886\u57df/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u7231\u5c14\u773c\u79d1/nt  \u65a5\u8d44/v  2/m  \u4ebf/m  \u518d\u6b21/d  \u53c2\u4e0e/v  \u5e76\u8d2d/v  \u57fa\u91d1/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6210\u90fd\u8def\u6865/nt  \u4e2d\u6807/ns  1.81/m  \u4ebf\u5143/m  PPP/eng  \u9879\u76ee/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6d3d\u6d3d\u98df\u54c1/nt  \u63a8/v  1.5/m  \u4ebf\u5143/m  \u5458\u5de5/n  \u6301\u80a1/v  \u8ba1\u5212/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u68ee\u8fdc\u80a1\u4efd/nt  \u8bbe/v  \u5408\u8d44/vn  \u516c\u53f8/n   /x  \u4fc3\u8fdb/ns  \u5927\u578b/b  \u518d\u751f/v  \u8bbe\u5907/vn  \u63a8\u5e7f\u5e94\u7528/i  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6da6\u90a6\u80a1\u4efd/nt  \u4e0e/p  \u6e05\u63a7/vn  \u8d44\u7ba1/n  \u5408\u4f5c/ns   /x  \u63a8\u52a8/v  \u8282\u80fd/v  \u73af\u4fdd/j  \u4ea7\u4e1a/n  \u53d1\u5c55/vn  </x  br/eng  >/x  \u3000/x  \u3000/x  \u65af\u7c73\u514b/nt  \u62df/v  \u6218\u7565/n  \u5165\u80a1/v  \u946b/nr  \u5c71/n  \u4fdd\u9669\u4ee3\u7406/n  \u516c\u53f8/n  </x  br/eng  >/x  \u3000/x  \u3000/x  */x  ST/eng  \u4e50/a  \u7535/n  \u4e2d\u671f/t  \u51c0\u5229/n  \u540c\u6bd4/j  \u589e/v  " \
	"\u4e09\u6210/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u798f\u751f\u4f73/nz  \u4fe1/n  225/m  \u4e07/m  \u53c2\u80a1/v  \u8bbe\u7acb/v  \u4e0a\u95e8/ns  \u63a8\u62ff/v  \u670d\u52a1\u516c\u53f8/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u5206\u8c46/n  \u6559\u80b2/ns  \u5b9a/v  \u589e\u52df/v  \u8d44/n  4.5/m  \u4ebf/m  \u52a0\u7801/n  \u4e3b\u4e1a/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u5929\u6daf\u793e\u533a/l  \u5c06/d  \u6b63\u5f0f/ad  \u6302\u724c/v   /x  \u52df/vg  \u8d44/n  3999/m  \u4e07\u5143/m  \u89e3\u51b3/v  \u77ed\u671f/b  \u6d41\u52a8\u8d44\u91d1/n  \u9700\u6c42/v  </x  br/eng  >/x  \u3000/x  \u3000/x  \u2014/x  \u2014/x  \u2014/x  \u2014/x  \u8d1f\u9762/n  \u6d88\u606f/n  \u2014/x  \u2014/x  \u2014/x  \u2014/x  </x  br/eng  >/x  \u3000/x  \u3000/x  \u4e07\u8fbe\u9662\u7ebf/nt  \u6f84\u6e05/v  \u738b\u5065\u6797/nr  \u59bb\u5b50/n  \u5185\u5e55/n  \u4ea4\u6613/n  \u4f20\u95fb/n  </x  br/eng  >/x  \u3000/x  \u3000/x  \u795e\u5f00\u80a1\u4efd/nt  \u603b\u7ecf\u7406/n  \u6d89/v  \u77ed\u7ebf\u4ea4\u6613/n  \u88ab/p  \u8bc1\u76d1\u4f1a/j  \u7acb\u6848/n  \u8c03\u67e5/vn  </x  br/eng  >/x  \u3000/x  \u3000/x  \u4e2d\u6d77\u8fbe/nt  \u4e0a\u534a\u5e74/t  \u51c0\u5229/n  \u4e0b\u964d/v  \u903e/vg  \u4e03\u6210/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u7696\u6c5f\u7269\u6d41/nt  \u6536\u5230/v  \u8bc1\u76d1\u4f1a/j  \u884c\u653f\u5904\u7f5a/n  \u4e66/n   /x  \u88ab/p  \u8b66\u544a/n  \u5e76/c  \u7f5a\u6b3e/n  50/m  \u4e07\u5143/m  </x  br/eng  >/x  \u3000/x  \u3000/x  \u6d77\u5b81\u76ae\u57ce/nt  \u4e0a\u534a\u5e74/t  \u51c0\u5229/n  5.11/m  \u4ebf/m   /x  \u540c\u6bd4/j  \u964d/v  14/m  %/x  </x  br/eng  >/x  \u3000/x  " \
	"\u3000/x  \u90e8\u5206/n  \u4ea7\u54c1/n  \u5904/n  \u57f9\u80b2/vn  \u671f/n   /x  \u5343\u91d1\u836f\u4e1a/nt  \u4e2d\u671f/t  \u51c0\u5229/n  \u4e0b\u6ed1/v  8.5/m  %/x  </x  br/eng  >/x  \u3000/x  \u3000/x"
	# news
	# id :
	# title :
	# first :
	# last :
	# content :
	# keywords :

	newsdict = {}
	newsdict['TITLE'] = None
	newsdict['FIRST_SENTENCE'] = u""
	newsdict['MID_SENTENCE'] = u""
	newsdict['LAST_SENTENCE'] = text

	topK = 10

	try:
		TextRank.set_stopwords('/home/lc/ht_work/news_textrank/stopwords_wz.txt')

		tr=TextRank()
		ret,err = tr.calc_wordpairs(newsdict)
		if not ret:
			raise ValueError(err)

		tr.calc_preference()

		keywords,err = tr.textrank(newsdict,topK=topK)
		if not keywords:
			raise ValueError(err)

		print " ".join(keywords)

	except Exception as e:
		print e.message

