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
from utils.minioUtil import MinioClient
from utils.mysqlUtil import MysqlClient
 
import glob

SUFFIXES = ".jpeg"
# SUFFIXES = ".JPG"
LOCAL_UNTREAT = "untreatedImg/"
LOCAL_RAW = "rawImg/"
LOCAL_SNIP = "snipImg/"
LOCAL_JSON = "fire_data_json/"
LOCAL_RECT = "rectImg/"


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
    ret, gray_mask = cv2.threshold(gray_u8, mean+std*1, 255, cv2.THRESH_BINARY)
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
        
    if isW:
        rect_path =  LOCAL_RECT+filesName+"/"+imgName+"_RW.JPG"
    else:
        rect_path =  LOCAL_RECT+filesName+"/"+imgName+"_RT.JPG"
        
    cv2.imwrite(rect_path,rect_img)
    return rect_path
    
    
    
def doSingleImg(imgWPath,imgTpath,imgName,filesName):
    
    # * test
    fire_data = fire_detect(imgTpath,imgName,filesName)
    
    try:
        print(os.path.isfile(imgWPath))
        currImageInfo = ImageInfo(imgWPath)
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
            imgW = cv2.imread(imgWPath)
            rect_path_T = genRectImgs(fire_data,imgT,imgName,filesName,isW=0)
            rect_path_W = genRectImgs(fire_data,imgW,imgName,filesName,isW=1)
            
            repo_data = {
                "shot_time":shotTime,
                "lat_lon":[lat,lon],
                "fire_data":fire_data,
                "origin_w_file":imgWPath,
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

class FileEventHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)
        self.last_filename = ""
        
    def on_moved(self, event):
        if event.is_directory:
            print("directory moved from {0} to {1}".format(event.src_path,event.dest_path))
        else:
            print("file moved from {0} to {1}".format(event.src_path,event.dest_path))

    def on_created(self, event):
        if event.is_directory:
            print("directory created:{0}".format(event.src_path))
        else:
            print("file created:{0}".format(event.src_path))

    def on_deleted(self, event):
        if event.is_directory:
            print("directory deleted:{0}".format(event.src_path))
        else:
            print("file deleted:{0}".format(event.src_path))

    # def on_modified(self, event):
    #     if event.is_directory:
    #         print("directory modified:{0}".format(event.src_path))
    #     else:
    #         print("file modified:{0}".format(event.src_path))
            
    def on_closed(self, event): 
        if not event.is_directory: 
            print("file closed:", event.src_path)
            filename = event.src_path.split('.')
            if filename[-6]=="T.jpeg":
                imgName = filename[:filename.index("_T")]
                imgPath = LOCAL_UNTREAT+imgName+"_W.jpeg"
                imgTpath = LOCAL_UNTREAT+imgName+"_T.jpeg"
                jsonPath = LOCAL_JSON+imgName+"_F.json"
                # busy wait _W.JPG ?
                
                # wait closed
                # doSingleProcess
                repo_data = doSingleImg(imgPath,imgTpath,imgName)
                with open(jsonPath,"w") as fp:
                    json.dump(repo_data,fp)
                return 1



    
# * watchdog , a new file a new process 
# if __name__ == "__main__":
#     observer = Observer()
#     event_handler = FileEventHandler()
#     path = sys.argv[1] if len(sys.argv) > 1 else '.'
#     observer.schedule(event_handler,path,True)
#     observer.start()
#     try:
#         while True:
#             time.sleep(1)
#     except KeyboardInterrupt:
#         observer.stop()
#     observer.join()

    
    # old method 1 begin

# configs = None
# with open('config.yml','r') as f:
#     configs = yaml.load(f,Loader=yaml.FullLoader)
# auth = oss2.Auth(configs['ALIYUN_ACCESS_KEY_ID'], configs['ALIYUN_ACCESS_KEY_SECRET'])
# bucket = oss2.Bucket(auth, configs['ALIYUN_EXTERNAL_END_POINT'], configs['BUCKET_NAME'])

#     while(True):
#         try:
#             time.sleep(10)
#             token = signup()
#             getCurrTask(bucket, token)
#         except Exception as e:
#             traceback.print_exc()
#             continue


# def find_all_files(files_path):
#     files_names = []
#     thisFile = []
#     """遍历指定文件夹所有指定类型文件"""
#     for filename in glob.glob(files_path+'*_T.jpeg'):
#         filename = filename.split("/")
#         imgName = filename[-1].split(".")
#         files_names.append(imgName[0][:-2])  # 以字符串形式保存
#     return files_names 
def find_all_files(files_path):
    files_names = []
    thisFile = []
    """遍历指定文件夹所有指定类型文件"""
    for filename in glob.glob(files_path+'*_T.jpeg'):
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

if __name__ == '__main__':
    
    # with open('/data/dealt.json', 'r') as f:
    #     json_data = json.load(f)
    #     json_data = json_data['dealt']
    #     print(json_data)
    
        
    # TODO *** the real main ***
    
    # minio_client = MinioClient(False)
    # filesPathsList = minio_client.load_data('/home/fushan/fs_fire_detect/untreatImg/')

    # for filesPath in filesPathsList:
    #     filesName = filesPath.split("/")
    #     filesName = filesName[-2]
    #     imgName = ""
    #     repo_json = []
    #     imgNames = find_all_files(filesPath) 
            
    #     for imgName in imgNames:
    #         imgWPath = filesPath+imgName+"_W"+SUFFIXES
    #         imgTpath = filesPath+imgName+"_T"+SUFFIXES
    #         # jsonPath = LOCAL_JSON+filesName+"/"+imgName+"_F.json"
    #         try:
    #             repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
    #             repo_json.append(repo_data)
    #         #     with open(jsonPath,"w") as fp:
    #         #         json.dump(repo_data,fp)
    #         except Exception as e:
    #             traceback.print_exc()   
    
    # client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
    # client.deal_data(repo_json) # repo_json:list        
    
    # TODO * singleTest files process
    
    filesPath = LOCAL_UNTREAT+"71b31487-55bf-4330-bb1c-caca5f460fe1/DJI_202304271553_013_71b31487-55bf-4330-bb1c-caca5f460fe1/"
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
        # jsonPath = LOCAL_JSON+filesName+"/"+imgName+"_F.json"
        # * test
        repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
        
        try:
            repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
            repo_json.append(repo_data)
        #     with open(jsonPath,"w") as fp:
        #         json.dump(repo_data,fp)
        except Exception as e:
            traceback.print_exc()   
    
    client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
    client.deal_data(repo_json) # repo_json:list        
    
             
    # 检测完整性
    # name = "DJI_20230331142744_0003_T"
    # imgPath = "./thermal_QingDao/img_test/IMG_M30T/"
    # imgName = imgPath+name+".JPG"
    # img =  cv2.imread(imgName)
    # savePath = "./thermal_QingDao/img_treated/IMG_M30T/"
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
        