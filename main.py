import json
import sys
import traceback
from TSDKreadTemp_Beta import TSDK_TemProcess
import cv2 
import numpy as np
import time
from myHttp import signup, updateMessage,upload_fire_info,get_process_info,clearmessage
from ImageInfo import ImageInfo
from watchdog.observers import Observer
from watchdog.events import *
import time
from readDJI import readDJI
# from utils.minioUtil import MinioClient
# from utils.mysqlUtil import MysqlClient
 
import glob

SUFFIXES = ".jpeg"
# SUFFIXES = ".JPG"
LOCAL_UNTREAT = "untreatedImg/"
LOCAL_RAW = "rawImg/"
LOCAL_SNIP = "snipImg/"
LOCAL_JSON = "fire_data_json/"
LOCAL_RECT = "rectImg/"
M = 3

SNIP_LEN = 75

# function()   执行的程序

def calcContours(gray_thres,thres):
    # 找轮廓（连通区域）
    # _, contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # OpenCV <= 3.4
    contours, hierarchy = cv2.findContours(gray_thres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # OpenCV > 3.4
    new_contours = []
    total_area = 0
    for con in contours:
        area = cv2.contourArea(con)
        # if 200 < area < 10000: # 排除面积太小或太大的
        if thres > area:  # 排除面积太大的
            new_contours.append(con)
    mask = np.zeros(shape=gray_thres.shape, dtype=np.uint8)
    mask = cv2.drawContours(mask, new_contours, -1, 255, -1)
    return mask


def delUsedFiles(imgRName,imgName):
    # 删除已经使用过的文件，减少服务器存储压力
    # TODO 更新文件明细
    name = imgName[:-4]
    RImgFile = 'output/' + name + '_R.jpg'
    MImg = 'output/' + name + '_M.jpg'
    ImgFile = 'output/' + name + '.jpg' 
    ComBImg = 'output/' + name + '.jpg'+'_combine_r'+'.jpg'
    SiftMImg = 'output/' + name + '.jpg'+'_siftmatch'+'.jpg'

def detect_outliers(gray, ppmax, threshold=3):    
    
    mean = np.mean(gray)
    std = np.std(gray)
    
    gray_u8 = gray.astype(np.uint8)
    gray_clean = np.zeros_like(gray)
    ret, gray_mask = cv2.threshold(gray_u8, mean+std*M, 255, cv2.THRESH_BINARY)
    # 可信范围 thin_mask
    thin_mask = calcContours(gray_mask,thres=100)
    cv2.bitwise_and(gray,gray,gray_clean,thin_mask) 
    # 离群值
    outlier_pixels = np.argwhere((gray_clean - mean) > threshold * std)
    fire_pp =  np.hstack((outlier_pixels, gray[outlier_pixels[:,0], outlier_pixels[:,1]].reshape(-1,1)))
    # 判断pmax是否在thin_mask范围内，是则加入 不是则忽略
    for pmax in ppmax:
        if(thin_mask[int(pmax[0]),int(pmax[1])]>0):
            fire_pp = np.vstack((fire_pp,pmax))   
        # print(outlier_pixels)
    return fire_pp

# 未定 去除大片连续区域
def remove_large_clusters_1(thresed_image, threshold_area=50):
    
    # 查找轮廓
    
    contours, _ = cv2.findContours(thresed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 遍历轮廓并进行面积判断
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > threshold_area:
            # 如果面积超过阈值，则将该区域填充为黑色
            cv2.drawContours(thresed_image, [contour], 0, 0, -1)
    return thresed_image

def merge_pixels(data, distance_threshold):
        # sort data by x coordinate firstly ,y coordinate secondly
        data = sorted(data, key=lambda x: (x[0], x[1]))
        
        merged_data = []
        current_pixel = None
        
        for pixel in data:
            if current_pixel is None:
                # first pixel, add to merged_data
                merged_data.append(pixel)
                current_pixel = pixel
            else:
                # calculate distance between current pixel and the new pixel
                distance = np.sqrt((pixel[0] - current_pixel[0])**2 + (pixel[1] - current_pixel[1])**2)
                # if distance <= distance_threshold and abs(pixel[3] - current_pixel[3]) <= temperature_threshold:
                if (distance <= distance_threshold):
                    # merge pixels
                    # current_pixel[2] += 1
                    if pixel[2] > current_pixel[2]:
                        current_pixel[2] = pixel[2]
                        current_pixel[0] = pixel[0]
                        current_pixel[1] = pixel[1]
                else:
                    # add the current pixel to merged_data and update current_pixel
                    merged_data.append(pixel)
                    current_pixel = pixel
        return np.array(merged_data)
    
def pp_sort(ppList,dt1 = 2,dt2 = 50):
    # use diff distance(dt1,dt2) get central tem point ,merge
    eP_1 = merge_pixels(ppList,dt1)
    eP_2 = merge_pixels(ppList,dt2)
    
    a = set((tuple(i) for i in eP_2))
    b = set((tuple(i) for i in eP_1))

    eP_full =list(list(i) for i in a.intersection(b)) 
    
    return eP_full


def fire_detect(imgTpath,imgName,filesName):
    # tsdk 生产raw，得到raw读取的红外数据存thermal_np
    try:
        tsdkT = TSDK_TemProcess(imgTpath,imgName[0],savePath = LOCAL_RAW+filesName+"/")
    except Exception as e:
        traceback.print_exc()
    # 最大值 
    
    ppmax = []
    pmax = tsdkT.thermal_np.max()
    for i in np.where(tsdkT.thermal_np == pmax):
        i = list(i)
        # 奇怪的错误处理
        if i[0]>512 or i[1]>640:
            continue
        i.append(pmax)
        ppmax.append(i)
    
    # 离群值 
    errPP = detect_outliers(tsdkT.thermal_np, ppmax, threshold=3)*2
    errPP[:,-1] = errPP[:,-1]/2
    # errPP = np.vstack((errPP,pmax))
    
    print(errPP)
    # 列表整理
    fire_data = pp_sort(errPP)
    
    return fire_data
    """
    fire_data:
    [  高温点像素位置(红外图) 温度（伪
     [336.0, 662.0, 171.8],
     [522.0, 1158.0,  98.8] ],
     """



def genSnipImgs(data,imgT,imgName,filesName):
    pos = []
    for d in data:
        x = d[0]
        y = d[1]
        pos.append([x,y])
    snip_paths = []
    for i,p in enumerate(pos):
        print(i,p)
        xmin = int(p[1] - SNIP_LEN) if int(p[1] - SNIP_LEN) >=0 else 0  
        xmax = int(p[1] + SNIP_LEN) if int(p[1] + SNIP_LEN) <=1280 else 1280
        ymin = int(p[0] - SNIP_LEN) if int(p[0] - SNIP_LEN) >=0 else 0
        ymax = int(p[0] + SNIP_LEN) if int(p[0] + SNIP_LEN) <= 1024 else 1024
        snip_img = imgT[ymin:ymax,xmin:xmax]
        snip_path = LOCAL_SNIP+filesName+"/"+imgName+"_S"+str(i)+".JPG"
        snip_paths.append(snip_path)
        cv2.imwrite(snip_path,snip_img)
    return snip_paths


def genRectImgs(data,imgT,imgName,filesName,isW):
    pos = []
    for d in data:
        x = d[1]
        y = d[0]
        # 省略透视变换
        if isW:
            x = 2000+(x-640)*2-27
            y = 1500+(y-512)*2+9
        pos.append([y,x])
        
    rect_img = imgT
    for i,p in enumerate(pos):
        print(i,p)
        if isW:
            xmin = int(p[1] - SNIP_LEN) if int(p[1] - SNIP_LEN) >=0 else 0  
            xmax = int(p[1] + SNIP_LEN) if int(p[1] + SNIP_LEN) <=4000 else 4000
            ymin = int(p[0] - SNIP_LEN) if int(p[0] - SNIP_LEN) >=0 else 0
            ymax = int(p[0] + SNIP_LEN) if int(p[0] + SNIP_LEN) <= 3000 else 3000
        else:      
            xmin = int(p[1] - SNIP_LEN) if int(p[1] - SNIP_LEN) >=0 else 0  
            xmax = int(p[1] + SNIP_LEN) if int(p[1] + SNIP_LEN) <=1280 else 1280
            ymin = int(p[0] - SNIP_LEN) if int(p[0] - SNIP_LEN) >=0 else 0
            ymax = int(p[0] + SNIP_LEN) if int(p[0] + SNIP_LEN) <= 1024 else 1024

        cv2.rectangle(rect_img,(xmin,ymin),(xmax,ymax),(0,0,255),4,4)
        
    # if isW:
    #     rect_path =  LOCAL_RECT+filesName+"/"+imgName[1][:-7]+"_RW.jpeg"
    # else:
    #     rect_path =  LOCAL_RECT+filesName+"/"+imgName[0][:-7]+"_RT.jpeg"
    # 测试   
    
    if isW:
        rect_path =  LOCAL_RECT+filesName+"/"+imgName[1][:-6]+"_RW.jpeg"
    else:
        rect_path =  LOCAL_RECT+filesName+"/"+imgName[0][:-6]+"_RT.jpeg"
        
    cv2.imwrite(rect_path,rect_img)
    return rect_path
    
    
    
def doSingleImg(imgWpath,imgTpath,imgName,filesName):
    
    # * test
    # fire_data = fire_detect(imgTpath,imgName,filesName)
    
    try:
        print(os.path.isfile(imgWpath))
        currImageInfo = ImageInfo(imgWpath)
        #shot time
        shotTime = currImageInfo.get_Time()
        #lat lon camera central
        lat,lon = currImageInfo.get_camera_lat_lon()
        # fire_detect
        fire_data = fire_detect(imgTpath,imgName,filesName)
        
        if len(fire_data)<1:
            # 无异常
            repo_data = {
                "shot_time":shotTime,
                "fire_data":fire_data,
                "lat_lon":[lat,lon],
                "fire_img_snip":"",
                "error_info":"",
                "status":"100"
            }
            return repo_data
        else:
            imgT = cv2.imread(imgTpath)
            imgW = cv2.imread(imgWpath)
            rect_path_T = genRectImgs(fire_data,imgT,imgName,filesName,isW=0)
            rect_path_W = genRectImgs(fire_data,imgW,imgName,filesName,isW=1)
            
            repo_data = {
                "shot_time":shotTime,
                "lat_lon":[lat,lon],
                "fire_data":fire_data,
                "origin_w_file":imgWpath,
                "w_file":rect_path_W,
                "origin_t_file":imgTpath,
                "t_file":rect_path_T,
                # "fire_img_snip":paths,
                "error_info":"",
                "status":"101",
            }
            
            # MYSQL impact
            return repo_data
    except Exception as e:
        traceback.print_exc()
        repo_data = {
                "shot_time":"",
                "fire_data":[],
                "lat_lon":[35,120],
                "fire_img_snip":"",
                "error_info": str(e),
                "status":"404"
            }
        return repo_data

def find_all_files(files_path):
    files_names = []
    thisFile = []
    """遍历指定文件夹所有指定类型文件"""
    for filename in glob.glob(glob.escape(files_path)+'*_T.jpeg'):
        filename = filename.split("/")
        imgTname = filename[-1].split(".")
        
        thisFile.append('.'.join(imgTname))

        nameAttr = imgTname[0][-6:-2]
        imgWpath = glob.glob(files_path+"*"+nameAttr+'*_W.jpeg')
        imgWname= imgWpath[0].split("/")
        imgWname = imgWname[-1].split(".")
        
        thisFile.append('.'.join(imgWname))
        
        files_names.append(thisFile)
        thisFile = []
    return files_names 

def processfiles(filesPathsList,mysqlClient):
    print("------img process on------")
    for filesPath in filesPathsList:
        filesName = filesPath.split("/")
        filesName = filesName[-2]
        imgName = ""
        repo_json = []
        imgTWnames = find_all_files(filesPath) 
    
        
        dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir)
        
        for imgName in imgTWnames:
            imgTname = imgName[0]
            imgWname = imgName[1]
            imgTpath = filesPath+imgTname
            imgWPath = filesPath+imgWname
            try:
                repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
                repo_json.append(repo_data) # 上传的数据 待mysql处理
                # jsonPath = LOCAL_JSON+filesName+"/"+imgTname+"_F.json"
                # with open(jsonPath,"w") as fp:
                #     json.dump(repo_data,fp)
            except Exception as e:
                traceback.print_exc()
                
        jsonPath = LOCAL_JSON+filesName+"_F.json"
        with open(jsonPath,"w") as fp:
            json.dump(repo_json,fp)    
            
        mysqlClient.deal_data(repo_json)
        print("process done")
    

if __name__ == '__main__':
       
    
    # work_dir = os.path.dirname(os.path.abspath(__file__))
    # CONF_FILE = os.path.join(work_dir,'server.conf')

    
    # * 线上部署
    # minio_client = MinioClient(False)
    # client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
    # old_count = 0
    # new_count = 0
    # is_uploading = False
    
    
    # while True:
    #     new_count = client.count()
    #     if old_count < new_count:
    #         print("uploading------")
    #         # is_uploading = True
    #         old_count = new_count
    #         print(old_count)
    #         time.sleep(60)
    #     else:
    #         print(old_count)
    #         # if is_uploading:
    #         filesPathsList = list(minio_client.load_data('/home/fushan/fs_fire_detect/untreatedImg'))
    #         print("downloading-----")
    #         # is_uploading = False
    #         if filesPathsList != []:
    #             print("start process")
    #             processfiles(filesPathsList,client)
    #         else:
    #             print("wayline data clear")
            
       ## 线上部署
        
        
        
        
    # * 本地指定文件夹上传
    
    # minio_client = MinioClient(False)
    # # filesPathsList = list(minio_client.load_data('/home/fushan/fs_fire_detect/untreatedImg/'))
    # filesPathsList = ["/home/fushan/fs_fire_detect/untreatedImg/402b20a5-74c6-4c78-bd84-a7b7e52d1131/"]
    
    # for filesPath in filesPathsList:
    #     filesName = filesPath.split("/")
    #     filesName = filesName[-2]
    #     imgName = ""
    #     repo_json = []
    #     imgTWnames = find_all_files(filesPath) 
    
        
    #     dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
    #     for dir in dirs:
    #         if not os.path.exists(dir):
    #             print(dir,"is generated")
    #             os.makedirs(dir)
        
    #     for imgName in imgTWnames:
    #         imgTname = imgName[0]
    #         imgWname = imgName[1]
    #         imgTpath = filesPath+imgTname
    #         imgWPath = filesPath+imgWname
    #         try:
    #             repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
    #             repo_json.append(repo_data)
    #         except Exception as e:
    #             traceback.print_exc()   
                
    #     jsonPath = LOCAL_JSON+imgName[0][:-2]+"_F.json"
    #     with open(jsonPath,"w") as fp:
    #         json.dump(repo_json,fp)
            
        # client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
        # client.deal_data(repo_json) # repo_json:list        
    
    # # TODO * singleTest files process
    
    # filesPath = LOCAL_UNTREAT+"71b31487-55bf-4330-bb1c-caca5f460fe1/DJI_202304271553_013_71b31487-55bf-4330-bb1c-caca5f460fe1/"
    # filesPath = LOCAL_UNTREAT+"/0517testdata/"
    # filesPath = "/root/fs_fire_detect/fs-uav/thermal_QingDao/img_test/IMG_M30T/"
    # filesName = filesPath.split("/")
    # filesName = filesName[-2]
    # imgName = ""
    # repo_json = []
    # imgTWnames = find_all_files(filesPath) 
    
    
    # dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
    # for dir in dirs:
    #     if not os.path.exists(dir):
    #         os.makedirs(dir)
        
    # for imgName in imgTWnames:
    #     imgTname = imgName[0]
    #     imgWname = imgName[1]
    #     imgTpath = filesPath+imgTname
    #     imgWPath = filesPath+imgWname
    #     # jsonPath = LOCAL_JSON+filesName+"/"+imgName+"_F.json"
    #     # * test
    #     repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
        
    #     try:
    #         repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
    #         repo_json.append(repo_data)
            
    #         jsonPath = LOCAL_JSON+filesName+"_F.json"
    #         with open(jsonPath,"w") as fp:
    #             json.dump(repo_json,fp)
    #     except Exception as e:
    #         traceback.print_exc()   
    
    # client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
    # client.deal_data(repo_json) # repo_json:list        
    
    
    # 检测完整性
    # name = "DJI_20230331142744_0003_T"
    # imgPath = "./thermal_QingDao/img_test/IMG_M30T/"
    # imgName = imgPath+name+".JPG"
    # img =  cv2.imread(imgName)
    # # savePath = "./thermal_QingDao/img_treated/IMG_M30T/"
    # savePath = "./rawImg/"
    # try:
    #     tsdkT = TSDK_TemProcess(imgName,name,tsdkpath="./DJI_TSDK/DJI_TSDK_linux/utility/bin/linux/release_x64/dji_irp", 
    #                             savePath = "./thermal_QingDao/img_treated/",imgPath = "./thermal_QingDao/img_untreated/")
    # except Exception as e:
    #     traceback.print_exc()
    
    # 检测可用性：
    # imgName = "DJI_20230331142744_0003"
    # # imgName = "DJI_20230331142802_0004"
    # filesName = "img_test"
    # # imgName = "DJI_20230331142919_0005"
    # imgPath = "./thermal_QingDao/img_test/IMG_M30T/"+imgName+"_W.JPG"
    # imgTpath = "./thermal_QingDao/img_test/IMG_M30T/"+imgName+"_T.JPG"
    # jsonPath = LOCAL_JSON+imgName+"_F.json"
    
    # dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
    # for dir in dirs:
    #     if not os.path.exists(dir):
    #         os.makedirs(dir)
    
    # repo_data = doSingleImg(imgPath,imgTpath,imgName,filesName)

    # with open(jsonPath,"w") as fp:
    #     json.dump(repo_data,fp)
        

    # 数据测试1
    # def genJson(imgWPath,imgTpath):
        
    #     repo_data = {
    #             "shot_time":"2023-03-31 14:27:14",
    #             "lat_lon":[36.69,117.09],
    #             "fire_data":[[480.0, 124.0, 181.5]],
    #             "origin_w_file":imgWPath,
    #             "w_file":imgWPath,
    #             "origin_t_file":imgTpath,
    #             "t_file":imgTpath,
    #             # "fire_img_snip":paths,
    #             "error_info":"",
    #             "status":"101",
    #         }
        
    #     return repo_data

    
    # minio_client = MinioClient(False)
    # # filesPathsList = list(minio_client.load_data('/home/fushan/fs_fire_detect/untreatedImg/'))
    # filesPathsList = ["/home/fushan/fs_fire_detect/untreatedImg/71b31487-55bf-4330-bb1c-caca5f460fe1/DJI_202304271553_013_71b31487-55bf-4330-bb1c-caca5f460fe1/"]
    
    # for filesPath in filesPathsList:
    #     filesName = filesPath.split("/")
    #     filesName = filesName[-2]
    #     imgName = ""
    #     repo_json = []
    #     imgTWnames = find_all_files(filesPath) 
    
        
    #     dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
    #     for dir in dirs:
    #         if not os.path.exists(dir):
    #             print(dir,"is generated")
    #             os.makedirs(dir)
        
    #     for imgName in imgTWnames:
    #         imgTname = imgName[0]
    #         imgWname = imgName[1]
    #         imgTpath = filesPath+imgTname
    #         imgWPath = filesPath+imgWname
    #         try:
    #             repo_data = genJson(imgWPath,imgTpath)
    #             repo_json.append(repo_data)
    #         except Exception as e:
    #             traceback.print_exc()   
                
    #     # jsonPath = LOCAL_JSON+imgName[0][:-2]+"_F.json"
    #     # with open(jsonPath,"w") as fp:
    #     #     json.dump(repo_json,fp)
    #     client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
    #     client.deal_data(repo_json) # repo_json:list        
    
    # 火点检测测试脚本
    # 范围要求：
    # 1-13 烟头 
    # 15 -25  火机
    # 27-100 小明火
    # 102之后 稍微大 点的明火
    
    #获取全部文件列表
    # filesPath = "/thermal_QingDao/img_firespot_alter/"
    # filesName = filesPath.split("/")
    # filesName = filesName[-2]
    # imgName = ""
    # repo_json = []
    # imgTWnames = find_all_files(filesPath) 
    
    
    # dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
    # for dir in dirs:
    #     if not os.path.exists(dir):
    #         os.makedirs(dir)
    
    # 

    filesPath = "thermal_QingDao/img_firespot_alter/"
    filesName = "img_firespot_alter"
    #轮询 
    
    # 1-13 烟头 
    for i in range(1,13):
        attrName = "0"*(4-len(str(i))) + str(i)
        imgTpath = filesPath + attrName + "_T.JPG"
        imgWpath = filesPath + attrName + "_W.JPG"
        imgName = [attrName + "_T.JPG",attrName + "_W.JPG"]
        dji_data_dict = readDJI(imgWpath)
        
        
        relativeH= dji_data_dict["RelativeAltitude"]
        repo_json = doSingleImg(imgWpath,imgTpath,imgName,filesName)
        relativeH = {"relativeH":relativeH}
        repo_json.update(relativeH)
        # fire_data = fire_detect(imgTpath,attrName,filesName)
        
        jsonPath = LOCAL_JSON+filesName+"/"+attrName+"_F.json"
        with open(jsonPath,"w") as fp:
            json.dump(repo_json,fp)

    # 15 -25  火机
    for i in range(15,25+1):
        
        attrName = "0"*(4-len(str(i))) + str(i)
        imgTpath = filesPath + attrName + "_T.JPG"
        imgWpath = filesPath + attrName + "_W.JPG"
        imgName = [attrName + "_T.JPG",attrName + "_W.JPG"]
        dji_data_dict = readDJI(imgWpath)
        
        
        relativeH= dji_data_dict["RelativeAltitude"]
        repo_json = doSingleImg(imgWpath,imgTpath,imgName,filesName)
        relativeH = {"relativeH":relativeH}
        repo_json.update(relativeH)
        # fire_data = fire_detect(imgTpath,attrName,filesName)
        
        jsonPath = LOCAL_JSON+filesName+"/"+attrName+"_F.json"
        with open(jsonPath,"w") as fp:
            json.dump(repo_json,fp)
            
    # 27-99 小明火
    for i in range(27,100):
        
        attrName = "0"*(4-len(str(i))) + str(i)
        imgTpath = filesPath + attrName + "_T.JPG"
        imgWpath = filesPath + attrName + "_W.JPG"
        imgName = [attrName + "_T.JPG",attrName + "_W.JPG"]
        dji_data_dict = readDJI(imgWpath)
        
        
        relativeH= dji_data_dict["RelativeAltitude"]
        repo_json = doSingleImg(imgWpath,imgTpath,imgName,filesName)
        relativeH = {"relativeH":relativeH}
        repo_json.update(relativeH)
        # fire_data = fire_detect(imgTpath,attrName,filesName)
        
        jsonPath = LOCAL_JSON+filesName+"/"+attrName+"_F.json"
        with open(jsonPath,"w") as fp:
            json.dump(repo_json,fp)

    # 102之后 稍微大 点的明火
    for i in range(102,133+1):
        
        attrName = "0"*(4-len(str(i))) + str(i)
        imgTpath = filesPath + attrName + "_T.JPG"
        imgWpath = filesPath + attrName + "_W.JPG"
        imgName = [attrName + "_T.JPG",attrName + "_W.JPG"]
        dji_data_dict = readDJI(imgWpath)
        
        
        relativeH= dji_data_dict["RelativeAltitude"]
        repo_json = doSingleImg(imgWpath,imgTpath,imgName,filesName)
        relativeH = {"relativeH":relativeH}
        repo_json.update(relativeH)
        # fire_data = fire_detect(imgTpath,attrName,filesName)
        
        jsonPath = LOCAL_JSON+filesName+"/"+attrName+"_F.json"
        with open(jsonPath,"w") as fp:
            json.dump(repo_json,fp)     
    
        