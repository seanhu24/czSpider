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


class zjs():
    def __init__(self):
        fileConfig('logging_config.ini')
        self.domain = 'http://zjpubservice.zjzwfw.gov.cn'
        self.logger = logging.getLogger('app_zj')
        self.logger.info('浙江省级开始...')

        self.zj_session = requests.session()
        self.header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
        self.main_url = self.domain + '/fulltextsearch/rest/getfulltextdata?'
        self.kws = KEYWORDS
        self.max_rownum = 10000

        self.source = '浙江省公共资源交易服务平台'

        self.rmk1 = {'采购公告': '002002001', '中标成交公告': '002002002',
                     '交易公告': '002005001', '交易结果': '002005002'}

    def get_main(self):
        self.logger.info('访问首页获取cookies')

        main_page = self.domain + '/index.html'
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

    def get_key_by_value(self, t_d=None, t_v=None):
        for k, v in t_d.items():
            if v == t_v:
                return k

    def format_notice(self, notice=None):
        new_notice = dict()

        # print(notice)
        title = tidy_notice_content(notice.get('title'))

        for bk in BLACK_LIST:
            if bk in title:
                self.logger.info('{} 含有关键字 {} , 忽略'.format(title, bk))
                return

        new_notice['title'] = title
        new_notice['noticeTitle'] = title
        new_notice['noticePubDate'] = notice.get('date')
        new_notice['id'] = notice.get('guid')
        new_notice['districtName'] = notice.get('remark5')
        new_notice['keywords'] = tidy_notice_content(notice.get('content'))
        new_notice['link'] = notice.get('link')
        new_notice['source'] = self.source
        new_notice['typeName'] = self.get_key_by_value(
            self.rmk1, notice.get('remark1'))
        new_notice['remark5'] = notice.get('remark5')
        new_notice['remark4'] = notice.get('remark4')
        # self.logger.debug(notice.get('guid'), notice.get('remark1'), self.get_key_by_value(
        #     self.rmk1, notice.get('remark1')))

        return new_notice

    def extract_info(self, info=None):
        info_json = json.loads(info)

        result = info_json.get('result')
        totalcount = result.get('totalcount')
        records = result.get('records')
        # print(result)
        self.logger.info('获得记录 {} 条'.format(totalcount))
        return records
        # for record in records:
        #     yield record
        # print(info_json)

    def search_kw(self, wd=None, rmk1=None, pn=None, rn=None):
        if not pn:
            pn = 0
        if not rn:
            rn = self.max_rownum

        params = {
            'format': 'json',
            'sort': 0,
            'rmk1': rmk1,
            'pn': pn,
            'rn': rn,
            'idx_cgy': 'web',
            'wd': wd
        }
        url = self.main_url + urlencode(params)

        self.logger.info(url)
        resp = self.do_get(url=url)
        return resp
        # print(resp)

    def compose_jump_url(self, url=None):
        self.logger.info('原始页面 {}'.format(url))
        parsed_params = parse_qs(urlparse(url).query)
        categorynum = parsed_params.get('categorynum')[0]
        infodate = parsed_params.get('infodate')[0]
        infoid = parsed_params.get('infoid')[0]

        jump_url = '/'.join([self.domain, categorynum[:3],
                             categorynum[:6], categorynum, infodate, infoid + '.html'])

        return jump_url

    def get_real_url(self, link=None):
        self.logger.info('抓取页面: {}'.format(link))

        resp = self.do_get(link)
        if not resp:
            self.logger.error('抓取页面出错: {}'.format(link))
            return
        bs = BeautifulSoup(resp, 'lxml')

        try:
            href = bs.find('div', class_='article_con').find('a')['href']
        except:
            self.logger.error('无法获取内容...')
            return
        noticeTitle = bs.find(
            'div', {'class': 'article_top'}).find('h3').get_text()

        # r = re.compile(r'发布时间：(.*?)字号：', re.S)
        # pubdate = bs.find('p', class_='article-a-info').get_text()
        # noticePubDate = r.findall(pubdate)[0].strip().replace(
        #     '年', '-').replace('月', '-').replace('日', ' ')

        return {'url': href, 'noticeTitle': noticeTitle}

    def store_notice(self, notices=None):

        ct = len(notices)
        i = 1
        for nt in notices:
            id = nt.get('id')
            title = nt.get('title')
            self.logger.info('开始更新/插入 {}/{} {} {}'.format(i, ct, id, title))
            i += 1
            if upsert_to_mongo({'id': id}, nt):
                self.logger.info(
                    '更新/插入 {} {} 成功'.format(id, title))

    def get_new_notices(self, notices=None):
        new_nts = []
        for nt in notices:
            id = nt.get('id')
            title = nt.get('title')
            if check_id_mongo(nt):
                self.logger.info('已存在通告 {}'.format(id))
            else:
                self.logger.info('新发现通告 {}'.format(id))
                new_nts.append(nt)

        return new_nts

    def main(self):
        # zjs = zjs()

        self.get_main()

        full_notices = []
        full_notices_cleaned = []

        for wd in self.kws:
            self.logger.info('查找关键字 {}'.format(wd))
            for k, v in self.rmk1.items():
                # print(k, v)
                resp = self.search_kw(wd=wd, rmk1=v)

                notices = self.extract_info(resp)
                if notices:
                    full_notices.extend(notices)
        self.logger.info('获得记录 {} 条'.format(len(full_notices)))
        # print(full_notices[0])

        for nt in full_notices:
            formated_nt = self.format_notice(nt)
            if formated_nt:
                full_notices_cleaned.append(self.format_notice(nt))

        uniq_notices = get_uniq_notice(full_notices_cleaned)

        self.logger.info('获得不重复记录 {} 条'.format(len(uniq_notices)))

        self.logger.info('检查新增通知...')
        new_uniq_notices = self.get_new_notices(notices=uniq_notices)
        new_uniq_notices_ct = len(new_uniq_notices)
        self.logger.info('获得新记录 {} 条'.format(new_uniq_notices_ct))

        # 拿到真实链接
        i_ct = 1
        for nt in new_uniq_notices:
            # nt['noticeTitle']

            self.logger.info('获取详细信息 {}/{} {} {}'.format(i_ct, new_uniq_notices_ct,
                                                         nt.get('id'), nt.get('title')))
            i_ct += 1
            real_info = self.get_real_url(
                self.compose_jump_url(nt.get('link')))
            if not real_info:
                self.logger.error('无法获取链接...')
                continue

            nt['url'] = real_info.get('url')
            nh = self.do_get(url=real_info.get('url'))
            nt['noticeContent_html'] = str(nh)
            try:
                nt['noticeContent'] = BeautifulSoup(nh, 'lxml').get_text()
            except:
                self.logger.error('解析公告摘要页面出错 {}'.format(real_info.get('url')))
                self.logger.error(nh)
            nt['noticeTitle'] = real_info.get('noticeTitle')
            # nt['noticePubDate'] = real_info.get('noticePubDate')

            # 明细页的链接经常失效，将摘要页存放和推送
            nt['real_source_link'] = nt['url']
            nt['url'] = nt['link']

        self.logger.info('开始存放...')
        self.store_notice(notices=new_uniq_notices)
        self.logger.info('浙江省级结束...')

    def test1(self):
        wd = '存款'
        mk = '002002001'
        a = self.search_kw(wd=wd, rmk1=mk)
        print(a)


