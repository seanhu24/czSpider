from config import *
import re
from bs4 import BeautifulSoup


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
    instr = '''
    /* Generator: eWebEditor */
    p.MsoNormal, li.MsoNormal, div.MsoNormal {margin:0cm;margin-bottom:.0001pt;text-align:justify;text-justify:inter-ideograph;font-size:10.5pt;font-family:"Times New Roman","serif";}
    a:link, span.MsoHyperlink {color:blue;text-decoration:underline;text-underline:single;}
    a:visited, span.MsoHyperlinkFollowed {color:purple;text-decoration:underline;text-underline:single;}
    p.a, li.a, div.a {margin-top:0cm;margin-right:0cm;margin-bottom:7.8pt;margin-left:0cm;text-align:justify;text-justify:inter-ideograph;text-indent:10.0pt;layout-grid-mode:char;font-size:12.0pt;font-family:"Times New Roman","serif";}
    .MsoChpDefault {font-size:10.0pt;}
    div.WordSection1 {page:WordSection1;}
    ol {margin-bottom:0cm;}
    ul {margin-bottom:0cm;}

    根据《中华人民共和国招投标法》、《中华人民共和国招投标法实施条例》等规定，现就长兴县2016年第二期县级政府管理资金竞争存放计划项目进行公开招标，欢迎符合资格要求并有能力完成本项目的投标人参加，具
    体内容如下：
    一、项目编号： CXCG201607012
    二、项目概况：
    '''

    remove_header_comment(instr)
