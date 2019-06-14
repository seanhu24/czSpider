# -*- coding: utf-8 -*-

import logging
import requests
import json
import re
import schedule
import time
import math
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

fileConfig('logging_config.ini')
logger = logging.getLogger('sLogger')


def parse_hz_notice(html=None):
    bs = BeautifulSoup(html, 'lxml')
    noticeTitle = bs.find('td', {'id': 'tdTitle'}).find(
        'font', class_="titlestyle").get_text()
    noticeContent_html = bs.find(
        'td', {'id': 'TDContent', 'class': 'infodetail'})
    noticeContent = remove_header_comment(noticeContent_html.get_text())
    keywords = noticeContent[:100]
    return {'noticeTitle': noticeTitle,
            'noticeContent_html': str(noticeContent_html),
            'noticeContent': noticeContent,
            'keywords': keywords}


def get_page_num(html=None):
    bs = BeautifulSoup(html, 'lxml')
    pg = bs.find('td', class_='huifont')
    # print(pg.get_text())
    # print(pg.get_text().split('/'))
    if pg:
        return pg.get_text().split('/')[1]
    return None


def get_links(html=None):
    ret_links = []
    bs = BeautifulSoup(html, 'lxml')
    links = bs.find_all('td', class_='moreinfoCss')
    # print(links)
    for link in links:
        ret = {}
        link_a = link.find_all('a')[0]
        # print(link_a)
        dt = link.find_next_sibling().find_next_sibling().find('font').get_text()
        ret['noticePubDate'] = dt
        ret['title'] = link_a['title']
        ret['url'] = 'http://ggzy.huzhou.gov.cn/' + link_a['href']
        pattern = re.compile(r'.*InfoID=(.*?)&CategoryNum.*')
        matchObj = pattern.findall(link_a['href'])
        # print(matchObj)
        if matchObj:
            ret['id'] = matchObj[0]

        ret_links.append(ret)

    return ret_links


def hz_zb():
    logger.info('开始处理湖州公共资源交易网')

    all_links = []
    cleaned_links = []

    # 首页
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Host': 'ggzy.huzhou.gov.cn',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }

    for sl in HZ_MAIN_SEARCH_LINK:
        search_link = sl[0]
        tpname = sl[1]

        logger.info('开始查找{}'.format(tpname))
        index_html = get_one_url_with_header(search_link, headers=headers)
        total_page_no = int(get_page_num(index_html))

        if not total_page_no:
            logger.info('无法获得总页数...')
            return

        logger.info('总共得到 {} 页'.format(total_page_no))

        # 翻页
        ref_link = search_link
        for Paging in range(1, total_page_no + 1):
            full_url = search_link + '?Paging=' + str(Paging)
            # print(full_url)
            logger.info('获取第 {} 页'.format(Paging))
            headers['Referer'] = ref_link
            index_html = get_one_url_with_header(full_url, headers=headers)
            links = get_links(index_html)
            all_links.extend(links)

    cleaned_links = filter_by_keyword(all_links)

    for l in cleaned_links:
        if check_dup_record(l):
            logger.info('%s:%s已存在数据库中，忽略...' %
                        (l.get('id'), l.get('title')))
            continue

        logger.info('新发现公告%s' % l.get('id'))
        # print(l.get('url'))
        notice_html = get_one_url_with_header(l.get('url'), headers=headers)
        notice_dict = parse_hz_notice(notice_html)

        l.update(notice_dict)
        l['source'] = '湖州市公共资源交易信息网'
        l['typeName'] = tpname
        l['districtName'] = '湖州市本级'

        print(l)
        if upsert_to_mongo({'id': l.get('id')}, l):
            logger.info('更新/插入[%s]成功' % l.get('id'))
    logger.info('结束处理湖州公共资源交易网')


if __name__ == "__main__":
    hz_zb()