if __name__ == "__main__":

    zjs = zjs()
    # zjs.test1()
    zjs.main()

    # zjs.get_main()

    # url = 'http://zjpubservice.zjzwfw.gov.cn/jump.html?infoid=7e647a85-b001-420f-bb22-7d706940433a&categorynum=002002001&infodate=20190620'

    # zjs.compose_jump_url(url)


#     resp = zjs.do_get(url)

#     print(resp)
#     bs = BeautifulSoup(resp, 'lxml')

#     print(bs.find('div', class_='article_con'))


# #     notice_title = bs.find(
#         'div', {'class': 'article_top'}).find('h3').get_text()
#     print(notice_title)

#     pubdate = bs.find('p', class_='article-a-info')

#     p = pubdate.get_text()
#     print(p)
#     r = re.compile(r'发布时间：(.*?)字号：', re.S)
#     p_r = r.findall(p)[0].strip()
#     p_r = p_r.replace('年', '-').replace('月', '-').replace('日', ' ')
#     print(p_r)

#     # a = bs.find('div', class_='article_con').find(
#     #     'table').find_all('tr')[2].find_all('td')
#     # print(a)


# # /html/body/div[5]/div/div[2]/div[2]/table/tbody/tr[7]/td/div/b/a

# # body > div:nth-child(11) > div > div.article_bd > div.article_con
