b = b"\x3c\x2f\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x3e"
a = b"\x3c\x72\x64\x66\x3a\x44\x65\x73\x63\x72\x69\x70\x74\x69\x6f\x6e\x20"

def readDJI(imgPath):
    # img = open("thermal_QingDao/img_firespot_alter/0001_W.JPG", 'rb')
    img = open(imgPath, 'rb')
    data = bytearray()
    flag = False
    for i in img.readlines():
        if a in i:
            flag = True
        if flag:
            data += i
        if b in i:
            break
    if len(data) > 0:
        data = str(data.decode('ascii'))
        print(data)
        lines = list(filter(lambda x: 'drone-dji:' in x, data.split("\n")))
        dj_data_dict = {}
        for d in lines:
            d = d.strip()[10:]
            k, v = d.split("=")
            print(f"{k} : {v}")
            dj_data_dict[k] = v
        return dj_data_dict

# readDJI("thermal_QingDao/img_firespot_alter/0001_W.JPG")