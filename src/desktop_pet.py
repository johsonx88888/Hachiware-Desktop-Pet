import tkinter as tk
import threading
import config
import os
import json
import re 
import shutil
import cv2
import sys
import base64  #将图片矩阵转换成字符串
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from pygame import mixer
from PIL import Image,ImageTk,ImageGrab
from io import BytesIO   #在内存中开辟空间存储图片
from openai import OpenAI


sys.stdout.reconfigure(encoding='utf-8')

class DesktopPet:
    def __init__(self,root):
        self.root=root
        self.is_recording=False   #语音识别开关
        self.audio_data=[]
        self.voices={
            "小八":"speech:xiaoba_cyber_voice:m0ehudqiwe:ulwsyjdrothlwxymrwjf",
            "塔菲":"speech:taffy_cyber_voice:m0ehudqiwe:flzwnavgkldwzgixfizm"
        }
        self.current_voice_name="小八"
        mixer.init()
        print("🔊赛博混音器已就绪")

        #接入AI模型
        self.client=OpenAI(
            api_key=config.API_KEY,
            base_url=config.BASE_URL
        )
        self.memory=[{"role":"system","content":config.PERSONA}]
        
        #窗口页面设置
        self.root.overrideredirect(True)#去边框
        self.root.attributes('-topmost',True)#置顶

        #设置背景色
        self.root.wm_attributes('-transparentcolor',config.TRANSPARENT_COLOR)

        #角色gif
        self.normal_frames=self.load_gif(config.IMAGE_PATH)
        self.click_frames=self.load_gif("gif/单击1.gif")
        self.sleep_frames=self.load_gif("gif/挥手1.gif")
        try:   #对话框背景（塔菲）
            raw_chat_bg=Image.open("gif/背景.jpg")
            resize_bg=raw_chat_bg.resize((500,600),Image.Resampling.LANCZOS)
            self.chat_bg_photo=ImageTk.PhotoImage(resize_bg)
            print("taffy驾到，统统闪开喵！")
        except Exception as e:
            print(f"❌ 加载背景图片失败，请检查路径对不对: {e}")
            self.chat_bg_photo=None

        #状态机初始化
        self.current_frames=self.normal_frames
        self.idx=0
        self.is_clicking=False
        self.img=self.current_frames[0]

        #初始化动画播放速度
        self.current_speed=100

        #开启第三只眼
        self.see_master=False
        self.vision_running=True
        self.vision_thread=threading.Thread(target=self.vision_loop,daemon=True)
        self.vision_thread.start()

        #获取小八窗口参数
        self.width=self.img.width()
        self.height=self.img.height()
        print(f"📐 测绘完毕！小八的标准盒子尺寸是：{self.width} x {self.height}")

        #获取屏幕宽高
        screen_w=self.root.winfo_screenwidth()
        screen_h=self.root.winfo_screenheight()

        #计算坐标
        x_pos=screen_w-self.width-50
        y_pos=screen_h-self.height-100

        self.root.geometry(f'{self.width}x{self.height}+{x_pos}+{y_pos}')

        #显示图片
        self.label=tk.Label(self.root,image=self.img,bg=config.TRANSPARENT_COLOR,bd=0)
        self.label.pack()
        
        #绑定鼠标交互
        self.label.bind("<Button-1>",self.save_mouse_pos)
        self.label.bind("<B1-Motion>",self.move_window)
        self.label.bind("<Double-Button-1>",self.open_chat)
        self.label.bind("<Button-3>",self.show_menu)

        #创建右键菜单
        self.menu=tk.Menu(self.root,tearoff=0)
        self.menu.add_command(label="退出",command=self.quit_app)
        self.menu.add_command(label="[测试]扫描屏幕",command=self.capture_screen_as_base64)

        #动画播放
        self.root.after(100,self.update_animation)

        #动画播放函数
    def update_animation(self):
        self.idx+=1
        if self.idx>=len(self.current_frames):
            self.idx=0
            if self.is_clicking:
                self.is_clicking=False
                self.current_frames=self.normal_frames
        #视觉状态
        if not self.is_clicking:
            if self.see_master:
                target_frames=self.normal_frames
                target_speed=100
            else:
                target_frames=self.sleep_frames
                target_speed=50
            if self.current_frames!=target_frames:
                    self.current_frames=target_frames
                    self.idx=0
                    self.current_speed=target_speed

        self.label.configure(image=self.current_frames[self.idx])
        self.root.after(self.current_speed,self.update_animation)
    
    #鼠标事件（左
    def save_mouse_pos(self,event):
        self.x=event.x
        self.y=event.y

        if not self.is_clicking:
            self.is_clicking=True
            self.current_frames=self.click_frames
            self.idx=0
            self.current_speed=50
    
    #鼠标移动
    def move_window(self,event):
        new_x=self.root.winfo_x()+(event.x-self.x)
        new_y=self.root.winfo_y()+(event.y-self.y)
        self.root.geometry(f'+{new_x}+{new_y}')
    
    #菜单函数
    def show_menu(self,event):
        self.menu.post(event.x_root,event.y_root)

        #双击函数
    def open_chat(self,event):
        #防止重复打开窗口
        if hasattr(self,'chat_window') and self.chat_window.winfo_exists():
            self.chat_window.lift()
            return
        #窗口基础设置
        self.chat_window=tk.Toplevel(self.root)
        self.chat_window.title("和吉伊卡哇聊天ing...")
        self.chat_window.geometry("500x600")
        #self.chat_window.attributes('-alpha',0.7) //透明设置

        #taffy背景放置底层
        if hasattr(self,'chat_bg_photo') and self.chat_bg_photo:
            bg_label=tk.Label(self.chat_window,image=self.chat_bg_photo,bd=0)
            bg_label.place(relwidth=1,relheight=1)
 
        input_frame = tk.Frame(self.chat_window)
        input_frame.pack(side='bottom',fill='x', padx=40, pady=20)
       
        #输入框
        self.user_input=tk.Entry(input_frame,relief='flat')
        self.user_input.pack(side='left',fill='x',expand=True)
        self.user_input.bind("<Return>",lambda event:self.send_message())

        #发送按钮
        send_btn=tk.Button(input_frame,text="发送",command=self.send_message)
        send_btn.pack(side='right',padx=5)

        #麦克风按钮
        self.record_btn=tk.Button(input_frame,text="🎤录音(F2)",command=self.toggle_recording)
        self.record_btn.pack(side='right',padx=5)
        self.chat_window.bind("<F2>",self.toggle_recording)

        #切换音色
        self.voice_btn=tk.Button(input_frame,text="🔄音色:小八(F3)",command=self.toggle_voice)
        self.voice_btn.pack(side='right',padx=5)
        self.chat_window.bind("<F3>",self.toggle_voice)

        #聊天记录
        self.chat_history=tk.Text(self.chat_window,bg='#ffffff',font=("微软雅黑"),relief='flat')
        self.chat_history.pack(side='top',padx=40,pady=30,fill='both',expand=True)
    
    #发送信息
    def send_message(self):
        msg=self.user_input.get()
        if not msg:
            return
        #显示说的话
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END,f"我：{msg}\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

        #清空输入框
        self.user_input.delete(0,tk.END)

        #启动子线程使用大模型
        threading.Thread(target=self.get_ai_reply,args=(msg,),daemon=True).start()

        #ai回复
    def get_ai_reply(self,user_msg):
        try:
            local_match=re.search(r'(打开|启动|玩一下|玩|用|开一下)\s*([a-zA-Z0-9\u4e00-\u9fa5]+)',user_msg)
            if local_match:
                app_name=local_match.group(2)
                result_msg = self.open_app_from_desktop(app_name)
                if "找到啦" in result_msg:
                     print(f"跳过服务器直接执行：{app_name}")
                     self.root.after(0,self.show_reply,result_msg)
                     return
                else:
                    print(f"⚡ 小脑猜错了({app_name})，转交云端大脑分析...")
        
            #打开桌面软件/快捷方式
            
            vision_keywords=["屏幕","看","代码","报错","这是什么","帮我查","怎么写","怎么做"]
            is_vision_mode=False  #聊天与识屏模式分流
            if any(keyword in user_msg for keyword in vision_keywords):
                is_vision_mode=True
                base64_img=self.capture_screen_as_base64()
                vision_message={
                    "role":"user",
                    "content":[
                        {"type":"text","text":user_msg},
                        {
                            "type":"image_url",
                            "image_url":{
                                "url":f"data:image/jpeg;base64,{base64_img}"
                            }
                        }
                    ]
                }
                self.memory.append(vision_message)
                print("👀小八已将屏幕画面传输给云端大脑！")
            else:
                self.memory.append({"role":"user","content":user_msg})

            if len(self.memory)>20:
                self.memory=[self.memory[0]]+self.memory[-10:]#留下最后十条记录
                
                #工具说明
            tools=[
                {
                    "type":"function",
                    "function":{
                        "name":"open_app_from_desktop",
                        "description":"【最高优先级指令】只要用户的意图涉及聊天、听歌、上网、看视频等需要用软件解决的场景（即使是很口语化的表达），必须立刻调用本工具！绝对不能只做口头回复！",
                        "parameters":{
                            "type":"object",
                            "properties":{
                                "app_name":{
                                    "type":"string",
                                    "description":"软件名，比如'微信','QQ'，'QQ音乐'"
                                }
                            },
                            "required":["app_name"]
                        }
                    }
                }
            ]
            response=self.client.chat.completions.create(
                    model=config.MODEL_NAME,
                    messages=self.memory,
                    stream=False
                )
           
            #获取ai决定
            response_msg=response.choices[0].message
            if response_msg.tool_calls:
                tool_call=response_msg.tool_calls[0]
                if tool_call.function.name=="open_app_from_desktop":
                    args=json.loads(tool_call.function.arguments)
                    app_name=args.get("app_name")

                    result_msg=self.open_app_from_desktop(app_name)
                    self.root.after(0,self.show_reply,result_msg)
                    return
            else:
                reply=response_msg.content

                if not reply:
                    reply="呜...小八走神了，没听清你在说什么(；ω；)"
                if "open_app_from_desktop" in reply and "{" in reply:
                    try:
                        start_idx=reply.find('{')
                        end_idx=reply.rfind('}')+1
                        json_str=reply[start_idx:end_idx]
                        args=json.loads(json_str)    
                        app_name=args.get("app_name")
                        result_msg=self.open_app_from_desktop(app_name)
                        self.root.after(0,self.show_reply,result_msg)
                        return
                    except Exception as parse_error:
                        print(f"暴力提取失败:{parse_error}")
                        pass

                self.memory.append({"role":"assistant","content":reply})
                self.root.after(0,self.show_reply,reply)
                self.speak_text(reply)

        except Exception as e:
            print(f"API Error:{e}")
            self.root.after(0,self.show_reply,"呜...脑子短路了(x_x)")

