#coding=utf-8
import math
import re
from decimal import Decimal
import geopy.distance
import cv2

import exifread
from PIL import Image as ImagePIL, ImageDraw
from PIL.ExifTags import TAGS
# from pyexiv2 import Image as ImageExiv
import pandas as pd
from log import logger

# FOV 57.12°× 42.44°
VerticalFov = 42.44
LevelFov = 57.12

VerticalPixel = 3000
LevelPixel = 4000

VerticalPixel_R = 512
LevelPixel_R = 640


class ImageInfo:
    # 读取图片及其信息
    def __init__(self, file_name):
        self.file_name = file_name
        self.imgPIL = ImagePIL.open(file_name)
        # self.imgExiv = ImageExiv(file_name)
        # self.xmpDict = self.imgExiv.read_xmp()
        info = self.imgPIL._getexif()
        columns_list = ['nice', 'k', 'v']
        data_list = []
        if info is None:
            print("No Info")
        else:
            for k, v in info.items():
                nice = TAGS.get(k, k)
                data_list.append([nice, k, v])
        self.exif_df = pd.DataFrame(columns=columns_list, data=data_list)
        # print(self.exif_df)
        f = open(file_name, 'rb')
        self.tags = exifread.process_file(f)
        # print(self.tags)
        f.close()

    def cal_degree(self, yaw, y, x):
        # print('yaw x y out',yaw,x,y,math.atan2(y,x)/math.pi/2*360)
        ans = ((-yaw + math.atan2(y, x) / math.pi / 2 * 360) % 360 + 360) % 360
        # print(ans)
        return -ans

    # 获取图片角度属性 1：不翻转 2：左右翻转 3：180度翻转 4：上下翻转 5：6&2 6：顺时针翻转90度；7：8&2 8：逆时针翻转90度
    def get_orientation(self):
        orientation = self.exif_df[self.exif_df['nice'] == 'Orientation']['v'].tolist()[0]
        # print('orientation', orientation)
        return orientation

    # 获取相机经纬度
    def get_camera_lat_lon(self):
        try:
            # 拍摄时间
            EXIF_Date = self.tags["EXIF DateTimeOriginal"].printable
            # 纬度
            LatRef = self.tags["GPS GPSLatitudeRef"].printable
            Lat = self.tags["GPS GPSLatitude"].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
            Lat = float(Lat[0]) + float(Lat[1]) / 60 + float(Lat[2]) / float(Lat[3]) / 3600
            if LatRef != "N":
                Lat = Lat * (-1)
            # 经度
            LonRef = self.tags["GPS GPSLongitudeRef"].printable
            Lon = self.tags["GPS GPSLongitude"].printable[1:-1].replace(" ", "").replace("/", ",").split(",")
            Lon = float(Lon[0]) + float(Lon[1]) / 60 + float(Lon[2]) / float(Lon[3]) / 3600
            if LonRef != "E":
                Lon = Lon * (-1)
        except:
            print("ERROR:请确保照片包含经纬度等EXIF信息。")
            return None, None, None
        else:
            return  Lat, Lon

    

    # 获取飞行高度
    def get_altitude(self):
        # XMLPacket = self.exif_df[self.exif_df['nice'] == 'XMLPacket']['v'].tolist()[0]
        absoluteAltitude = float(self.xmpDict['Xmp.drone-dji.AbsoluteAltitude'])
        relativeAltitude = float(self.xmpDict['Xmp.drone-dji.RelativeAltitude'])
        return absoluteAltitude, relativeAltitude
        # try:
        #     altitude=self.tags['GPS GPSAltitude'].printable
        #     altitudeRef=self.tags['GPS GPSAltitudeRef'].printable
        #     return altitude,altitudeRef
        # except:
        #     print("ERROR:请确保照片包含高度等EXIF信息。")

    # 获取云台偏转角度
    # def get_degree_info(self):
        
    #             # 偏向角信息
    #     FlightYawDegree = float(self.xmpDict['Xmp.drone-dji.FlightYawDegree'])
    #     # 4 横滚角信息
    #     FlightRollDegree = float(self.xmpDict['Xmp.drone-dji.FlightRollDegree'])
    #     # 5 俯仰角信息
    #     FlightPitchDegree = float(self.xmpDict['Xmp.drone-dji.FlightPitchDegree'])

    #     GimbalRollDegree  = float(self.xmpDict['Xmp.drone-dji.GimbalRollDegree'])

    #     GimbalPitchDegree = float(self.xmpDict['Xmp.drone-dji.GimbalPitchDegree'])
                
    #     GimbalYawDegree = float(self.xmpDict['Xmp.drone-dji.GimbalYawDegree'])

    #     yaw = (GimbalYawDegree + 360) % 360
    #     pitch = (GimbalPitchDegree + 360) % 360
    #     roll = (GimbalRollDegree + 360) % 360
                
        # print(self.exif_df)
        # XMLPacket = self.exif_df[self.exif_df['nice'] == 'XMLPacket']['v'].tolist()[0]
        # ## 3.从 XMLPacket 里获取 偏向角信息
        # FlightYawDegree = \
        #     float(re.findall(r'<drone-dji:FlightYawDegree>(.*)</drone-dji:FlightYawDegree>', str(XMLPacket))[0])
        # # 4 横滚角信息
        # FlightRollDegree = \
        #     float(re.findall(r'<drone-dji:FlightRollDegree>(.*)</drone-dji:FlightRollDegree>', str(XMLPacket))[0])
        # # 5 俯仰角信息
        # FlightPitchDegree = \
        #     float(re.findall(r'<drone-dji:FlightPitchDegree>(.*)</drone-dji:FlightPitchDegree>', str(XMLPacket))[0])
        # GimbalRollDegree = \
        #     float(re.findall(r'<drone-dji:GimbalRollDegree>(.*)</drone-dji:GimbalRollDegree>', str(XMLPacket))[0])
        # GimbalPitchDegree = \
        #     float(re.findall(r'<drone-dji:GimbalPitchDegree>(.*)</drone-dji:GimbalPitchDegree>', str(XMLPacket))[0])
        # GimbalYawDegree = \
        #     float(re.findall(r'<drone-dji:GimbalYawDegree>(.*)</drone-dji:GimbalYawDegree>', str(XMLPacket))[0])
        # # print('pitch',FlightPitchDegree,GimbalPitchDegree)
        # # yaw=(FlightYawDegree+GimbalYawDegree+720)%360
        # # pitch=(FlightPitchDegree+GimbalPitchDegree+720)%360
        # # roll=(FlightRollDegree+GimbalRollDegree+720)%360
        # yaw = (FlightYawDegree + 360) % 360
        # # pitch=(FlightPitchDegree+360)%360
        # # roll=(FlightRollDegree+360)%360
        # # print('yaw', yaw)
        # yaw = (GimbalYawDegree + 360) % 360
        # pitch = (GimbalPitchDegree + 360) % 360
        # roll = (GimbalRollDegree + 360) % 360
        return pitch, yaw, roll  # 俯仰角，偏航角，翻滚角

    # 获取图片中心经纬度
    def get_center_lat_lon(self):
        camereLat, cameraLon = self.get_camera_lat_lon()
        pitch, yaw, roll = self.get_degree_info()
        absoluteAltitude, relativeAltitude = self.get_altitude()
        if pitch <= 180:
            print("俯仰角向上，可能不是拍摄地面图片，或存在俯仰角计算错误")
            return None
        degree = math.radians(pitch - 270)
        # print(degree)
        distance = float(relativeAltitude) * math.tan(degree) / 1000
        # print(distance)
        try:
            start = geopy.Point(camereLat, cameraLon)
            # print(start.format_decimal())
            d = geopy.distance.great_circle()
            return d.destination(point=start, bearing=yaw, distance=distance)
        except:
            print('计算失败')
            return None

    # 图片逆时针旋转 x 度后正上与正北重合
    def get_degree_to_north(self):
        orientation = self.get_orientation()
        # print(orientation)
        degree = self.get_degree_info()[1]
        # print('degree ot north', degree)
        if (orientation == 3):
            degree += 180
        elif (orientation == 6):
            degree -= 90
        elif (orientation == 8):
            degree += 90
        return -(degree + 360) % 360

    # 计算图片四个角的经纬度
    # 4 3
    # 1 2
    # def get_angles_lat_lon(self, verticalFov=VerticalFov, levelFov=LevelFov):
    #     pitch, yaw, roll = self.get_degree_info()
    #     relativeAltitude = self.get_altitude()[1]

    #     updeg = math.radians(pitch - 270 + verticalFov / 2)
    #     downdeg = math.radians(270 - pitch + verticalFov / 2)
    #     leftdeg = math.radians(roll + levelFov / 2)
    #     rightdeg = math.radians(-roll + levelFov / 2)
    #     # print(updeg, downdeg, leftdeg, rightdeg)
    #     updis = relativeAltitude * math.tan(updeg) / 1000
    #     downdis = relativeAltitude * math.tan(downdeg) / 1000
    #     leftdis = relativeAltitude * math.tan(leftdeg) / 1000
    #     rightdis = relativeAltitude * math.tan(rightdeg) / 1000
    #     # print(updis, downdis, leftdis, rightdis)

    #     camereLat, cameraLon = self.get_camera_lat_lon()
    #     #print('cameraLat,cameraLon',camereLat,cameraLon)

    #     start = geopy.Point(camereLat, cameraLon)
    #     d = geopy.distance.great_circle()
    #     # print('yaw', yaw)

    #     angle4 = d.destination(start, self.cal_degree(yaw, leftdis, updis),
    #                            math.sqrt(updis * updis + leftdis * leftdis))

    #     angle3 = d.destination(start, self.cal_degree(yaw, -rightdis, updis),
    #                            math.sqrt(updis * updis + rightdis * rightdis))

    #     angle1 = d.destination(start, self.cal_degree(yaw, leftdis, -downdis),
    #                            math.sqrt(leftdis * leftdis + downdis * downdis))

    #     angle2 = d.destination(start, self.cal_degree(yaw, -rightdis, -downdis),
    #                            math.sqrt(rightdis * rightdis + downdis * downdis))

    #     return angle1, angle2, angle3, angle4

    #给图像画出中心线后输出
    def show_img(self):
        img = cv2.imread(self.file_name)
        shape = img.shape
        # print(shape)
        x = int(shape[0] / 2)
        y = int(shape[1] / 2)
        cv2.line(img, (0, x), (shape[1], x), (255, 0, 0), 10)
        cv2.line(img, (y, 0), (y, shape[0]), (255, 0, 0), 10)
        # cv2.imshow('output',img)
        cv2.waitKey(0)
        path = self.file_name[0:-4]
        # print(path)
        cv2.imwrite(path + '_o.jpg', img)
        
    #图像叠加后输出
    # w :可见光图权重
    # w_r :热成像图权重
    # 输出位置 ../../output/test(num).jpg
    def show_over_lay_image(self,w,w_r):
        num = int(self.file_name[-8:-4])
        num -= 1
        file_name_R = self.file_name[:-8] + '{:04}'.format(num) + '_R.JPG'
        print(file_name_R)
        img = cv2.imread(self.file_name)
        imgr = cv2.imread(file_name_R)
        imgrx = int(2000 * math.tan(math.radians(16)) / math.tan(math.radians(28.56)))
        imgry = int(+1500 * math.tan(math.radians(13)) / math.tan(math.radians(21.22))+0.5)
        # print('imgx,imgy',imgrx,imgry)
        imgry=920
        imgrx=1150
        # imgry=int(imgrx/640*512)
        # imgrx=int(imgry/512*640+0.5)
        # print(imgrx)
        # print(imgry)
        yaw = self.get_degree_info()[1]
        yaw = math.radians((yaw + 70 + 90) % 360)
        # print(yaw*180/math.pi)
        # dy = 30 * math.cos(yaw)
        # dx = -30 * math.sin(yaw)
        dx=15
        dy=0
        print(dx)
        print(dy)
        x = int(1500 + dx - imgry / 2)  # 1500-256
        y = int(2000 + dy - imgrx / 2)  # 2000-320
        print('x,y',x,y)
        # cv2.imshow('imgr',imgr)
        # cv2.waitKey(0)
        imgr = cv2.resize(imgr, (imgrx, imgry))
        iro = img[x:x + imgry, y:y + imgrx]
        dst = cv2.addWeighted(imgr, w_r, iro, w, 0)
        img[x:x + imgry, y:y + imgrx] = dst
        # cv2.imwrite('../../output/test' + '{:04}'.format(num+1) + '.jpg', img)
        cv2.imwrite('../../output/test' + '{:04}'.format(num+1) + '.jpg', img)
        return [[y+imgrx,x],[y+imgrx,x+imgry],[y,x+imgry],[y,x]]

    def get_Time(self):
        EXIF_Date = self.tags["EXIF DateTimeOriginal"].printable
        EXIF_Date=list(EXIF_Date)
        EXIF_Date[4]='-'
        EXIF_Date[7]='-'
        EXIF_Date=''.join(EXIF_Date)
        return EXIF_Date

