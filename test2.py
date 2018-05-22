#!/usr/bin/env python3 
# -*- coding: utf-8 -*-

__author__ = 'baoshuxie'

import os
import requests
from selenium import webdriver
from datetime import datetime
import time
import math

#定义用于下载图片url的request头部
def header(referer):
	headers = {
        'Host': 'fmn.rrimg.com',
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.115 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': '{}'.format(referer),
	}
	return headers

#获取关注的用户的urls
def get_urls(base_user_id,users):

	browser = webdriver.PhantomJS()
	urls =[]
	base_url = 'http://www.renren.com/SysHome.do'	#登录页
	browser.get(base_url)
	browser.find_element_by_id('email').clear()		
	browser.find_element_by_id('password').clear()
	browser.find_element_by_id('email').send_keys('xxxxxxxxxxxx')       #请输入你自己的手机号
	browser.find_element_by_id('password').send_keys('xxxxxxx')	#请输入你自己的密码
	browser.find_element_by_id('login').click()
	time.sleep(1)									#请勿注释掉这一句
	user_ids=['%s' %base_user_id]
	print('OK1')

	count=0				#count是用来控制循环的，否则user_ids不断被append进urls,会直到爬取完所有的人人页面才终止程序

	for user_id in user_ids:
		user_id = user_ids.pop(0)
		user_url = 'http://follow.renren.com/list/' + user_id + '/pub/v7'		#访问每个用户的关注用户页
		browser.get(user_url)
		followers = browser.find_elements_by_class_name('photo')			#用选择器找到每个关注者

		for follower in followers:
			follower_id = follower.get_attribute('namecard')				#拿到关注者的user_id
			print(follower_id)
			if follower_id not in user_ids:
				user_ids.append(follower_id)								#简单的去重，加入user_ids列表
			
			url='http://photo.renren.com/photo/' + '%s' % follower_id + '/albumlist/v7?offset=0&limit=40#'  #构造关注者的相册url
			if url not in urls:
				urls.append(url)
				print(url)

		count += 1
	
		if count==users:
			
			break

	#print('OK2')

	if user_ids:
		print(user_ids[-1])
		with open('photos/last_id.txt','w+',encoding='utf-8') as f:		#循环结束后，将user_ids里面最后一个user_id写入本地文件
			f.write(user_ids[-1])
		with open('photos/time.txt','a+',encoding='utf-8') as f:		#记录运行时间和每次保存的最后一个user_id
			f.write(user_ids[-1]+'\n')

	#print(urls)

	browser.quit()
	return urls


def get_photo_urls(base_user_id,users):
	browser = webdriver.PhantomJS()
	urls = get_urls(base_user_id,users)					#调用get_urls获取urls
	album_urls = []
	base_url = 'http://www.renren.com/SysHome.do'
	browser.get(base_url)
	browser.find_element_by_id('email').clear()
	browser.find_element_by_id('password').clear()
	browser.find_element_by_id('email').send_keys('13689024414')
	browser.find_element_by_id('password').send_keys('19950708')
	browser.find_element_by_id('login').click()
	time.sleep(1)

	print('OK3')

	#print(browser.get_cookies())
	for url in urls:
		print(url)
		browser.get(url)
		browser.implicitly_wait(3)
		albums=browser.find_elements_by_class_name("album-box")				#找到相册
		
		for album in albums:
			if not album:
				continue
			album_url = album.find_element_by_class_name('album-item').get_attribute('href')
			count = album.find_element_by_class_name('album-count').text
			item={}
			print(album_url,count)
			item['url'] = album_url				
			item['count'] = int(count)
			album_urls.append(item)						#album_urls是dict的list,包含每个相册的url和相册中照片的数量count

	photo_urls=[]										
	for item in album_urls:    #http://photo.renren.com/photo/500999244/album-848184418/v7?page=3&pageSize=20
		for i in range(1,math.ceil(item['count']/20)+1):
		
			browser.get(item['url']+'?page=%d&pageSize=20'%i)		#访问照片数据来源的url
			
			browser.implicitly_wait(3)
			photos=browser.find_elements_by_class_name("photo-box")	
			for photo in photos:
				photo_url = photo.find_element_by_class_name('p-b-item').get_attribute('src')
				print(photo_url)
				photo_urls.append(photo_url)

	browser.quit()

	return photo_urls

#创建路径
def make_dir(path):
	if not os.path.exists(path):
		os.mkdir(path)
	return None

#图片保存到本地
def save_photos(urls):
	date = datetime.now()
	dir_name = date.strftime('%b %d')
	make_dir('photos/'+dir_name)
	n=1
	for url in urls:
		if not url:
			continue
		print(url)
		name = url[8:].replace('/','_')

		file_name = '%s' % name
		with open('photos/'+dir_name+'/'+file_name,'wb+') as f:				#请确保在本脚本的同级目录下有一个photos文件夹，下载的图片将会存储在photos下按日期建立的文件夹中
			f.write(requests.get(url,headers=header(url)).content)
		print('正在下载第%s张图片' % n)
		n = n+1
	print('OK4')
	return n 										#

def main():
	start_time=datetime.now()						
	start_date=start_time.strftime('%b''%d')
	with open('photos/last_id.txt','r') as f:
		base_user_id=f.read()						#获取初始id,每次运行本程序之后此ID在get_urls()中更新
	users = 10										#获取循环次数
	photo_urls = get_photo_urls(base_user_id,users)
	num = save_photos(photo_urls)
	end_time=datetime.now()
	do_time = (end_time - start_time).seconds
	with open('photos/time.txt','a+',encoding='utf-8') as f:
		f.write("{} 爬取了 {} 张图片,耗时{}秒\n".format(start_date,num,do_time))


main()
