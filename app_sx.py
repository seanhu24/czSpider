# -*- coding: utf-8 -*-

import logging
import requests
import json
import re
import schedule
import time
from datetime import datetime

from logging.config import fileConfig
from urllib.parse import urlencode, urlparse, parse_qs
from requests import RequestException
from math import ceil
from bs4 import BeautifulSoup

from config import *
from db_utils import *
from request_utils import *


fileConfig('logging_config.ini')
logger = logging.getLogger('sLogger')


def update_hidden_tags(soup, tags, page_no):
    tags['__VIEWSTATE'] = soup.find(id='__VIEWSTATE')['value']
    tags['__VIEWSTATEGENERATOR'] = soup.find(
        id='__VIEWSTATEGENERATOR')['value']
    tags['__EVENTARGUMENT'] = str(page_no)

    return tags


def get_a_index(tags):
    logger.info('抓取第%s页' % tags['__EVENTARGUMENT'])
    url = SX_MAIN_ZB_LINK

    rt = []

    # a_page = requests.post(url, data=tags)
    # a_page.encoding = 'UTF-8'
    rt_page = post_one_url(url, tags)
    if rt_page:
        bs = BeautifulSoup(rt_page, 'lxml')
    else:
        logger.error('拿不到页面，跳过...')
        return (None, None)
    # print(a_page.text)

    notecies = bs.find(id='MoreInfoList1_tdcontent').find_all('a')
    for notice in notecies:
        href = notice['href']
        title = notice['title']
        # print('#标题%s', title)
        # logger.debug('#标题%s', title)
        parsed_href = urlparse(href)
        # print(parse_qs(parsed_href.query)['InfoID'][0])
        id = parse_qs(parsed_href.query)['InfoID'][0]
        rt.append({'id': id, 'title': title,
                   'url': 'http://www.sxztb.gov.cn:33660' + href})

    return (rt, bs)


def parse_sx_notice(html, tpname):
    bs = BeautifulSoup(html, 'lxml')
    noticeTitle = bs.find(id='tdTitle').find('font').get_text().strip()
    noticePubDate_tmp = bs.find(id='tdTitle').find_all('font')[
        1].get_text().strip()
    source = bs.find('title').get_text()
    typeName = tpname

    noticePubDate = datetime.strptime(re.findall(
        '信息时间：(.+?)阅读次数', noticePubDate_tmp, re.S)[0].strip(), '%Y/%m/%d').strftime('%Y-%m-%d')
    noticeContent_html = bs.find(id='TDContent')

    # 去掉style标签
    [s.extract() for s in noticeContent_html('style')]

    # print(type(noticeContent_html))
    noticeContent = noticeContent_html.get_text()
    # print(noticePubDate)

    return {'noticeTitle': noticeTitle,
            'noticePubDate': noticePubDate,
            'source': source,
            'typeName': typeName,
            'noticeContent_html': str(noticeContent_html),
            'noticeContent': noticeContent}


def sxbj_zb():
    '''
        招标
    '''
    logger.info('开始处理绍兴公共资源交易网招标数据')
    # 绍兴本级招标
    url = SX_MAIN_ZB_LINK
    index_pg = get_one_url(url)
    bs = BeautifulSoup(index_pg, 'lxml')

    # 总页数
    MoreInfoList1_Pager = bs.find("div", {"id": "MoreInfoList1_Pager"})
    page_num = MoreInfoList1_Pager.select('td font b')[1].get_text()
    logger.info('总页数：%s' % page_num)

    all_items = []

    # 处理隐藏参数
    hidden_tags = dict(
        __VIEWSTATE='',
        __VIEWSTATEGENERATOR='168B6978',
        __EVENTTARGET='MoreInfoList1$Pager',
        __EVENTARGUMENT='',
        __VIEWSTATEENCRYPTED='',
    )

    resp = requests.get(url)
    page = BeautifulSoup(resp.text, 'lxml')

    # 翻页
    for i in range(1, int(page_num) + 1):
        hidden_tags = update_hidden_tags(page, hidden_tags, i)
        time.sleep(1)
        (a_index, page) = get_a_index(hidden_tags)
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
        if check_id_mongo(a_item):
            logger.info('%s:%s已存在数据库中，忽略...' %
                        (a_item.get('id'), a_item.get('title')))
            continue

        logger.info('新发现公告%s' % a_item.get('id'))
        notice_html = get_one_url(a_item.get('url'))

        a_item.update(parse_sx_notice(notice_html, '招标（交易）公告'))

        a_item['districtName'] = '绍兴市本级'

        if upsert_to_mongo({'id': a_item.get('id')}, a_item):
            logger.info('更新/插入[%s]成功' % a_item.get('id'))

    logger.info('结束处理绍兴公共资源交易网招标数据')


def sxbj_zb2():
    '''
        中标
    '''
    logger.info('开始处理绍兴公共资源交易网中标数据')
    # 绍兴本级招标
    url = SX_MAIN_ZB2_LINK
    index_pg = get_one_url(url)
    bs = BeautifulSoup(index_pg, 'lxml')

    # 总页数
    MoreInfoList1_Pager = bs.find("div", {"id": "MoreInfoList1_Pager"})
    page_num = MoreInfoList1_Pager.select('td font b')[1].get_text()
    logger.info('总页数：%s' % page_num)

    all_items = []

    # 处理隐藏参数
    hidden_tags = dict(
        __VIEWSTATE='',
        __VIEWSTATEGENERATOR='C57B8F78',
        __EVENTTARGET='MoreInfoList1$Pager',
        __EVENTARGUMENT='',
        __VIEWSTATEENCRYPTED='',
    )

    resp = requests.get(url)
    page = BeautifulSoup(resp.text, 'lxml')

    # 翻页
    for i in range(1, int(page_num) + 1):
        hidden_tags = update_hidden_tags(page, hidden_tags, i)
        time.sleep(1)
        (a_index, page) = get_a_index(hidden_tags)
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
        if check_id_mongo(a_item):
            logger.info('%s:%s已存在数据库中，忽略...' %
                        (a_item.get('id'), a_item.get('title')))
            continue

        logger.info('新发现公告%s' % a_item.get('id'))
        notice_html = get_one_url(a_item.get('url'))

        a_item.update(parse_sx_notice(notice_html, '中标公示'))

        a_item['districtName'] = '绍兴市本级'

        if upsert_to_mongo({'id': a_item.get('id')}, a_item):
            logger.info('更新/插入[%s]成功' % a_item.get('id'))

    logger.info('结束处理绍兴公共资源交易网中标数据')


if __name__ == "__main__":
    sxbj_zb()
    # sxbj_zb2()
