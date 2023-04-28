    
from utils.minioUtil import MinioClient
from utils.mysqlUtil import MysqlClient
from main import doSingleImg, find_all_files
import os

# SUFFIXES = ".jpeg"
SUFFIXES = ".JPG"
LOCAL_UNTREAT = "untreatedImg/"
LOCAL_RAW = "rawImg/"
LOCAL_SNIP = "snipImg/"
LOCAL_JSON = "fire_data_json/"
LOCAL_RECT = "rectImg/"



# # 检测可用性：
# imgName = "DJI_20230331142744_0003"
# # imgName = "DJI_20230331142802_0004"
# filesName = "img_test"
# # imgName = "DJI_20230331142919_0005"
# imgPath = "./thermal_QingDao/img_test/IMG_M30T/"+imgName+"_W.JPG"
# imgTpath = "./thermal_QingDao/img_test/IMG_M30T/"+imgName+"_T.JPG"
# jsonPath = LOCAL_JSON+imgName+"_F.json"

filesPath = "/data/minio/cloud-bucket/wayline/3702440f-226b-4bb2-9ba8-6e1181be6212/DJI_202304211655_010_3702440f-226b-4bb2-9ba8-6e1181be6212/"

filesPath = "/data/image/3702440f-226b-4bb2-9ba8-6e1181be6212/DJI_202304211655_010_3702440f-226b-4bb2-9ba8-6e1181be6212/"
filesName = filesPath.split("/")
filesName = filesName[-2]
imgName = ""

dirs = [LOCAL_JSON+filesName,LOCAL_RAW+filesName,LOCAL_RECT+filesName]
for dir in dirs:
    if not os.path.exists(dir):
        os.makedirs(dir)
imgNames = find_all_files(filesPath) 
    
for imgName in imgNames:
    imgWPath = filesPath+imgName+"_W"+SUFFIXES
    imgTpath = filesPath+imgName+"_T"+SUFFIXES
    jsonPath = LOCAL_JSON+filesName+"/"+imgName+"_F.json"


    repo_data = doSingleImg(imgWPath,imgTpath,imgName,filesName)
    print(repo_data)

client = MysqlClient(True, base_path='/home/fushan/fs_fire_detect/rectImg')
client.deal_data(list([repo_data]))    

# filesPath = "/data/minio/cloud-bucket/wayline/3702440f-226b-4bb2-9ba8-6e1181be6212/DJI_202304211655_010_3702440f-226b-4bb2-9ba8-6e1181be6212/"
filesPath = "/data/image/3702440f-226b-4bb2-9ba8-6e1181be6212/DJI_202304211655_010_3702440f-226b-4bb2-9ba8-6e1181be6212/"
filesName = filesPath.split("/")
filesName = filesName[-2]
imgName = ""