if __name__ == '__main__':
    # print(math.sqrt(15 * 15 + 25 * 25))
    # print(math.atan2(15, 25) * 180 / math.pi)
    # cv2.imread('unTreatedImg/DJI_0124.jpg')
    # imageFileName = 'unTreatedImg/DJI_0054.jpg'
    testImgPath = "thermal_QingDao/img_firespot_alter/0001_W.JPG"
    # testImgPath = r'./unTreatedImg/DJI_0002.jpg'
    testImg = ImageInfo(testImgPath)
    print(testImg.get_camera_lat_lon())
    print(testImg.get_Time())
    
    
    
    # # imageFileName = '../../img/DJI_0649.jpg'
    # # imageFileName = 'img/t4.jpg'
    # imageInfo = ImageInfo(imageFileName)
    # imageInfo.get_Time()
    # print(imageInfo.get_center_lat_lon().format_decimal())
    # print(imageInfo.get_altitude())
    print(testImg.get_altitude())
    # # print(imageInfo.get_camera_lat_lon())
    # print('degree',imageInfo.get_degree_info())
    # # print(imageInfo.get_center_lat_lon())


    # #
    # # print(imageInfo.get_center_lat_lon().format_decimal())
    # # print(imageInfo.get_degree_to_north())
    # angles = imageInfo.get_angles_lat_lon(VerticalFov,LevelFov)
    # for angle in angles:
    #     print(angle.format_decimal())
    # # imageInfo.show_img()
    # #
    # # angles=imageInfo.get_angles_lat_lon(20,25)
    # # print(VerticalFov * VerticalPixel_R / VerticalPixel)
    # # for angle in angles:
    # #     print(angle.format_decimal())
    # # imageInfo.show_img()
    # imageInfo.show_over_lay_image(0,1)
    # cv2.waitKey(0)

# (110.0, 100.0)
# 49
# ('2020:07:12 15:10:07', 30.756988525333334, 120.1887969968889)
# (270.099998, 82.800003, 0.0)
# 30.756988525333334, 120.1887969968889
# 30.756988722053812, 120.18879880897302

# 热成像
# 48R
# (110.0, 100.0)
# ('2020:07:12 15:10:07', 30.756988525333334, 120.1887969968889)
# (270.099998, 84.40000199999997, 0.0)
# 30.756988525333334, 120.1887969968889
# 30.756988678497457, 120.1887988146583

# 46R
# (109.0, 99.0)
# ('2020:07:12 15:10:05', 30.756978988444445, 120.18875885022223)
# (270.099998, 111.199997, 0.0)
# 30.756978988444445, 120.18875885022223
# 30.7569784265217, 120.18876053607016

# 47
# (109.0, 99.0)
# ('2020:07:12 15:10:05', 30.756978988444445, 120.18875885022223)
# (270.099998, 111.199997, 0.0)
# 30.756978988444445, 120.18875885022223
# 30.7569784265217, 120.18876053607016


        
# exifrw(savepath,path)
