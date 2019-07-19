# -*- coding: utf-8 -*-

from urllib.parse import urlencode, urlparse, parse_qs
from logging.config import fileConfig
import requests
import json
import logging
from config import *
from common_utils import *
from bs4 import BeautifulSoup
import re
from db_utils import *
from request_utils import *
from math import ceil
import datetime


class zjcg():

    def __init__(self):
        fileConfig('logging_config.ini')
        self.domain = 'http://www.zjzfcg.gov.cn/'
        self.search_path = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?'
        self.logger = logging.getLogger('zjcg_logger')
        self.logger.info('浙江省采购网开始...')

        self.zj_session = requests.session()
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}

        self.kws = KEYWORDS
        self.source = '浙江政府采购网'
        # 采购公告 > 非政府采购公告
        # self.tps = {'公款竞争性存放招标公告': '10002', '公款竞争性存放更正公告': '10003',
        #             '公款竞争性存放结果公告': '10004'}

    def get_main(self):
        self.logger.info('访问首页获取cookies')
        main_page = 'http://www.zjzfcg.gov.cn/'
        resp = self.zj_session.get(main_page, headers=self.header)
        return resp.text

    def do_get(self, url):
        # self.logger.info('爬取url:' + url)
        retry = 1
        success = False
        while not success:
            try:
                resp = self.zj_session.get(url, headers=self.header)
                success = True
                if resp.status_code == 200:
                    resp.encoding = 'utf-8'  # 解决中文问题
                    return resp.text
                return None
            except:
                self.logger.error('请求索引页出错')
                for i in range(1, retry + 1):
                    wait = i * 3
                    self.logger.info('等待%d秒' % wait)
                    time.sleep(wait)
                return None

    def get_a_index(self, kw=None, pageNo=None):
        '''
        http://www.zjzfcg.gov.cn/innerUsed_fullTextSearch/index.html?m=1&k=%E5%AD%98%E6%AC%BE&exact=0
        '''
        para = {
            'pageSize': 15,
            'pageNo': pageNo,
            'type': 0,
            'keyword': kw,
            'isExact': 0,
            'url': 'http://notice.zcygov.cn/new/globalFullTextSearch'
        }

        full_url = self.search_path + urlencode(para)

        res = self.do_get(url=full_url)
        res_json = json.loads(res)

        return res_json

    def get_a_detail(self, noticeId=None):
        para = {
            'noticeId': noticeId,
            'url': 'http://notice.zcygov.cn/new/noticeDetail'
        }

        full_url = self.search_path + urlencode(para)

        res = self.do_get(url=full_url)
        res_json = json.loads(res)

        return res_json

    def get_uniq_notice(self, notices):
        id_list = []
        new_notices = []
        for n in notices:
            if n.get('id') not in id_list:
                id_list.append(n.get('id'))
                new_notices.append(n)
        return new_notices

    # def parse_one_notice(self, html=None):
    #     bs = BeautifulSoup(html, 'lxml')
    #     noticePubDate = bs.find('p', class_='detail-info cggg')
    #     return {'noticePubDate': noticePubDate}

        # <p class="detail-info cggg"><span>发布时间：2016-12-16</span><span class="skanCount">浏览次数：70</span></p>

    def main(self):
        r = self.get_main()

        full_notices = []
        full_notices_uniq = []
        # 关键字
        for kw in self.kws:
            logger.info('查询 {}'.format(kw))
            ret = self.get_a_index(kw=kw, pageNo=1)
            # 获取记录数
            realCount = ret.get('realCount')
            logger.info('获得记录数 {}'.format(realCount))
            if realCount == 0:
                logger.info('0条记录，跳过')
                continue
            pg = ceil(realCount / 15)
            for pageNo in range(1, pg + 1):
                # logger.info('第 {} 页'.format(pageNo))
                ret = self.get_a_index(kw=kw, pageNo=pageNo)
                articles = ret.get('articles')
                logger.info('第 {} 页,有记录 {} 条'.format(pageNo, len(articles)))
                full_notices.extend(articles)
        logger.info('共获取记录 {} 条'.format(len(full_notices)))

        # 去除重复记录
        full_notices_uniq = self.get_uniq_notice(notices=full_notices)
        logger.info('得到不重复记录 {} 条'.format(len(full_notices_uniq)))

        # 逐个处理， 提取时间和内容, 去除标记， noticeContent,noticeContent_html,noticePubDate,noticeTitle
        # 按照标题判断是否入库
        for notice in full_notices_uniq:
            id = notice.get('id')
            title = tidy_notice_content(notice.get('title'))
            notice['title'] = title
            url = notice.get('url')
            keywords = tidy_notice_content(notice.get('keywords'))
            notice['keywords'] = keywords
            logger.info('处理 {} {} {}'.format(id, title, url))
            if check_id_mongo(notice):
                logger.info('已存在通告: {} 忽略'.format(id))
                continue

            logger.info('获取通告: {} 详细信息'.format(id))

            notice_detail = self.get_a_detail(noticeId=id)
            # logger.info(notice_detail)
            notice['noticePubDate'] = notice_detail.get('noticePubDate')[:10]
            notice['noticeTitle'] = notice_detail.get('noticeTitle')
            notice_html = notice_detail.get('noticeContent')
            bs = BeautifulSoup(notice_html, 'html.parser')
            notice['noticeContent'] = bs.get_text()
            notice['noticeContent_html'] = notice_html

        # 检查标题黑名单,并存入数据库
        # for notice in full_notices_uniq:
        #     # logger.info(notice)
        #     title = notice.get('title')
        #     id = notice.get('id')

            if check_title_black_list(title=title):
                logger.info('{} {} 检查到黑名单关键字 {}, 忽略'.format(id, title, kw))
                continue
            else:
                logger.info('开始插入 {} {}'.format(id, title))
                notice['source'] = self.source
                if upsert_to_mongo({'id': id}, notice):
                    logger.info('插入 {} {} 成功'.format(id, title))

            # for kw in BLACK_LIST:
            #     if kw in title:
            #         logger.info('{} {} 检查到黑名单关键字 {}, 忽略'.format(id, title, kw))
            #         break
            #     else:
            #         logger.info('开始插入 {} {}'.format(id, title))
            #         notice['source'] = self.source
            #         if upsert_to_mongo({'id': id}, notice):
            #             logger.info('插入 {} {} 成功'.format(id, title))
            #         break

        self.logger.info('浙江省采购网结束...')

    def test(self):
        # url = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?noticeId=10247&url=http%3A%2F%2Fnotice.zcygov.cn%2Fnew%2FnoticeDetail'
        # html = self.do_get(url=url)
        # # rt = self.parse_one_notice(html=html)
        # # logger.info(html)
        # notice_html = html.get('noticeContent')
        # bs = BeautifulSoup(notice_html, 'lxml')

        id = '10247'
        rt = self.get_a_detail(noticeId=id)
        # logger.info(type(rt.get('noticeContent')))
        bs = BeautifulSoup(rt.get('noticeContent'), 'html.parser')
        logger.info(bs.get_text())

        # tt = self.get_a_index(kw='存款', pageNo=1)
        # logger.info(tt)

        # for i in range(1, 7):
        #     self.get_a_index(kw='存款', pageNo=i)

        # zjcg = zjcg()

        # para = {
        #     'pageSize': 15,
        #     'pageNo': 2,
        #     'sourceAnnouncementType': '10002',
        #     'keyword': '存款',
        #     'url': 'http://notice.zcygov.cn/new/noticeSearch'
        # }

        # full_url = self.search_path + urlencode(para)
        # logger.info(full_url)
        # res = self.do_get(url=full_url)
        # # logger.info(res)
        # res_json = json.loads(res)
        # realCount = res_json.get('realCount')
        # logger.info(realCount)
        # articles = res_json.get('articles')
        # for a in articles:
        #     logger.info(a.get('id'), a.get('title'))
if __name__ == "__main__":
    zjcg = zjcg()
    zjcg.main()
    # zjcg.test()

    # 重新配置地区
    # 胡啸 ['浙江省','浙江省省本级',...]
