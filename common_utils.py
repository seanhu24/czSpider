from config import *
import re
from bs4 import BeautifulSoup


def check_title_black_list(title=None):
    for kw in BLACK_LIST:
        if kw in title:
            return True
    return False


def get_uniq_notice(notices=None):
    id_list = []
    new_notices = []
    for n in notices:
        if n.get('id') not in id_list:
            id_list.append(n.get('id'))
            new_notices.append(n)
    return new_notices


def tidy_notice_content(text):
    cleanr = re.compile('<(.*?)>', re.S)
    d1 = re.sub(cleanr, '', text)
    d2 = re.sub('&nbsp;', ' ', d1)
    cleanr2 = re.compile('^(table|th)(.*?);}', re.S)
    d3 = re.sub(cleanr2, '', d2)
    d4 = d3.replace(u'\u200b', '')

    return ''.join(d4.splitlines())


def filter_by_keyword(links=None):
    back = []
    for l in links:
        title = l['title']
        for kw in KEYWORDS:
            if kw in title:
                back.append(l)
                break

    return back


def remove_header_comment(instr=None):
    s1 = re.sub(r'/\*.*\*/', '', instr)
    s2 = re.sub(r'.*;}', '', s1).strip()
    return s2


def get_page_num(html=None):
    '''
        湖州丽水公用提取页面数
    '''
    bs = BeautifulSoup(html, 'lxml')
    pg = bs.find('td', class_='huifont')
    # print(pg.get_text())
    # print(pg.get_text().split('/'))
    if pg:
        return pg.get_text().split('/')[1]
    return None


if __name__ == "__main__":

    ins = "海宁市海洲街道福采购合同公告"
    r = check_title_black_list(ins)
    print(r)
