# -*- coding: utf-8 -*-

import logging
import requests
import json
import re
import schedule
import time
import math
from datetime import datetime
import time

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
logger = logging.getLogger('app_ls')


DOMAIN = 'http://www.lssggzy.com'


def parse_ls_notice(html=None):
    bs = BeautifulSoup(html, 'lxml')
    noticeTitle = bs.find(
        'td', class_='s-mid-content-title').get_text().strip()

    try:
        noticePubDate_t = bs.find(
            'p', class_='s-mid-content-date').get_text().strip().split('：')[1].strip()
    except IndexError as e:
        logger.error('获取内容失败', e)
        return None
    noticePubDate = datetime.strptime(
        noticePubDate_t, '%Y/%m/%d').strftime('%Y-%m-%d')

    content = bs.find('td', {'id': 'TDContent', 'class': 'infodetail'})

    return {'noticePubDate': noticePubDate, 'noticeTitle': noticeTitle, 'noticeContent_html': str(content), 'noticeContent': content.get_text(), 'keywords': content.get_text()[:100]}


def get_page_links(html=None):
    ret_links = []

    bs = BeautifulSoup(html, 'lxml')
    try:
        links = bs.find('div', class_='contentall').find_all(
            'a', {'target': '_blank'})
    except AttributeError as e:
        logger.error(e)
        # logger.info(html)
        return None

    for l in links:
        # print(l)
        ret_links.append(
            {'id': l['href'].split('?')[1].split('&')[0].split('=')[1], 'title': l['title'], 'url': DOMAIN + l['href']})

    return ret_links
    # print(main_content)


def zb_ls():
    logger.info('开始处理丽水市公共资源交易网')

    all_links = []
    cleaned_links = []

    for region in LS_MAIN_SEARCH_LINK:
        index_url = region[0]
        districtName = region[1]
        tpname = region[2]
        logger.info('处理 {} 地区 {}'.format(districtName, tpname))

        # print(index_url)
        index_html = get_one_url_gbk(index_url)
        pg_num = get_page_num(index_html)
        if not pg_num:
            logger.info('无记录...')
            continue
        page_num = int(pg_num)
        logger.info('需要提取页面数 {}'.format(page_num))

        for Paging in range(1, page_num + 1):
            logger.info('第 {} 页'.format(Paging))
            # payload = {'Paging': Paging}
            page_html = get_one_url_gbk(
                index_url + '?Paging=' + str(Paging))

            links = get_page_links(page_html)
            if not links:
                logger.info('没有收集到链接 {}'.format(
                    index_url + '?Paging=' + str(Paging)))
                time.sleep(3)
                logger.info('再次尝试第 {} 页'.format(Paging))
                # payload = {'Paging': Paging}
                page_html = get_one_url_gbk(
                    index_url + '?Paging=' + str(Paging))

                links = get_page_links(page_html)
                if not links:
                    logger.info('再次没有收集到链接 {}'.format(
                        index_url + '?Paging=' + str(Paging)))
                    continue

            for l in links:
                l['districtName'] = districtName
                l['typeName'] = tpname
            logger.info('得到 {} 条链接'.format(len(links)))
            all_links.extend(links)

    logger.info('共得到链接 {} 条'.format(len(all_links)))
    cleaned_links = filter_by_keyword(all_links)
    logger.info('关键字过滤后得到 {} 条'.format(len(cleaned_links)))

    # print(cleaned_links)

    for l in cleaned_links:
        if check_dup_record(l):
            logger.info('%s:%s已存在数据库中，忽略...' %
                        (l.get('id'), l.get('title')))
            continue

        logger.info('新发现公告%s' % l.get('id'))
        # print(l.get('url'))
        notice_html = get_one_url_gbk(l.get('url'))
        notice_dict = parse_ls_notice(notice_html)
        if notice_dict:
            l.update(notice_dict)
            l['source'] = '丽水市公共资源交易网'

            # # print(l)
            if upsert_to_mongo({'id': l.get('id')}, l):
                logger.info('更新/插入[%s]成功' % l.get('id'))

    logger.info('结束处理丽水市公共资源交易网')


if __name__ == "__main__":

    # url = 'http://www.lssggzy.com/lsweb/jyxx/071005/071005001/071005001001/'
    # pay = {'Paging': 2}

    # html = get_one_url_with_payload_gbk(url, payload=pay)
    # # print(html)
    # rt = get_page_links(html)
    # print(rt)

    # url = 'http://www.lssggzy.com/lsweb/infodetail/?infoid=ab0e2e3c-7911-4492-923e-8b7819f044a4&categoryNum=071005003009'

    # html = get_one_url_gbk(url)

    # parse_ls_notice(html)
    zb_ls()
