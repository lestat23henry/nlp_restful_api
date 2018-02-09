# coding=utf-8
# author : liangchen
# decription : class doc_splitter to split all words in one directory path,generate new files(with segmented words in)

import os
from multiprocessing import cpu_count
import re
from datetime import datetime

from pathlib import Path
import jieba
import jieba.posseg as pseg
import codecs

class doc_splitter():
	def __init__(self,srcdir,targetfile,stopwordfiles=None,userdicts=None,parallel=True):
		self.srcdir = srcdir
		self.tagfile = targetfile

		self.stopword = []
		self.number = re.compile(ur'([一二三四五六七八九零十百千万亿]+点{0,1}[一二三四五六七八九零十百千万亿]+|[0-9]+\.{0,1}[0-9]*)')

		if stopwordfiles:
			for sw in stopwordfiles:
				self._load_stopwords(sw)  #dict
		self.parallel = parallel

		jieba.initialize()
		if userdicts:
			for ud in userdicts:
				jieba.load_userdict(ud)

		if self.parallel:
			jieba.enable_parallel(cpu_count())

	def _load_stopwords(self,fn):
		try:
			with open(fn) as f:
				for line in f:
					try:
						self.stopword.append(line.strip().decode('utf-8'))
					except Exception,e:
						continue

		except Exception,e:
			print e.message



	def utf8_one_doc(self,filepath):
		if not filepath:
			return

		print u'time: %s ==> 转换文件%s为utf-8格式\n' % (datetime.now(),filepath)
		filepath_utf8 = '/tmp' + os.path.sep + os.path.splitext(os.path.basename(filepath))[0] + '_utf8' + '.txt'

		if os.path.exists(filepath_utf8):
			print u'time: %s ==> 文件%s已经转换为%s\n' % (datetime.now(), filepath,filepath_utf8)
			return filepath_utf8

		with open(str(filepath),'r') as fr:
			with open(filepath_utf8,'w') as fw:
				line = fr.readline()
				while line:
					if line == '\r\n':
						line = fr.readline()
						continue
					newline = line.decode('GB18030').encode('utf-8')
					print newline
					print >> fw, newline
					line = fr.readline()

		print u'time: %s ==> 文件%s已经转换为%s\n' % (datetime.now(), filepath, filepath_utf8)
		return filepath_utf8

	def split_one_string(self,str):
		if not str:
			return ([],"no str to split")
		try:
			line_list = self.number.split(str.strip())
			line_result_list = []
			out_pair_list = []
			for line_str in line_list:
				try:
					if self.number.match(line_str):
						line_result_list.append(line_str)
						out_pair_list.append((line_str,u'm'))
					else:
						line1 = re.sub("[\s+\.\!\/_,$%^*()?;；:-【】+\"\']+|[+－——！，;:：。？、~@#￥%……&*（）]+".decode("utf8"), \
								   "".decode("utf8"), line_str)

						word_pair_list = pseg.cut(line1)
						if self.stopword:
							out_pair = [(wordpair.word,wordpair.flag) for wordpair in word_pair_list if wordpair.word not in self.stopword]
						else:
							out_pair = [(wordpair.word,wordpair.flag) for wordpair in word_pair_list]

						out_pair_list.extend(out_pair)
				except Exception,e:
					print e.message
					continue

			return (out_pair_list,None)

		except Exception,e:
			print e.message
			return ([],e.message)


	def split_content(self,text):
		#text = re.sub(' ', '', text)  # 去文字间的空格
		if not text:
			return ([],[],[],"to content to split")
		else:
			try:
				# todo !!
				# news_list = re.split(r'([。！？])', text)
				news_list = re.split(u'。', text)
				length = len(news_list)
				if length == 0:
					return ([],[],[],"split content get 0 length")
				if length <= 2:
					first_sen = u''
					mid_sen = u''
					last_sen = u''.join(news_list[0])
				elif length == 3:
					first_sen = u''.join(news_list[0])
					mid_sen = u''
					last_sen = u''.join(news_list[1])
				elif length == 4:
					first_sen = u''.join(news_list[0])
					mid_sen = u''.join(news_list[1])
					last_sen = u''.join(news_list[2])
				else:
					first_sen = u''.join(news_list[0])
					last_sen = u''.join(news_list[-2])
					mid_sen = u''.join(news_list[1:-2])

				first_sen_seg,_ = self.split_one_string(first_sen)
				mid_sen_seg,_ = self.split_one_string(mid_sen)
				last_sen_seg,_ = self.split_one_string(last_sen)

				return (first_sen_seg,mid_sen_seg,last_sen_seg,None)

			except Exception,e:
				print e.message
				return ([],[],[],e.message)


	def split_one_doc(self,filepath):
		if not filepath:
			return

		print u'time: %s ==> 对文件%s进行分词\n' % (datetime.now(), filepath)
		#filepath_segmented = self.tagdir + os.path.sep + os.path.splitext(os.path.basename(filepath))[0] + '_segmented' + '.txt'
		filepath_segmented = self.tagfile

		with open(filepath,'r') as fr:
			with open(filepath_segmented,'a') as fw:
				line = fr.readline()
				while line:
					if line == '\r\n':
						line = fr.readline()
						continue
					line_str = line.strip().decode('utf-8', 'ignore')  # 去除每行首尾可能出现的空格，并转为Unicode进行处理
					line1 = re.sub("[\s+\.\!\/_,$%^*()?;；:-【】+\"\']+|[+－——！，;:：。？、~@#￥%……&*（）]+".decode("utf8"),
								   "".decode("utf8"), line_str)

					word_list = list(jieba.cut(line1,cut_all=False,HMM=True))  # 用结巴分词，对每行内容进行分词
					if self.stopword:
						out_str = [word+' ' for word in word_list if word not in self.stopword]
					else:
						out_str = word_list
					fw.write(" ".join(out_str).strip().encode('utf-8') + '\n')  # 将分词好的结果写入到输出文件
					line = fr.readline()

		print u'time: %s ==> 文件%s分词结束，保存到%s\n' % (datetime.now(), filepath, filepath_segmented)
		return filepath_segmented


	def split_all(self):
		p = Path(self.srcdir)
		for txt in p.glob("**/*.txt"):
			txt_utf8 = self.utf8_one_doc(str(txt))
			self.split_one_doc(txt_utf8)

		return True


#class test:
if __name__=='__main__':
	ds = doc_splitter('/home/lc/ht_work/ML/old_txt','/home/lc/ht_work/ML/new_txt/allwords.txt','/home/lc/ht_word/xwparse/stopwords_merge.txt','/home/lc/ht_work/xwparse/userdict.txt',True)
	wordpair = ds.split_one_string(u'小明硕士毕业于中国科学院计算所，后在日本京都大学深造')
	#ds.split_all()

