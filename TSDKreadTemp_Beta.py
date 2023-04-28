import os
import numpy as np
import cv2


def showImgInCv2(img, width, height, name="img"):
    res = img
    cv2.namedWindow(name,cv2.WINDOW_NORMAL)
    cv2.resizeWindow(name,width,height)
    
    cv2.imshow(name ,res)
    c = cv2.waitKey()
    if c == 27:
        cv2.destroyAllWindows()
        

class TSDK_TemProcess:
    """
    使用时初始化一个TSDK类
    """

    def __init__(self, imgTpath, imgName, distance=25.0, emissivity=0.95, humidity=22, reflection=51.8, 
                 tsdkpath="DJI_TSDK/DJI_TSDK_linux/utility/bin/linux/release_x64/dji_irp", 
                 savePath="unTreatedImg/", 
                 imgPath="unTreatedImg/"):
        

        self.tsdkPath = tsdkpath
        self.distance = distance
        self.emissivity = emissivity
        self.humidity = humidity
        self.reflection = reflection
        
 
        
        print("the file TSDK extracting is: " +
            imgTpath, os.path.isfile(imgTpath))
        self.tsdkGenRaw(tsdkpath, imgTpath, savePath, imgName)
        # self.tsdkGenRaw_Params(tsdkpath, imgTpath, savePath, imgName)
        
        imgRrawPath = str(savePath+imgName+".raw")
        rows = 512  # 图像的行数
        cols = 640  # 图像的列数
        channels = 1  # 图像的通道数，灰度图为1
        thermal_img = np.fromfile(file = imgRrawPath,dtype ='uint16')
        np.savetxt(r'test.txt', thermal_img, fmt='%d', delimiter=' ')
        self.thermal_np = thermal_img.reshape(rows, cols)
        # cv2.imwrite(imgTpath[:-4]+"_t_v.png",(self.thermal_np/65535)*205+50)
        # png = cv2.imread(imgTpath[:-4]+"_t_v.png")
        self.thermal_np = self.thermal_np/10
        # showImgInCv2(thermal_img,rows,cols,name="thermal_img")
        
        print(1) 
        # print(self.thermal_np) 
        # print(self.thermal_np.shape)

    def tsdkGenRaw(self, tsdk, imgTpath, savePath, imgName):     
        
        print('--------export libdrip.so--------')
        param0 = "export LD_LIBRARY_PATH=/usr/local/lib:"+self.tsdkPath[:-7]
        print(param0)
        # r_v = os.system(param0)  
        
        print('--------tsdk start--------')
        # 选择的模式是measure输出的结果是温度信息，不是原始信息；
        param = '-s ' + imgTpath + ' -a measure -o ' +savePath+imgName+ '.raw'
        # print(tsdk+' '+param)
        r_v = os.system(param0 +" && "+ tsdk+' '+param)
        print(str(r_v)+'\n---------tsdk end---------')  # 输出的为tsdk.exe运行的返回值

    def tsdkGenRaw_Params(self, tsdk, imgTpath, savePath, imgName):
        print('--------tsdk start--------')
        # 选择的模式是measure输出的结果是温度信息，不是原始信息；
        param = '-s ' + imgTpath + ' -a measure -o ' +savePath+imgName+ '.raw' + ' --distance ' + str(self.distance) + ' --emissivity ' + str(self.emissivity) + \
            ' --humidity ' + str(self.humidity) + \
            ' --reflection ' + str(self.reflection)
        print(tsdk+' '+param)
        r_v = os.system(tsdk+' '+param)
        print(str(r_v)+'\n---------tsdk end---------')  # 输出的为tsdk.exe运行的返回值
    # 利用numpy的fromfile函数读取raw文件，并指定数据格式
    def readRawTem(path,dtype):
        rows = 512  # 图像的行数
        cols = 640  # 图像的列数
        channels = 1  # 图像的通道数，灰度图为1
        img = np.fromfile(file = path,dtype ='uint16')
        img = img.reshape(rows, cols, channels)/10
        return img

    def showRawImgR_beta(self,savename):
        rows = 512  # 图像的行数
        cols = 640  # 图像的列数
        channels = 1  # 图像的通道数，灰度图为1
        img = self.thermal_np
        img = img.reshape(rows, cols, channels)
        # 利用numpy中array的reshape函数将读取到的数据进行重新排列。
        imgToShow = img.astype("uint8")
        
        cv2.imwrite(savename,imgToShow)
        # # 展示图像
        # cv2.namedWindow('Infared image-640*512-8bit')
        # cv2.imshow('Infared image-640*512-8bit', imgToShow)
        # # # 如果是uint16的数据请先转成uint8。不然的话，显示会出现问题。
        # cv2.waitKey()
        # cv2.destroyAllWindows()
    def ShowRawImgR(path, dtype):
        rows = 512  # 图像的行数
        cols = 640  # 图像的列数
        channels = 1  # 图像的通道数，灰度图为1

        img = np.fromfile(path, dtype)
        img = img.reshape(rows, cols, channels)
        # 利用numpy中array的reshape函数将读取到的数据进行重新排列。
        imgToShow = img.astype("uint8")
        # 展示图像
        cv2.namedWindow('Infared image-640*512-8bit')
        cv2.imshow('Infared image-640*512-8bit', imgToShow)
        # # 如果是uint16的数据请先转成uint8。不然的话，显示会出现问题。
        cv2.waitKey()
        cv2.destroyAllWindows()

    def get_templist(self, points):
        if not points:
            return 0
        tem = 0
        temList = []
        for p in points:
            tem = self.thermal_np[p[0], p[1]]
            temList.append(tem)
        return temList

    # 转换到温度图下的坐标
    def get_tempsolo(self, point, svrFlag=1):
        tem = float(self.thermal_np[int(point[0]), int(point[1])])
        return tem

    def get_tempsolo_kernal(self, point):
        point = self.transPt(point)
        tem = self.kernalTemp(point)
        return tem

    def kernalTemp(self, point, width=3):
        # 获取一块像素面积内的温度 卷积处理值（锐化）
        # kernal=np.array([[1,1,1],[1,2,1],[1,1,1]])
        kernal = np.array([1, 1, 1, 1, 2, 1, 1, 1, 1])
        cnt = 0
        sum = 0
        for y in range(point[1]-width, point[1]+width+1):  # 高
            if y < 0 or y >= 256:
                continue
            for x in range(point[0]-width, point[0]+width+1):  # 宽
                if x < 0 or x >= 320:
                    continue
                temp = self.thermal_np[y][x] * kernal[cnt]
                sum += temp
                cnt += 1
        if cnt == 0:
            return 0
        return sum/cnt  # 均值

if __name__ == "__main__":
    imgRname = "/home/fushan/fs_fire_detect/thermal_QingDao/img_test/IMG_M30T/DJI_20230331142744_0003_T.JPG"
    name = "DJI_20230331142744_0003"


    tsdkT = TSDK_TemProcess(imgRname, name,savePath="./rawImg/")
    print(tsdkT.thermal_np)