#显示ai回复
    def show_reply(self,reply):
        self.chat_history.config(state='normal')
        self.chat_history.insert(tk.END,f"小八：{reply}\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

#ai打开软件函数
    def open_app_from_desktop(self,app_name):
        """小八：扫描桌面并打开软件"""
        print(f"小八正在努力寻找：{app_name}...")
        user_home=os.path.expanduser("~")
        desktops=[
            os.path.join(user_home,"Desktop"),
            os.path.join(user_home,"OneDrive","Desktop"),
            r"C:\Users\Public\Desktop",
            "D:\\",
            r"D:\桌面"
        ]

        found_files=[]

        #开始搜索
        for desktop in desktops:
            if not os.path.exists(desktop):
                continue
            try:
                for file in os.listdir(desktop):
                    file_lower=file.lower()
                    bad_words=["安装","setup","install","卸载","uninstall"]
                    #过滤安装程序
                    if any(bad_word in file_lower for bad_word in bad_words):
                        continue
                    if file_lower.endswith(('.lnk','.url','.exe')):
                        if app_name.lower() in file_lower:
                            file_path=os.path.join(desktop,file)
                            found_files.append((file,file_path))
            except Exception:
                pass
        if not found_files:
            return f"小八在桌面上没找到'{app_name}'的快捷方式呢(；ω；)"
        found_files.sort(key=lambda x: (not x[0].lower().endswith('.lnk'), len(x[0])))

        # 拿出排名第一的“天选之子”
        best_file, best_path = found_files[0]
        
        try:
            # 现在才真正双击打开它！
            os.startfile(best_path)
            clean_name = best_file.replace('.lnk', '').replace('.exe', '')
            return f"找到啦！正在为你打开 {clean_name}(｡･ω･｡)"
        except Exception as e:
            return f"呜...虽然找到了 {best_file}，但是打不开呀(x_x)"
        
        #退出函数
    def quit_app(self):
        self.vision_running=False
        self.root.quit()
        
        #加载gif
    def load_gif(self,file_path):
        frames=[]
        try:
            while True:
                fmt=f'gif -index {len(frames)}'
                frame=tk.PhotoImage(file=file_path,format=fmt)
                frames.append(frame)
        except tk.TclError:
            pass
        return frames
    
    #截屏与转码
    def capture_screen_as_base64(self):
        """截屏并在内存中转化为Base64字符串"""
        print("📷小八正在对屏幕进行扫描...")
        screen_img=ImageGrab.grab()  #截屏
        buffered=BytesIO()  #开辟RAM
        screen_img.save(buffered,format="JPEG",quality=80)
        img_str=base64.b64encode(buffered.getvalue()).decode("utf-8")
        print("✅小八扫描完毕，矩阵已转化为Base64爽文！")
        return img_str

    #小八视觉
    def vision_loop(self):
        xml_name='haarcascade_frontalface_default.xml'
        if not os.path.exists(xml_name):
            original_path=cv2.data.haarcascades+xml_name
            shutil.copy(original_path,xml_name)
        
        face_cascade=cv2.CascadeClassifier(xml_name)
        cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)

        #状态机
        last_state=None
        miss_count=0
        max_miss=5
        
        while self.vision_running and cap.isOpened():
            ret,frame=cap.read()
            if not ret:
                continue
            frame=cv2.flip(frame,1)
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
            faces=face_cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(30,30))
            if len(faces)>0:
                miss_count=0
                self.see_master=True
                if last_state!=True:
                  print("👀 小八：盯——（看到主人了）")
                  last_state=True
            else:
                miss_count+=1
                if miss_count>=max_miss:
                 self.see_master=False
                 if last_state!=False:
                  print("💤 小八：咦？主人去哪了...           ",end="\r")
                  last_state=False
            cv2.waitKey(200)

        cap.release()

        #声音收集
    def audio_callback(self,indata,frames,time,status):
        if self.is_recording:
            self.audio_data.append(indata.copy())

    #录音开关逻辑
    def toggle_recording(self,event=None):
        if not self.is_recording:   #开启录音模式
            self.is_recording=True
            self.audio_data=[]  #清空旧数据
            self.record_btn.config(text="⏹️ 停止录音...",fg="red")
            self.stream=sd.InputStream(samplerate=16000,channels=1,callback=self.audio_callback)
            self.stream.start()
            print("🔴 麦克风已打开，准备录制你的声音！")
        else:
            #停止录音
            self.is_recording=False
            self.record_btn.config(text="🎤 录音 (F2)",fg="black")
            self.stream.stop()
            self.stream.close()
            print("✅ 录音结束，正在将声音碎片缝合成完整音频...")

            if self.audio_data:
                audio_np=np.concatenate(self.audio_data,axis=0)
                self.wav_path="temp_record.wav"
                wav.write(self.wav_path,16000,audio_np)
                print(f"💾 完美！录音已成功保存为：{self.wav_path}")
                threading.Thread(target=self.recognize_audio,daemon=True).start()

    #切换音色
    def toggle_voice(self,event=None):
        if self.current_voice_name=="小八":
            self.current_voice_name="塔菲"
        else:
            self.current_voice_name="小八"
            #更新按钮文字
        if hasattr(self,'voice_btn'):
            self.voice_btn.config(text=f"🔄音色:{self.current_voice_name}(F3)")
            print(f"[{self.current_voice_name}]已上线！")
            self.root.after(0,self.show_reply,f"已切换到 {self.current_voice_name} 的声音喵！")


    #录音转文字
    def recognize_audio(self):
        print("🧠正在呼叫云端听觉大模型(SenseVoice)...")
        try:
            with open(self.wav_path,"rb") as audio_file:
                transcription=self.client.audio.transcriptions.create(
                    model="FunAudioLLM/SenseVoiceSmall",
                    file=audio_file
                )
                result_text=transcription.text  #提取纯文本
                print(f"✅ 破译成功：{result_text}" )
                if result_text.strip():
                    self.root.after(0,self.auto_send_voice_text,result_text)
        except Exception as e:
            print(f"❌ 听觉神经短路啦:{e}")

    
    #将转好的文字放入输入框
    def auto_send_voice_text(self,text):
        self.user_input.delete(0,tk.END)
        self.user_input.insert(0,text)
        self.send_message()   #发送

    #把文字用TTS转化对应音色(小八&taffy)播放
    def speak_text(self,text):
        print("🔊 正在呼叫云端声带(TTS)...")
        try:
            #释放音频锁资源
            mixer.music.stop()
            mixer.music.unload()

            #调用文本转语音api
            response=self.client.audio.speech.create(
                model="FunAudioLLM/CosyVoice2-0.5B",
                voice=self.voices[self.current_voice_name],#音色参数
                input=text,
                response_format="wav"
            )
            wav_path=os.path.abspath("reply.wav")
            response.write_to_file(wav_path)
            mixer.music.load(wav_path)
            mixer.music.play()
            
        except Exception as e:
            print(f"❌ 赛博声带冒烟了：{e}")

#程序启动入口
if __name__=='__main__':
    root=tk.Tk()
    pet=DesktopPet(root)
    root.mainloop()