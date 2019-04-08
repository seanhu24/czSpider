# -*- coding: utf-8 -*-

import logging
import requests
import json
import re
import schedule
import time

from logging.config import fileConfig
from urllib.parse import urlencode
from requests import RequestException
from math import ceil

from config import *
from db_utils import *


fileConfig('logging_config.ini')
logger = logging.getLogger('sLogger')


# TODO
# 1. 检查需要爬取的明细是否在数据库中
# 2. 增加爬取日志
# 3. 取数据库记录并发送后台

def merge_list(l1, l2, key):
    merged = {}
    for item in l1 + l2:
        if item[key] in merged:
            merged[item[key]].update(item)
        else:
            merged[item[key]] = item
    return [val for (_, val) in merged.items()]


def get_one_url(url):
    # logger.info('爬取url:' + url)
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            resp.encoding = 'utf-8'  # 解决中文问题
            return resp.text
        return None
    except RequestException:
        print('请求索引页出错')
        return None


def parse_key_count(html):
    data = json.loads(html)
    if data and data.get('successFlag') == True:
        return data.get('count')
    else:
        print('获得页面数失败')


def build_url(tp, **params):
    if tp == 'index':
        # http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?pageNo=1&pageSize=15&keyword=%E5%85%AC%E6%AC%BE&type=0&isExact=1&url=http%3A%2F%2Fnotice.zcy.gov.cn%2Fnew%2FglobalFullTextSearch
        if params.get('word') and params.get('pageno'):
            data = {
                'pageNo': params.get('pageno'),
                'pageSize': 15,
                'keyword': params.get('word'),
                'type': 0,
                'isExact': 0,
                'url': 'http://notice.zcy.gov.cn/new/globalFullTextSearch'
            }
            return SEARCH_LINK + urlencode(data)
        else:
            return None
    elif tp == 'notice':
        # http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?noticeId=2828520&url=http://notice.zcy.gov.cn/new/noticeDetail
        # link = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?'
        if params.get('notice_id'):
            data = {
                'noticeId': params.get('notice_id'),
                'url': 'http://notice.zcy.gov.cn/new/noticeDetail'
            }
            return SEARCH_LINK + urlencode(data)
        else:
            return None
    return None


def parse_one_page(html):
    if html:
        data = json.loads(html)
        if 'articles' in data.keys():
            for article in data.get('articles'):
                yield {
                    'id': int(article.get('id')),
                    'mainBidMenuName': article.get('mainBidMenuName'),
                    'title': re.sub(r'<[^>]+>', "", article.get('title'), re.S),
                    'projectCode': article.get('projectCode'),
                    'projectName': article.get('projectName'),
                    'districtName': article.get('districtName'),
                    'typeName': article.get('typeName'),
                    'keywords': re.sub(r'<[^>]+>', "", article.get('keywords'), re.S),
                    'url': article.get('url')
                }


def get_uniq_notice(notices):
    id_list = []
    new_notices = []
    for n in notices:
        if n.get('id') not in id_list:
            id_list.append(n.get('id'))
            new_notices.append(n)
    return new_notices


def parse_one_notice(html):
    if html:
        # print(html)
        data = json.loads(html)
        if 'noticeContent' in data.keys():
            yield {
                'id': data.get('id'),
                'noticeTitle': data.get('noticeTitle'),
                'noticePubDate': data.get('noticePubDate'),
                'noticeContent': tidy_notice_content(data.get('noticeContent')),
                'noticeContent_html': data.get('noticeContent')
            }
    return None


def tidy_notice_content(text):
    cleanr = re.compile('<(.*?)>', re.S)
    d1 = re.sub(cleanr, '', text)
    d2 = re.sub('&nbsp;', ' ', d1)
    cleanr2 = re.compile('^(table|th)(.*?);}', re.S)
    d3 = re.sub(cleanr2, '', d2)

    return ''.join(d3.splitlines())


def main():
    key_words = KEYWORDS
    urls = []
    notices = []  # 摘要
    details = []  # 详细信息

    for key_word in key_words:
        logger.info('搜索关键字:{}'.format(key_word))
        html = get_one_url(build_url(tp='index', pageno=1, word=key_word))
        rows = parse_key_count(html)
        pages = ceil(rows / 15)
        logger.info('得到记录:{0}条,{1}页'.format(rows, pages))

        # 翻页
        for pageno in range(1, pages + 1):
            url = build_url(tp='index', pageno=pageno, word=key_word)
            urls.append(url)

    logger.info('需要爬取索引页数量:' + str(len(urls)))

    for url in urls:
        index_html = get_one_url(url)
        notices.extend(list(parse_one_page(index_html)))
    logger.info('共得到notice:' + str(len(notices)))

    notices = get_uniq_notice(notices)
    logger.info('共得到不重复notice:' + str(len(notices)))

    part_notices = notices[0:5]

    # print(notices[0])
    for nts in notices:
        id = nts.get('id')
        logger.info('处理通告:' + str(id))
        if check_id_mongo({'id': id}):
            logger.info('已存在通告:' + str(id))
            # continue
        else:
            logger.info('新发现通告:' + str(id))
            notice_url = build_url(tp='notice', notice_id=id)
            notice_html = get_one_url(notice_url)
            notice_content = list(parse_one_notice(notice_html))
            details.append(list(notice_content)[0])

    full_notices = merge_list(notices, details, 'id')
    logger.info('合并后通告数:%d' % len(full_notices))

    for full_notice in full_notices:
        # print(full_notice.get('id'), len(full_notice))
        # 检查标题关键字是否在黑名单中
        title = full_notice.get('title')
        for bk in BLACK_LIST:
            if bk not in title:
                if upsert_to_mongo({'id': full_notice.get('id')}, full_notice):
                    logger.info('更新/插入[%s]成功' % full_notice.get('id'))
            else:
                logger.info('标题%s包含关键字%s,忽略' % (title, bk))


schedule.every().day.at(FIRE_TIME1).do(main)
schedule.every().day.at(FIRE_TIME2).do(main)

while True:
    schedule.run_pending()
    # logger.info('tick tack...')
    time.sleep(1)

if __name__ == "__main__":
    main()
    # l1 = [{'id': 1, 'name': 'huhu'}, {'id': 2, 'name': 'lll'}]
    # l2 = [{'id': 1, 'age': 22}, {'id': 3, 'age': 23}]
    # l3 = merge_list(l1, l2, 'id')
    # print(l3)
