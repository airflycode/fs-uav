# merge data
import numpy as np

# data = [[10, 20, 0, 25.5],
#         [11, 21, 0, 22.3],
#         [12, 22, 0, 24.8],
#         [13, 23, 0, 23.7],
#         [15, 25, 0, 26.1],
#         [16, 26, 0, 27.6],
#         [17, 27, 0, 27.0],
#         [18, 28, 0, 28.2],
#         [20, 30, 0, 24.9],
#         [21, 31, 0, 26.3],
#         [22, 32, 0, 25.8],
#         [23, 33, 0, 25.1],
#         [25, 35, 0, 26.7],
#         [26, 36, 0, 27.2],
#         [27, 37, 0, 25.6],
#         [28, 38, 0, 28.5]]
        
# data = [[16, 26, 0, 27.6],
#         [17, 27, 0, 27.0],
#         [336, 662,    0,  171.8],
#         [336,  664,    0,  107.2],
#         [18, 28, 0, 28.2],
#         [20, 30, 0, 24.9],
#         [338,  662,    0,   99.4]]
data = [[16, 26, 0, 27.6],
        [57, 27, 0, 27.0]]

data = np.array(data)

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


# ppOut = merge_pixels(data,10)
# print(ppOut)


# filename = "DJI_20230331142919_0005_T.JPG"
# imgName = filename[:filename.index("_T")]
# print(imgName)
import cv2
# imgName = "DJI_20230331142744_0003"
# imgT = cv2.imread("DJI_20230331142744_0003_T.JPG")

# snip_len = 75

# # data = [[336.0, 662.0, 0.0, 171.8],
# #         [642.0, 511.0, 0.0, 171.8]]

# data = [[1000.0, 662.0, 0.0, 171.8],
#         [642.0, 20.0, 0.0, 171.8]]

# pos = []
# for d in data:
#     x = d[0]
#     y = d[1]
#     pos.append([x,y])

# snip_pos = []
# for i,p in enumerate(pos):
#     print(i,p)
#     xmin = int(p[1] - snip_len) if int(p[1] - snip_len) >=0 else 0  
#     xmax = int(p[1] + snip_len) if int(p[1] + snip_len) <=1280 else 1280
#     ymin = int(p[0] - snip_len) if int(p[0] - snip_len) >=0 else 0
#     ymax = int(p[0] + snip_len) if int(p[0] + snip_len) <= 1024 else 1024
#     snip_img = imgT[ymin:ymax,xmin:xmax]
#     cv2.imwrite(imgName+"_S"+str(i)+".JPG",snip_img)



data = [[10, 20, 0, 25],
        [11, 21, 0, 22],
        [12, 22, 0, 24],
        [13, 23, 0, 23],
        [15, 25, 0, 26],
        [16, 26, 0, 27],
        [17, 27, 0, 27],
        [18, 28, 0, 28],
        [20, 30, 0, 24],
        [21, 31, 0, 26],
        [22, 32, 0, 25],
        [23, 33, 0, 25],
        [25, 35, 0, 26],
        [26, 36, 0, 27],
        [27, 38, 0, 25],
        [28, 38, 0, 28]]

# data = np.array(data)
# ppmax = []
# for i in np.where(data == data.max()):
#     i = list(i)
#     i.append(data.max())
#     ppmax.append(i)
#     # ppmax.append(data.max())
# print(ppmax)




# imgName = "DJI_20230427155506_0005_W"
# nameAttr = imgName[-6:-1]
LOCAL_UNTREAT = "untreatedImg/"
filesPath = LOCAL_UNTREAT+"71b31487-55bf-4330-bb1c-caca5f460fe1/DJI_202304271553_013_71b31487-55bf-4330-bb1c-caca5f460fe1/"
    

# print(imgName, nameAttr)
import glob
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

imgNames = find_all_files(filesPath)