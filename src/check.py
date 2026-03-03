import os
print("小八视力检查X光片")
user_home=os.path.expanduser("~")
desktops=[
    os.path.join(user_home,"Desktop"),
    os.path.join(user_home,"OneDrive","Desktop"),
    r"C:\Users\Public\Desktop",
    "D:\\"
]
for desktop in desktops:
    if not os.path.exists(desktop):
        print("找不到路径{desktop}")
        continue
    print(f"\n正在深度扫描：{desktop}")
    try:
        files=os.listdir(desktop)
        count=0
        for f in files:
            if f.endswith(('.lnk','.exe')):
                f_lower=f.lower()
                if 'qq' in f_lower or 'wechat' in f_lower or '微信' in f_lower:
                    print(f"发现目标：{f}")
                    count+=1
        if count==0:
            print("啥也没找到")
    except Exception as e:
        print("文件夹读取失败")
print("\n扫描结束")