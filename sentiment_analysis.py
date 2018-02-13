# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 16:18:54 2018

@author: ZhWang
"""
from __future__ import absolute_import, unicode_literals
import jieba
import jieba.posseg as pseg
import re 
import pickle

      
class Sentiment_Analysis():

    stm_dict = {}
    dg_dict = {}
    not_dict = {}

    def __init__(self,):
        self.re_sen=re.compile('[。！？，；]') #当前仍以逗号为最短分割

    @classmethod
    def load_dict_resource(cls,stm_dict_pkl,dg_dict_pkl,not_dict_pkl):
        with open(stm_dict_pkl,'rb') as sr:
            cls.stm_dict=pickle.load(sr)
        with open(dg_dict_pkl,'rb') as sr:
            cls.dg_dict=pickle.load(sr)
        with open(not_dict_pkl,'rb') as sr:
            cls.not_dict=pickle.load(sr)

    #计算句子整体评分
    def calc_point(self,p_stm):
        if not p_stm:
            return 0  
        else:
            pos_list=[num for num in p_stm if num>0]
            neg_list=[num for num in p_stm if num<0]
            if sum(pos_list)+sum(neg_list)>0:  
                num_list=pos_list
                flag=1
            elif sum(pos_list)+sum(neg_list)<0:
                num_list=[abs(num) for num in neg_list]
                flag=-1
            else:
                return 0
            if len(num_list) == 1:
                return num_list[0]
            else:
                if max(num_list) == 10:  
                    if flag == 1:
                        return 10
                    elif flag == -1:
                        return -10
                    else:
                        return 0
                else:
                    sum_denom=sum(num_list)  #分母
                    domin=max(num_list)           
                    num_list.remove(domin)
                    try:
                        point=domin+2*(sum(num_list)+min(num_list))/sum_denom
                    except Exception as e:
                        print(e.message)
                        return 0
                    if point > 10:
                        point=10
                    if flag == 1:
                        p_val=point
                    elif flag == -1:
                        p_val=-point
                    else:
                        return 0
                    return p_val 
    #由普通句来主导评分
    def dominate_bysentence(self,p_sen_list,prior):
        if prior == 0:
            p=self.calc_point(p_sen_list)
            c=abs(p)/10
        else:
            num_list=[abs(num) for num in p_sen_list if num*prior < 0]
            if len(num_list) == 0:
                return 0
            elif len(num_list) == 1:
                return num_list[0]
            else:                           
                sum_denom=sum(num_list)  #分母
                domin=min(num_list)           
                num_list.remove(domin)
                try:
                    point=domin+2*sum(num_list)/sum_denom
                except Exception as e:
                    print(e.message)
                    return 0
                if point > 10:
                    return 1
                else:
                    c=point/10
        return c
    #普通句的否定质疑
    def doubt_bysentence(self,p_sen_list,p):
        len_stm=len(p_sen_list)
        num_diff=0
        for p_sen in p_sen_list: #p_sen 是各短句情感
            if p_sen * p < 0: #与待判断的内容异向情感
                num_diff+=1 
        if num_diff >= 0.9*len_stm:
            flag_wrong=2     #重度隐患
        elif num_diff >= 0.75*len_stm:
            flag_wrong=1     #轻度隐患
        else:
            flag_wrong=0     #可认为无隐患
        return flag_wrong 
    #提取特征
    def extraction_feature(self,text):
        ti=0
        p_dg=0
        p_not=0
        ti_not=0
        neg_list=[]
        pos_list=[]        
        slp=pseg.lcut(text) #对该句话分词，分析
        length=len(slp)
        for i in range(length):
            p=0 #未匹配到特征情感值为0
            if slp[i].flag in ['a','an'] and slp[i].word in self.stm_dict:#特征1                
                if i != 0 and slp[i-1].word in self.dg_dict:
                    p_dg=p_dg+self.dg_dict[slp[i-1].word]
                elif i != length-1 and slp[i+1].word in self.dg_dict:
                        p_dg=p_dg+self.dg_dict[slp[i+1].word]         
                for j in range(length):
                    if j==i:
                        continue
                    if slp[j].word in self.not_dict and ti_not<2: #要判断单重与双重否定
                        ti_not+=1
                        if ti_not==1:
                            p_not=p_not+self.not_dict[slp[j].word]
                        elif ti_not==2:
                            p_not=p_not-self.not_dict[slp[j].word]
                if self.stm_dict[slp[i].word]>0:                        
                    p=self.stm_dict[slp[i].word]+p_dg-p_not
                elif self.stm_dict[slp[i].word]<0:
                    p=self.stm_dict[slp[i].word]-p_dg+p_not
                if ti == 0:
                    ti+=1
                #print((slp[i].word,p,'F1'))
            elif 'v' in set(slp[i].flag) and slp[i].word in self.stm_dict:#特征2
                if i != 0 and slp[i-1].word in self.dg_dict:
                    p_dg=p_dg+self.dg_dict[slp[i-1].word]
                elif i != length-1 and slp[i+1].word in self.dg_dict:
                    p_dg=p_dg+self.dg_dict[slp[i+1].word]
                for j in range(length):
                    if j==i:
                        continue
                    if slp[j].word in self.not_dict and ti_not<2:
                        ti_not+=1
                        if ti_not==1:
                            p_not=p_not+self.not_dict[slp[j].word]
                        elif ti_not==2:
                            p_not=p_not-self.not_dict[slp[j].word]
                if self.stm_dict[slp[i].word]>0:
                    p=self.stm_dict[slp[i].word]+p_dg-p_not
                else:
                    p=self.stm_dict[slp[i].word]-p_dg+p_not
                if ti == 0:
                    ti+=1
                #print((slp[i].word,p,'F2'))
            elif slp[i].flag=='n' and slp[i].word in self.stm_dict:   #特征3
                for j in range(length):
                    if j==i:
                        continue
                    if slp[j].word in self.not_dict and ti_not<2:
                        ti_not+=1
                        if ti_not==1:
                            p_not=p_not+self.not_dict[slp[j].word]
                        elif ti_not==2:
                            p_not=p_not-self.not_dict[slp[j].word]
                if self.stm_dict[slp[i].word]>0:
                    p=self.stm_dict[slp[i].word]-p_not
                else:
                    p=self.stm_dict[slp[i].word]+p_not
                if ti == 0:
                    ti+=1
                #print((slp[i].word,p,'F3'))
            if p > 0:
                if p > 10:
                    p=10
                pos_list.append(p)
            if p < -0:
                if p<-10:
                    p=-10
                neg_list.append(abs(p))
        if len(pos_list) == 0 and len(neg_list) == 0:
            p_val=0
        elif len(pos_list) != 0 and len(neg_list) == 0: 
            p_val=max(pos_list)
        elif len(pos_list) == 0 and len(neg_list) != 0:
            p_val=-max(neg_list)
        elif max(pos_list) >= max(neg_list): #包括了max()值为0的情况
            p_val=max(pos_list)
        else:
            p_val=-max(neg_list)
        return p_val
    #找关键句(待完成)
    def find_keysentence():
        pass
    
    def sentiment_analysis(self,request_dict):
        try:
            flag=0  #情感极性
            c=0     #总确信度    
            title=request_dict['title'] #标题文本内容
            content=''.join(request_dict['content'].split()) #正文文本内容
            #分析标题情感
            p_tit=0 
            if title:
                p_tit=self.extraction_feature(title)        
            #计算 Ct
            if p_tit != 0:
                c_tit=0.45+0.1*abs(p_tit)/10 
            else:
                c_tit=0
            #分析正文关键句子情感
            #p_key=find_keysentence(content) #当前该函数暂空,待完善
            p_key=0
            #分析正文普通句子情感
            p_sen_list=[]
            text_list=self.re_sen.split(content)[:-1]
            for text in text_list:
                if text:
                    p=self.extraction_feature(text)
                    if p != 0:
                        p_sen_list.append(p) #记录一篇文章中每个短句的非中性情感词        
            p_con=self.calc_point(p_sen_list) #计算正文普通句的整体情感       
            if c_tit > 0:  #有标题情感(p_tit != 0)，最外部判断        
                if p_key != 0:  #暂不会进入该条件
                    c_key=0.2+0.1*abs(p_key)/10
                else:
                    c_key=0             
                if p_con != 0:
                    c_con=0.2+0.1*abs(p_con)/10
                else:
                    c_con=0
                #标题情感和关键词情感的综合评估
                if p_key*p_tit > 0:
                    c=c_tit+1.5*c_key
                else:
                    c=c_tit-0.5*c_key  #已经包括了c_key==0的情况
                #根据标题与关键词的先验情感计算总确信度
                if c < 0.45: #暂不会进入该条件
                    if p_con*p_tit > 0:
                        c=c+1.2*c_con
                    else:
                        c=c-0.8*c_con  #已经包括了c_con==0的情况
                elif c >= 0.75: #暂不会进入该条件
                    if p_con*p_tit > 0:
                        c=c+1.5*c_con  #已经包括了c_con==0的情况
                else: 
                    if p_con*p_tit > 0: 
                        c=c+1.5*c_con
                    else:
                        c=c-0.5*c_con  #已经包括了c_con==0的情况
                flag=p_tit/abs(p_tit)
                #分析是否应该推翻先验的标题情感
                if self.doubt_bysentence(p_sen_list,p_tit) == 2 and c_key == 0:
                    c=self.dominate_bysentence(p_sen_list,p_tit)
                    if c != 0:
                        flag=-p_tit/abs(p_tit)
                    else:
                        flag=0
                if self.doubt_bysentence(p_sen_list,p_tit) >= 1 and p_key*p_tit < 0:
                    flag=-p_tit/abs(p_tit)
                    c=c_key+c_con
                if c > 1:
                    c=1 #满分推荐
            elif c_tit == 0: #标题无情感(p_tit == 0) 
                if p_key != 0:  #暂不会进入该条件
                    c_key=0.3+0.1*abs(p_key)/10  #在无标题情感时关键句的价值提升
                    if p_con != 0:
                        c_con=0.2+0.1*abs(p_con)/10
                    else:
                        c_con=0
                    if c_con*c_key > 0:
                        c=c_key+1.5*c_con
                    else:
                        c=c_key-0.5*c_con  #已经包括了c_con==0的情况
                    flag=p_key/abs(p_key)
                    #分析是否应该推翻先验的关键句情感
                    if self.doubt_bysentence(p_sen_list,p_key) >= 1: 
                        c=self.dominate_bysentence(p_sen_list,p_key)
                        if c != 0:
                            flag=-p_key/abs(p_key)
                        else:
                            flag=0
                else:  #此时只有正文普通句子可以判断情感，是当前常进入的条件分支
                    c=self.dominate_bysentence(p_sen_list,0)  #该操作先放在函数中有待潜在的扩展
                    if c != 0:
                        flag=p_con/abs(p_con)
                    else:
                        flag=0
            else: 
                print('This conition can not be activated if normal')
            return ((flag,c),None) 
        except Exception as e:
            return (None,e.message)
                   


if __name__=="__main__":
    '''
    demo for sentiment_analysis
    
    step 1.  creat Sentiment_Analysis instance
    step 2.  load all kinds of useful dictionaries for analyzing sentiments
    step 3.  evaluate the sentiment of the title and its result wiil be a significant prior for next analysis
    step 4.  find key sentences in the article (need to edit)
    step 5.  evaluate those key sentences according to the mark of the sentiment of the title
    step 6.  after that, begin to process those common sentences
    step 7.  calculate synthesis scores by current tactics
    step 8.  reflect the accuracy of the score automatically and try to doubt the former result
    step 9.  decide whether to subvert the former result or not with authentic data statistics
    step 10. calculate the final score and demostrate the polarity and the quantity
    
    '''
    text="日前，由上投摩根基金独家代理的“北上”互认基金摩根亚洲总收益债券\
    基金AsianInvestor（亚洲投资杂志）颁发的资产管理奖项――“Best RetailProduct优秀零售基金”殊荣。\
    据统计，自摩根亚洲债券2016年年初在内地发售以来，截至今年5月11日，其累计销售额达到人民币62亿元，\
    占全部北上基金销售规模的9成以上。据了解，摩根亚洲债券成立至今已有12年历史，\
    在此期间始终由同一位基金经理管理，运作风格相对稳定，投资收益也较为稳健。"
    newsdict={}
    newsdict['title']='摩根亚洲总收益债券获殊荣'
    newsdict['content']=text
    try:
        sa=Sentiment_Analysis()
        ci=0
        test=[]
        for elem in hexun_bondnews:
            newsdict['title']=elem[0]
            newsdict['content']=elem[1]
            if ci == 10:
                break
            ci+=1
            result=sa.sentiment_analysis(newsdict)
            test.append(result)
    except Exception as e:
        print(e)

    
    
    
    
    
    
    
