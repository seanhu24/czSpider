KEYWORDS = ['存款', '公款', '结算账户', '专户', '存放', '存放银行', '存放定期', '存放资金',
            '存放公款', '存放定点', '存放账户', '存放金融', '存放养老金',
            '存放备用金', '存放保证金', '存放公积金', '代理银行', '开户银行',
            '资金银行', '基本户', '一般户', '账户开户', '基本账户', '一般账户', '银行账户', '开立账户']
BLACK_LIST = ['反向竞价', '在线询价']
MONGO_URL = 'localhost:17027'
# MONGO_URL = '120.193.61.37:17027'
MONGO_DB = 'czck'
MONGO_TABLE = 'czck'


SEARCH_LINK = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?'
# NOTICE_LINK = 'http://manager.zjzfcg.gov.cn/cms/api/cors/getRemoteResults?'

# 绍兴市公共资源交易网-招标
SX_MAIN_ZB_LINK = 'http://www.sxztb.gov.cn:33660/sxweb/fzxjy/007001/MoreInfo.aspx?CategoryNum=007001'

# 绍兴市公共资源交易网-中标
SX_MAIN_ZB2_LINK = 'http://www.sxztb.gov.cn:33660/sxweb/fzxjy/007002/MoreInfo.aspx?CategoryNum=007002'


SX_MAIN_SEARCH_LINK = [('http://ggb.sx.gov.cn/col/col1518878/index.html',
                        '招标（交易）公告', 1518878),  # 非中心交易（公告代发）项目	> 招标（交易）公告
                       ('http://ggb.sx.gov.cn/col/col1518879/index.html',
                        '中标公示', 1518879),  # 非中心交易（公告代发）项目	> 中标公示
                       ('http://ggb.sx.gov.cn/col/col1518859/index.html',
                        '采购要素公示', 1518859),  # 政府采购	> 采购要素公示
                       ('http://ggb.sx.gov.cn/col/col1518860/index.html',
                        '采购公告', 1518860),  # 政府采购	> 采购公告
                       ('http://ggb.sx.gov.cn/col/col1518861/index.html',
                        '中标（成交）公告', 1518861),  # 政府采购	> 中标（成交）公告
                       ('http://ggb.sx.gov.cn/col/col1518862/index.html',
                        '终止（废标）公告', 1518862)]  # 政府采购	> 终止（废标）公告

SX_MAIN_DATA_PROXY = 'http://ggb.sx.gov.cn/module/jpage/dataproxy.jsp'


# 嘉兴市公共资源交易中心
JX_GGZY_MAIN_LINK = 'http://www.jxzbtb.cn'
JX_GGZY_SEARCH_LINK = 'http://www.jxzbtb.cn/inteligentsearch/rest/inteligentSearch/getFullTextData'

# 湖州公共资源交易中心

HZ_MAIN_SEARCH_LINK = [('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024001/024001001/', ' 集中采购招标公告'),  # 政府采购 > 集中采购 > 集中采购招标公告
                       # 政府采购 > 集中采购 > 集中采购中标公示
                       ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024001/024001002/', '集中采购中标公示'),
                       # 政府采购 > 分散采购 > 分散采购招标公告
                       ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024002/024002001/', '分散采购招标公告'),
                       # 政府采购 > 分散采购 > 分散采购中标公示
                       ('http://ggzy.huzhou.gov.cn/HZfront/zfcg/024002/024002002/', '分散采购中标公示')


                       ]


FIRE_TIME1 = "10:30"
FIRE_TIME2 = "16:57"
