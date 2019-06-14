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


DOMAIN_URL = 'http://ggb.sx.gov.cn'


def update_hidden_tags(soup, tags, page_no):
    tags['__VIEWSTATE'] = soup.find(id='__VIEWSTATE')['value']
    tags['__VIEWSTATEGENERATOR'] = soup.find(
        id='__VIEWSTATEGENERATOR')['value']
    tags['__EVENTARGUMENT'] = str(page_no)

    return tags


def get_a_index(url, tags):
    # print(url)
    logger.info('抓取第%s页' % tags['__EVENTARGUMENT'])
    # url = SX_MAIN_ZB_LINK

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


def parse_sx_notice_v2(html, tpname):
    bs = BeautifulSoup(html, 'lxml')
    noticeTitle = bs.find('td', class_='title').get_text().strip()

    noticeContent_html = str(bs.find('td', class_='bt_content'))
    noticeContent = noticeContent_html.get_text()
    return {'noticeTitle': noticeTitle,
            # 'source': source,
            'typeName': tpname,
            'noticeContent_html': str(noticeContent_html),
            'noticeContent': noticeContent
            }
    # print(noticeContent)
    # <td width="30%" align="right">发布日期：2019-06-10</td>


def get_uid():
    return '4685909'


def get_total_records(inStr=None):
    # print(inStr)
    pattern = re.compile(r'.*?totalRecord:(.*?),.*?')
    matchObj = pattern.findall(inStr)
    if matchObj[1]:
        return matchObj[1]

    return None


def get_records(html=None):
    links = []
    # print(html)
    bs = BeautifulSoup(html, 'lxml')
    uls = bs.find_all('ul', class_='ajax-list')
    for ul in uls:
        # print(ul)
        a = ul.find('a')
        dt = ul.find('span').get_text().strip()[1:-1]
        id = a['href'].split('/')[-1].split('.')[0]
        # print(dt)
        links.append(
            {'id': id, 'url': DOMAIN_URL + a['href'], 'title': a.get_text(), 'noticePubDate': dt})
    return links


def sxbj_zb_v2():

    logger.info('开始处理绍兴公共资源交易网')

    for sl in SX_MAIN_SEARCH_LINK:

        url = sl[0]
        tpname = sl[1]
        columnid = sl[2]
        logger.info('处理 {}'.format(tpname))

        index_pg = get_one_url(url)
        # print(index_pg)
        bs = BeautifulSoup(index_pg, 'lxml')

        all_notices = []
        all_links = []  # 所有链接
        # 总页数
        # uid
        ajaxlb = bs.find('div', {'class': 'ajaxlb'})
        # print(ajaxlb.get_text())
        total_records = int(get_total_records(ajaxlb.get_text()))
        if not total_records:
            logger.info('can not get total records...')
            return
        total_pages = math.ceil(total_records / 120)
        logger.info('共有记录 {} 条, 分为 {} 页'.format(total_records, total_pages))

        uid = get_uid()
        # for pageNum in range(1, 20):
        for pageNum in range(total_pages):
            logger.info('爬取第 {} 页'.format(pageNum + 1))
            startrecord = pageNum * 120 + 1
            endrecord = (pageNum + 1) * 120
            if endrecord > total_records:
                endrecord = total_records
            logger.info('取第 {} 到 {} 条记录'.format(startrecord, endrecord))
            # full_url = '{}?uid={}&pageNum={}'.format(url, uid, pageNum)

            data = {'col': 1, 'appid': '1', 'webid': 3003, 'path': '/', 'columnid': columnid,
                    'sourceContentType': 1, 'unitid': uid, 'webname': '绍兴公共资源交易网', 'permissiontype': 0}

            payload = {'startrecord': startrecord,
                       'endrecord': endrecord, 'perpage': 40}

            a_index = post_one_url_with_payload(
                SX_MAIN_DATA_PROXY, payload=payload, data=data)
            # logger.info(a_index)
            links = get_records(a_index)
            all_links.extend(links)

            # logger.info(links)

            # logger.info(full_url)
            # a_page = get_by_PhantomJS(full_url)
            # links = get_records(a_page)
            # logger.info(links)
            # all_links.extend(links)
        logger.info('采集到 {} 条索引'.format(len(all_links)))
        cleaned_links = filter_by_keyword(all_links)
        logger.info('过滤关键字后得到 {} 条'.format(len(cleaned_links)))
        # logger.info('共收集到信息 %d 条' % len(cleaned_links))
        # print(cleaned_links)
        for l in cleaned_links:
            if check_dup_record(l):
                logger.info('%s:%s已存在数据库中，忽略...' %
                            (l.get('id'), l.get('title')))
                continue

            logger.info('新发现公告%s' % l.get('id'))
            a_notice = get_one_url(l['url'])
            a_notice_dict = parse_sx_notice_v2(a_notice, tpname=tpname)
            a_notice_dict.update(l)

            # a_notice_dict['id'] = l['url'].split('/')[-1].split('.')[0]

            source = '绍兴公共资源交易网'
            districtName = '绍兴市本级'
            keywords = a_notice_dict['noticeContent'][:100]
            a_notice_dict['source'] = source
            a_notice_dict['districtName'] = districtName
            a_notice_dict['keywords'] = keywords

            if upsert_to_mongo({'id': a_notice_dict.get('id')}, a_notice_dict):
                logger.info('更新/插入[%s]成功' % a_notice_dict.get('id'))
            # print(a_notice_dict)
            # all_notices.append(a_notice_dict)

    logger.info('结束处理绍兴公共资源交易网')


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
        (a_index, page) = get_a_index(url, hidden_tags)
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
        (a_index, page) = get_a_index(url, hidden_tags)
        if a_index:
            all_items.extend(a_index)
        else:
            continue

    logger.info('共有记录条数：%s' % len(all_items))

    # 逐条处理
    for a_item in all_items:
        # 检查标题关键字
        title = a_item.get('title')
        # print(title)
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
        notice_html = get_one_url(a_item.get('url'))

        a_item.update(parse_sx_notice(notice_html, '中标公示'))

        a_item['districtName'] = '绍兴市本级'

        if upsert_to_mongo({'id': a_item.get('id')}, a_item):
            logger.info('更新/插入[%s]成功' % a_item.get('id'))

    logger.info('结束处理绍兴公共资源交易网中标数据')


if __name__ == "__main__":
    # sxbj_zb()
    # sxbj_zb2()
    sxbj_zb_v2()
    # html = get_one_url(
    #     'http://ggb.sx.gov.cn/art/2019/6/10/art_1518878_34544831.html')
    # parse_sx_notice_v2(html=html, tpname='测试')
    # get_records(html)

    # aa = '<ul class="ajax-list"> <li> <a href="/art/2019/6/12/art_1518878_34598612.html" target="_blank">绍兴市制水有限公司防雷系统优化改造项目（视频监控部分）招标公告</a> <span>[2019-06-12]</span> </li></ul>'
    # bs = BeautifulSoup(aa, 'lxml')
    # a = bs.find('a')
    # l = bs.find('li')
    # s = bs.find('span')
    # print(a)
    # print(l)
    # print(s)
    # a={'a':1,'b':2}
    # b={'c':3,'d':4}
    # a.update(b)
    # print(a)
