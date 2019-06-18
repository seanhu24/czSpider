# -*- coding: utf-8 -*-

import logging
import requests
import json
import re
import schedule
import time
from datetime import datetime

from logging.config import fileConfig
from urllib.parse import urlencode, urlparse, parse_qs, quote
from urllib import request
from requests import RequestException
from math import ceil
from bs4 import BeautifulSoup

from config import *
from db_utils import *
from request_utils import *


def jxbj():
    # 从查询页面开始
    search_url = JX_GGZY_SEARCH_LINK
    site = '嘉兴市公共资源交易中心'

    logger.info('开始处理%s' % site)

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'www.jxzbtb.cn',
        'Origin': 'http://www.jxzbtb.cn',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'Referer': 'http://www.jxzbtb.cn/search/fullsearch.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    payload_template = dict(
        token='',
        pn=0,
        rn=10000,
        sdt='',
        edt='',
        # wd='存款',
        inc_wd='',
        exc_wd='',
        # fields='title;content',
        fields='title',
        cnum='',
        sort='{"showdate":0}',
        ssort='title',
        cl=500,
        terminal='',
        condition=None,
        time=None,
        # highlights='title;content',
        highlights=None,
        statistics=None,
        unionCondition=None,
        accuracy='',
        noParticiple='1',
        searchRange=None
    )

    ret_list = []
    ret_list_tidy = []
    ret_id_set = set()

    for kw in KEYWORDS:
        payload = payload_template
        logger.info('查询关键字%s' % kw)
        payload['wd'] = kw

        payload_json = json.dumps(payload)
        resp = post_one_url(search_url, payload_json)

        if resp:
            resp_dict = json.loads(resp)
            # print(resp_dict)
            result = resp_dict.get('result')
            totalcount = result.get('totalcount')
            logger.info('找到相关结果%d个' % totalcount)
            records = result.get('records')
            ret_list.extend(records)

        else:
            logger.info("查询关键字%s失败" % kw)

    logger.info('共得到招投标信息%d条' % len(ret_list))

    for a_item in ret_list:
        id = a_item.get('id')
        title = a_item.get('title')
        districtName = '嘉兴市本级'
        keywords = a_item.get('content')
        noticePubDate = a_item.get('infodate')
        url = JX_GGZY_MAIN_LINK + a_item.get('linkurl')

        if '招标' in title:
            typeName = '招标公告'
        elif '中标' in title:
            typeName = '中标公告'
        else:
            typeName = '其他'

        if id not in ret_id_set:
            ret_id_set.add(id)
            ret_list_tidy.append({'id': id,
                                  'title': title,
                                  'districtName': districtName,
                                  'keywords': keywords,
                                  'noticePubDate': noticePubDate,
                                  'url': url,
                                  'typeName': typeName})

    logger.info('得到不重复信息%d条' % len(ret_list_tidy))

    for notice in ret_list_tidy:
        id = notice.get('id')
        url = notice.get('url')
        # print(url)

        logger.info('处理通告%s' % notice.get('id'))
        # print(url)
        noticeContent_html = get_one_url(url)
        if not noticeContent_html:
            logger.info('{} 不能访问'.format(url))
            continue
        bs = BeautifulSoup(noticeContent_html, 'lxml')
        notice['noticeTitle'] = bs.find(class_='infoContentTitle').get_text()
        # print(notice['noticeTitle'])
        sublink_bs = bs.find(
            'a', attrs={'href': '/jygg/subpage.html'})
        if not sublink_bs:
            sublink = ''
        else:
            sublink = sublink_bs.get_text()

        if sublink != '交易公告':
            logger.info('%s不是交易公告，忽略' % id)
            continue

        notice['noticeContent_html'] = noticeContent_html
        noticeContent = bs.find(class_='ewb-info-list')

        # 删除无用的标签
        [s.extract() for s in noticeContent('script')]
        [s.extract() for s in noticeContent(class_='info-sources')]
        notice['noticeContent'] = noticeContent.get_text()

        notice['source'] = site

        # 检查是否存在重复的通告
        a_rec = {'source': notice.get('source'), 'title': notice.get('title')}
        if check_dup_record(a_rec):
            logger.info('%s:%s已存在数据库中，忽略...' %
                        (a_rec.get('id'), a_rec.get('title')))
            continue

        if upsert_to_mongo({'id': id}, notice):
            logger.info('更新%s成功' % id)

    logger.info('结束处理%s' % site)
    # return ret_list_tidy


if __name__ == "__main__":
    jxbj()

    # print(len(ret))
    # for r in ret:
    #     print(r.get('id'), r.get('title'), r.get('url'), r.get('noticeTitle'))
    # # url='http://www.jxzbtb.cn/search/fullsearch.html?wd=存款'
