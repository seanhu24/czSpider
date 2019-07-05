# def extendList(val, list=[]):
#     list.append(val)
#     return list


# list1 = extendList(10)
# list2 = extendList(123, [])
# # list3 = extendList('a')

# print("list1 = %s" % list1)
# print("list2 = %s" % list2)
# # print("list3 = %s" % list3)


import random
from random import randint

# a = ['Monday', 'Tuesday', 'Wensday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
# random.shuffle(a)

# print(a)


# def gen():
#     a = ['Monday', 'Tuesday', 'Wensday',
#          'Thursday', 'Friday', 'Saturday', 'Sunday']
#     for i in a:
#         yield i


# if __name__ == "__main__":
#     for a in gen():
#         print(a)


# site_stats = {'site': 'tecbeamers.com', 'traffic': 10000, "type": "organic"}

# for k, v in site_stats.items():
#     print("The key is: %s" % k)
#     print("The value is: %s" % v)
#     print("The type of value is: %s" % type(v))
#     print("++++++++++++++++++++++++")


# weekdays = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']

# print('-'.join(weekdays))


def y(x): return x ** 2


t = y(2)
print(t)
