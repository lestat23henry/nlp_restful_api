

/**********************************************************************************
*** 作者： 梁辰 henry_liangc@163.com
    功能： 通过http服务，向调用者提供nlp基础功能服务，具体包括：
          1. 获取关键词列表
          2. 获取文章情感打分

    接口： /               获取服务描述信息
          /stats          获取服务统计信息，主要包括成功和失败的计数
          /nlp_process    实际提供服务接口，POST方式调用，参数如下：
                            输入JSON格式参数
	                            title : 新闻标题
	                            content : 新闻正文
	                            kw_topK : 获取关键词的个数  ( optional , default is 5 )
	                            publish_date : 新闻发布时间
	                            catagory : 新闻的类别
	                        返回json格式信息
	                            keywords : 关键词列表
	                            sentiment : 情感分数
	                            keywords_err : 如果关键词提取出错，此处为错误信息，否则None
	                            sentiment_err : 如果情感分析出错，此处为错误信息，否则None
	                       注： 输入输出均应使用utf-8编码格式
	      /nlp_update     更新数据模型接口，目前为空实现

    示例：
        def curl_to_api(self,title,content):
            post_url = 'http://127.0.0.1:5555/nlp_process'

		    headers = {'Content-Type': 'application/json'}

		    post_data = {}
		    post_data['title'] = title                     #新闻标题
		    post_data['content'] = content                 #新闻正文
		    post_data['kw_topK'] = 10                      #想提取的关键词个数

		    data = json.dumps(post_data)

		    req = urllib2.Request(post_url,headers=headers,data=data)

		    response = urllib2.urlopen(req)

		    return response.read()



***************************************************************************************/