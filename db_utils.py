import pymongo
from config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]


def save_to_mongo(a_set):
    if db[MONGO_TABLE].insert_one(a_set):
        # print('save to mongo successfully', a_set)
        return True
    return False


def upsert_to_mongo(where, a_set):
    if db[MONGO_TABLE].update_one(where, {'$set': a_set}, upsert=True):
        # print('upsert to mongo successfully', a_set)
        return True
    return False


def check_id_mongo(a_set):
    if db[MONGO_TABLE].find_one({'id': a_set.get('id')}):
        return True
    return False


def save_mongo_to_csv(tbname, filename):
    d = db[MONGO_TABLE].find_one({}, {'_id': False})
    print(d)


if __name__ == "__main__":
    # print(check_id_mongo({'id': '10247'}))
    # print(save_to_mongo({'id': 1, 'name': 'asdfa'}))
    print(upsert_to_mongo({'id': 1}, {'name': 'aaa', 'age': 22}))
