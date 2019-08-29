# -*- coding: utf-8 -*-

import logging
import requests
import json
import re
import schedule
import time
import math
import uuid
from datetime import datetime

from logging.config import fileConfig
from urllib.parse import urlencode, urlparse, parse_qs
from requests import RequestException
from math import ceil
from bs4 import BeautifulSoup

from config import *
from db_utils import *
from request_utils import *
from common_utils import *
from mail_utils import *


fileConfig('logging_config.ini')
logger = logging.getLogger('app_xs')


DOMAIN_URL = 'http://www.xszbjyw.com'

#更新隐藏值用于翻页
def update_hidden_tags(soup, tags, page_no):
    tags['__VIEWSTATE'] = soup.find(id='__VIEWSTATE')['value']
    tags['__EVENTVALIDATION'] = soup.find(
        id='__EVENTVALIDATION')['value']
    tags['GridViewer1$ctl18$NumGoto'] = str(page_no)

    return tags

#获取总页数和页面url
def get_a_index(url, headers, tags):
    # print(url)
    logger.info('抓取第%s页' % tags['GridViewer1$ctl18$NumGoto'])
    print('抓取第%s页' % tags['GridViewer1$ctl18$NumGoto'])
    # url = SX_MAIN_ZB_LINK

    rt = []

    # a_page = requests.post(url, data=tags)
    # a_page.encoding = 'UTF-8'
    rt_page = post_one_url_with_headers(url, headers, tags)
    if rt_page:
        bs = BeautifulSoup(rt_page, 'lxml')
        #print(bs)
    else:
        logger.error('拿不到页面，跳过...')
        return (None, None)
        # print(a_page.text)

    notecies = bs.find_all('a')
    for notice in notecies:
        hrefs = notice['onclick'].split(',')
        title = notice.string.strip()
        #print('title='+title)
        #print('hrefs1=' + hrefs[1].replace("'", "")+'hrefs2=' + hrefs[2].replace("'", ""))
        rt.append({'id': hrefs[2].replace("'", ""), 'title': title,
                       'url': 'http://www.xszbjyw.com/web_news/WebFromList.aspx?news_bigclass=' + hrefs[1].replace("'", "")+'&news_id='+hrefs[2].replace("'", "")})

    return (rt, bs)

def parse_xs_notice(html, tpname):
    bs = BeautifulSoup(html, 'lxml')
    noticeTitle = bs.find(id='ctl00_ContentPlaceHolder1_bt').get_text().strip()
    noticePubDate=bs.find(id='ctl00_ContentPlaceHolder1_pubTime').get_text().strip()
    noticeContent_html = bs.find('div', class_='Content')
    source='杭州市萧山区招投标管理信息网'
    #source = bs.find(id='ctl00_ContentPlaceHolder1_spanTitle').get_text().strip()
    #source =source[source.index('>')+1:].strip()
    typeName = tpname
    #print(source)
    # 去掉style标签
    [s.extract() for s in noticeContent_html('style')]
    keywords=bs.find(id='ctl00_ContentPlaceHolder1_nr').get_text().strip()
    # print(type(noticeContent_html))
    noticeContent = noticeContent_html.get_text()
    return {'noticeTitle': noticeTitle,
            'noticePubDate': noticePubDate,
            'source': source,
            'typeName': typeName,
            'noticeContent_html': str(noticeContent_html),
            'noticeContent': noticeContent,
            'keywords': keywords}


def xs_ztb():
    '''
        中心公告
    '''
    logger.info('开始处理萧山招投标信息网')
    print('开始处理萧山招投标信息网')
    # 萧山网站地址
    url = XS_MAIN_ZTB_LINK_REAL
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Host': 'www.xszbjyw.com',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cookie': 'ASP.NET_SessionId = jis0bwrvjlwgn355c1ujw555',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }
    index_pg = get_one_url_with_header(url,headers)
    bs = BeautifulSoup(index_pg, 'lxml')

    # 总页数
    MoreInfoList_Pager = bs.find("div", {"class": "RowPager"})
    newday  = bs.find_all("td", {"class": "DateColumn"})[0].get_text()
    print(newday)
    page_num = MoreInfoList_Pager.get_text().split('/')[1].split('页')[0].strip()
    print('总页数：%s' % page_num)
    logger.info('总页数：%s' % page_num)

    all_items = []

    # 处理隐藏参数
    hidden_tags ={
        '__VIEWSTATE': '',
        '__EVENTVALIDATION': '',
        'txtTile': '',
        'GridViewer1$ctl18$NumGoto': 1,
        'GridViewer1$ctl18$BtnGoto': 'Go',
        'ProTypeHid': ''}



    # 翻页
    for i in range(1, int(page_num)+1):
    #for i in range(2, 3):
        hidden_tags = update_hidden_tags(bs, hidden_tags, i)
        time.sleep(1)
        (a_index, page)=get_a_index(url, headers, hidden_tags)
        if a_index:
            all_items.extend(a_index)
        else:
            continue
    logger.info('共有记录条数：%s' % len(all_items))

    # 逐条处理
    for a_item in all_items:
        # 检查标题关键字
        title = a_item.get('title')
        id = a_item.get('id')
        white_key = False
        black_key = True
        for keyword in KEYWORDS:
            if keyword in title:
                white_key = True

        for keyword in BLACK_LIST:
            if keyword in title:
                black_key = False

        if not white_key or not black_key:
            logger.info('标题不在白名单或者存在黑名单:%s' % id)
            continue

            # 检查是否存在重复的通告
        if check_dup_record(a_item):
            logger.info('%s:%s已存在数据库中，忽略...' %
            (a_item.get('id'), a_item.get('title')))
            continue
        logger.info('新发现公告%s' % a_item.get('id'))
        # print(a_item.get('url'))
        #if  not a_item.get('url'):
            #print(a_item.get('url')+'---'+a_item.get('id'))
        notice_html = get_one_url_with_header(a_item.get('url'), headers)
        a_item.update(parse_xs_notice(notice_html, '中心动态'))

        a_item['districtName'] = '萧山区'

        if upsert_to_mongo({'id': a_item.get('id')}, a_item):
            logger.info('更新/插入[%s]成功' % a_item.get('id'))
    curr_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logger.info('结束处理开始处理萧山招投标信息网数据')
    #send_email(receiver=['huxiao_hz@citicbank.com', '16396355@qq.com', '8206741@163.com'],
    send_email(receiver=[ '8206741@163.com'],
               title=curr_time+'萧山招投标信息网发送情况', cont='<h1>今日萧山招投标信息网最新更新日期是{}</h1>'.format(newday))
if __name__ == "__main__":

    xs_ztb()

