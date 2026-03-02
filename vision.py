import cv2
import os
import shutil

def main():
    xml_name='haarcascade_frontalface_default.xml'
    local_xml_name=xml_name
    if not os.path.exists(local_xml_name):
         oringinal_path=cv2.data.haarcascades+xml_name
         shutil.copy(oringinal_path,local_xml_name)
    face_cascade=cv2.CascadeClassifier(local_xml_name)

    cap=cv2.VideoCapture(0)

    if not cap.isOpened():
        print("小八打不开眼睛TVT...")
        return
    print("小八已睁眼！请把脸对准摄像头哦")
    while cap.isOpened():
        ret,frame=cap.read()
        if not ret:
            print("画面读取失败！")
            break

        frame=cv2.flip(frame,1)
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

        faces=face_cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(30,30))

        if len(faces)>0:
            print("看到主人啦！陪你一起敲代码！           ",end="\r")
            #画框
            for(x,y,w,h) in faces:
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
        else:
                print("主人呢？怎么不见了，那我要休眠了哦...               ",end="\r")

        cv2.imshow('小八的第三只眼',frame)
        if cv2.waitKey(5)&0xFF==27:
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__=="__main__":
    main()