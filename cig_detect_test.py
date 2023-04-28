import traceback
from TSDKreadTemp_Beta import TSDK_TemProcess
import cv2 
import numpy as np
import time
time_start = time.time()  # 记录开始时间
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

def readRawTem(path,dtype):
    rows = 512  # 图像的行数
    cols = 640  # 图像的列数
    channels = 1  # 图像的通道数，灰度图为1
    img = np.fromfile(file = path,dtype ='uint16')
    img = img.reshape(rows, cols, channels)/10
    return img


name = "DJI_20230331142744_0003_T"
# name = "DJI_20230331142919_0005_T"
# imgPath = "./thermal_QingDao/img_test/IMG_M30T/"
imgPath = "thermal_QingDao/img_test/IMG_M30T/"

imgName = imgPath+name+".JPG"
# imgName = "./thermal_QingDao/img_test/IMG_M30T/DJI_20230331142744_0003_T.JPG
# imgName = "./thermal_QingDao/img_test/IMG_M30T/DJI_20230331142731_0002_T.JPG"
# imgName = "./thermal_QingDao/img_test/IMG_M30T/DJI_20230331142715_0001_T.JPG"
# imgName = "./thermal_QingDao/img_test/DJI_20230326105101_0003_T.JPG"
# imgName = "./thermal_QingDao/img_test/DJI_20230326105056_0002_T.JPG"
# imgName = "./thermal_QingDao/img_test/DJI_20230326105046_0001_T.JPG"
# imgName = "./DJI_TSDK_H20T/DJI_TSDK_linux/grayset/H20N/DJI_0001_R.JPG"


img =  cv2.imread(imgName)


# savePath = "./thermal_QingDao/img_treated/"
# imgPath = "./thermal_QingDao/img_untreated/"


savePath = "./thermal_QingDao/img_treated/IMG_M30T/"
imgPath = "./thermal_QingDao/img_untreated/IMG_M30T/"

print("*******************************************************")
print(img.shape)

try:
    tsdkT = TSDK_TemProcess(imgName,name,savePath = "./thermal_QingDao/img_treated/")
except Exception as e:
    traceback.print_exc()
# print(tsdkT.thermal_np)
print(type(tsdkT.thermal_np))
print(tsdkT.thermal_np.shape)

# print(tsdkT.thermal_np.max())
# print(np.where(tsdkT.thermal_np == tsdkT.thermal_np.max()))
ppmax = list(int(i) for i in np.where(tsdkT.thermal_np == tsdkT.thermal_np.max()))
ppmax.append(tsdkT.thermal_np.max())
pmax = np.array(ppmax)


# tsdkT.showRawImgR_beta(savename=savePath+name+"_G.jpg")    

# cv2.waitKey()
def detect_outliers(gray, threshold=4):
    """
    使用均方差检测方法检测灰度图中的离群值
    :param gray: 灰度图像,为一个二维的NumPy数组
    :param threshold: 离群值检测阈值，如果像素值与均值的差大于 threshold 倍的标准差，则认为该像素为离群值
    :return: 一个二维的NumPy数组,每行包含离群值的像素行坐标、列坐标和像素值
    """
    mean = np.mean(gray)
    std = np.std(gray)
    gray_u8 = gray.astype(np.uint8)
    gray_clean = np.zeros_like(gray)
    ret, gray_mask = cv2.threshold(gray_u8, mean+std*1, 255, cv2.THRESH_BINARY)
    thin_mask = calcContours(gray_mask,thres=100)
    cv2.bitwise_and(gray,gray,gray_clean,thin_mask)

    outlier_pixels = np.argwhere((gray_clean - mean) > threshold * std)
    # print(outlier_pixels)
    fire_pp =  np.hstack((outlier_pixels, gray[outlier_pixels[:,0], outlier_pixels[:,1]].reshape(-1,1)))
    return fire_pp

errPP = detect_outliers(tsdkT.thermal_np)*2
errPP[:,-1] = errPP[:,-1]/2
errPP = np.vstack((errPP,pmax))
# ppmax(errPP)


np.savetxt(r'testPP.txt', errPP, fmt='%d', delimiter=' ')
print(errPP)

from test import merge_pixels

# 
eP_1 = merge_pixels(errPP,50)
eP_2 = merge_pixels(errPP,2)


a = set((tuple(i) for i in eP_2))
b = set((tuple(i) for i in eP_1))

eP_full =list(list(i) for i in a.intersection(b)) 

print(type(eP_full))

print("1 this is \n",eP_1)
print("2 this is \n",eP_2)

print("this is :",eP_full)

time_end = time.time()  # 记录结束时间
time_sum = time_end - time_start  # 计算的时间差为程序的执行时间，单位为秒/s
print(time_sum)






