from db_utils import *
import json

client = pymongo.MongoClient('120.193.61.37:17027', connect=False)
db = client['czck']


def get_from_mongo(where):
    rt = db['czck'].find(where)

    if rt:
        return list(rt)

    return None


def find_no_date_data():
    tt = get_from_mongo({'source': '浙江政府采购网'})

    for t in tt:

        dt = t.get('noticePubDate')
        if not dt:
            print(t.get('id'), t.get('title'))


def test_check_id():
    # [{'_id': ObjectId('5d2fd9c375306e0a42fd0a73'), 'id': '5906531', 'districtName': '义乌市', 'keywords': '一、 采购人名称：\xa0义乌市财政局\xa0 二、 采购项目名称：\xa0义乌市财政局2019年度市级财政
    # 资金定期存款（第二期）项目中标公告\xa0\xa0 \xa0 \xa0 \xa0 \xa0 三、 采购项目编号：\xa0YWZC2019005GK\xa0\xa0 \xa0 \xa0 \xa0 \xa0 四、 采购组织类型：\xa0政府集中采购-委托本级集采\xa0 五、 采购方', 'mainBidMenuName': 'C150101银行代理服务', 'projectCode': 'YWZC2019005GK', 'projectName': '义乌市财政局2019年度市级财政资金定期存款（第二期）项目中标公告', 'pubDate': '1562601600000', 'source': '浙江政府采购网', 'title': '义乌市财政局2019年度市级财政资金定期存款（第二期）项目中标公告', 'type': 51, 'typeName': '中标公告', 'url': 'http://www.zjzfcg.gov.cn/innerUsed_noticeDetails/index.html?noticeId=5906531'}]
    # a = get_from_mongo({'id': '5906531'})
    # print(a[0].get('title'))
    # a = get_from_mongo({'id': '5880903'})
    # print(a[0].get('title'))
    # # check_id_mongo

    a = get_from_mongo({'title': '龙泉市财政局财政资金定期存款项目中标结果公示'})
    for i in a:
        print(i.get('title'))


if __name__ == "__main__":
    find_no_date_data()
    # test_check_id()
