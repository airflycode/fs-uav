# coding=utf-8
import json
import time
from urllib import response
import requests
from log import logger

#调用java后台服务器的接口

# 必要的修改：
"""
host

signup()

get_process_info()

upload_fire_info():
    一个所有信息的回传接口:新增报错记录

    数据包括：
        地理位置信息[lat,lon]
        温度[tem]
        时间[time]
        可见光截图的保存位置["xxx/xxx.jpg]

repo_error()


"""

host = 'http://47.98.151.104:8088'


message =''

def signup(username='admin',password='q.123456'):
    requrl='/uav-inspection-server/web/auth/login'
    data={
        'username':username,
        'password':password
    }
    try:
        r = requests.post(host + requrl, data=data,headers={'Content-Type':'application/x-www-form-urlencoded'})
        token = json.loads(r.text).get('data')['token']
        return token
    except requests.exceptions.RequestException as e:
        logger.error(e)



def get_process_info(token):
    requrl='/uav-inspection-server/web/gis/get-prepared-process-info'
    data={
        #'status':3
    }
    try:
        # start = time.time()
        r=requests.post(host+requrl,data=json.dumps(data),headers={'Content-Type':'application/json','token':token})
        items=json.loads(r.text).get('data').get('items')
        # end = time.time()
        # elapsed = end - start
        # s = (elapsed % 3600) % 60   
        # print("Time used = :%fs" % (s))
        # print("///////////////\n",items,"////////////////")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(e)


def upload_fire_info(id,time,firedata,token,errorCode):
    requrl = ""
    data = {
        'id':id,
        'shotDate':time,
        'firedata':firedata,
        "errorCode":errorCode
    }
    try:
        r=requests.post(host+requrl,data=json.dumps(data),headers={'Content-Type':'application/json','token':token})
        # print("response:",r)
        if r.status_code != 200:
            response=json.loads(r.text)
            print("@@@@@error_response:",response)
            print("data:",data)
    except requests.exceptions.RequestException as e:
        print("error:",e)
        logger.error(e)

def repo_error():
    requrl = ""
    data = {
    
    }
    try:
        r=requests.post(host+requrl,data=json.dumps(data),headers={'Content-Type':'application/json','token':token})
        # print("response:",r)
        if r.status_code != 200:
            response=json.loads(r.text)
            print("@@@@@error_response:",response)
            print("data:",data)
    except requests.exceptions.RequestException as e:
        print("error:",e)
        logger.error(e)


def updateMessage(mes):
    global message
    message=message+'\n'+mes


def getmessage():
    return message


def clearmessage():
    global message
    message=''



def add_process_info1(token,id,time):
    requrl='/uav-inspection-server/web/gis/update-process-info'
    data={
        'id':id,
        'status':4,
        'shootDate':time
        # 'shootDate':"2020-04-01 11:00:00"
    }
    try:
        r=requests.post(host+requrl,data=json.dumps(data),headers={'Content-Type':'application/json','token':token})
    except requests.exceptions.RequestException as e:
        logger.error(e)

def add_process_info2(mes,token,id,time,tem,bound,errorcode):
    requrl = '/uav-inspection-server/web/gis/update-process-info'
    data = {
        'id':id,
        'status': 6,
        'message':mes,
        'shootDate': time,
        # 'shootDate':"2020-04-01 11:00:00",
        'errorCode':errorcode,
        'temperatures':tem,
        'bound':bound
    }
    try:
        r=requests.post(host+requrl,data=json.dumps(data),headers={'Content-Type':'application/json','token':token})
        print(1)
    except requests.exceptions.RequestException as e:
        logger.error(e)
        

def catchErrorData1(data):
    # data = [{'lineName': '454649316eab4eb3a67b76e89198c185', 'longitude': 120.24733303891588, 'latitude': 30.769136081187664, 'pointId': '43226', 'temperature': 14.0, 'acquireTime': '2023-01-03 14:15:35'}, {'lineName': '454649316eab4eb3a67b76e89198c185', 'longitude': 120.24733793000291, 'latitude': 30.769136894795356, 'pointId': '43227', 'temperature': 13.6, 'acquireTime': '2023-01-03 14:15:35'}, {'lineName': '454649316eab4eb3a67b76e89198c185', 'longitude': 120.24734282108994, 'latitude': 30.76913770840305, 'pointId': '43228', 'temperature': 14.0, 'acquireTime': '2023-01-03 14:15:35'}, {'lineName': '454649316eab4eb3a67b76e89198c185', 'longitude': 120.24734771217697, 'latitude': 30.769138522010742, 'pointId': '43229', 'temperature': 12.1, 'acquireTime': '2023-01-03 14:15:35'}, {'lineName': '454649316eab4eb3a67b76e89198c185', 'longitude': 120.24735260326399, 'latitude': 30.769139335618434, 'pointId': '43230', 'temperature': 15.0, 'acquireTime': '2023-01-03 14:15:35'}]
    li=[]
    for d in data:
        # print(d['temperature'])
        li.append(d['temperature'])
    # print(data[0]['temperature'])
    if max(li)>=150.0:
        print(max(li))
        return

if __name__ == '__main__':
    token=signup()
    r=get_process_info(token)
    print(1)
