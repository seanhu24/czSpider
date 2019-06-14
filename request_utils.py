# -*- coding: utf-8 -*-

import requests
from requests import RequestException
import time
from logging.config import fileConfig
import logging
import app_sx
# from selenium import webdriver

fileConfig('logging_config.ini')
logger = logging.getLogger('sLogger')


# def get_by_PhantomJS(url=None):
#     service_args = []
#     service_args.append('--load-images=no')  # 关闭图片加载
#     service_args.append('--disk-cache=yes')  # 开启缓存
#     service_args.append('--ignore-ssl-errors=true')
#     driver = webdriver.PhantomJS(service_args=service_args)
#     driver.get(url)
#     html = driver.page_source
#     driver.quit()
#     return html


def get_one_url(url):
    # logger.info('爬取url:' + url)
    retry = 3
    success = False
    while not success:
        try:
            resp = requests.get(url)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None


def get_one_url_with_header(url, headers=None):
    # logger.info('爬取url:' + url)
    retry = 3
    success = False
    while not success:
        try:
            resp = requests.get(url, headers=headers)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None


def get_one_url_with_payload(url, payload=None):
    # logger.info('爬取url:' + url)
    retry = 3
    success = False
    while not success:
        try:
            if payload:
                resp = requests.get(url, params=payload)
                print(resp.url)
            else:
                resp = requests.get(url)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None


def post_one_url_with_payload(url, payload=None, data=None):
    retry = 3
    success = False
    while not success:
        try:
            resp = requests.post(url, params=payload, data=data)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None


def post_one_url(url, data=None):
    # logger.info('爬取url:' + url)
    retry = 3
    success = False
    while not success:
        try:
            resp = requests.post(url, data=data)
            success = True
            if resp.status_code == 200:
                resp.encoding = 'utf-8'  # 解决中文问题
                return resp.text
            return None
        except RequestException:
            logger.error('请求索引页出错')
            for i in range(1, retry + 1):
                wait = i * 10
                logger.info('等待%d秒' % wait)
                time.sleep(wait)
            return None


if __name__ == "__main__":

    # data = {'col': 1, 'appid': '1', 'webid': 3003, 'path': '/', 'columnid': 1518878,
    #         'sourceContentType': 1, 'unitid': '4685909', 'webname': '绍兴公共资源交易网', 'permissiontype': 0}

    # payload = {'startrecord': 1, 'endrecord': 120, 'perpage': 40}
    # # r = requests.post(
    # #     'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp', params=payload, data=data)

    # # r.encoding = 'utf8'
    # # print(r.text)
    # resp = post_one_url_with_payload(
    #     'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp', payload=payload, data=data)
    # print(resp)

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

    url = 'http://ggzy.huzhou.gov.cn//HZfront/InfoDetail/?InfoID=e1994d3e-a3ed-4677-898a-a289b5d97334&CategoryNum=024001001'
    r = requests.get(url, headers=headers)
    r.encoding = 'utf8'
    print(r.text)
