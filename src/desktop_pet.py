import tkinter as tk
import threading
import config
import os
import json
import re 
import shutil
import cv2
import sys
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
import base64  #将图片矩阵转换成字符串
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from pygame import mixer
from PIL import Image,ImageTk,ImageGrab
from io import BytesIO   #在内存中开辟空间存储图片
from openai import OpenAI
from tools_logic import read_local_file, run_cmd_command, write_local_file, run_python_script,search_knowledge_base
from wechat_skill import auto_collect_money, navigate_to_transfer_chat

if sys.stdout is not None:
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
        self.memory=self.load_memory()
        
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
            resize_bg=raw_chat_bg.resize((600,720),Image.Resampling.LANCZOS)
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
        self.chat_window.geometry("600x720")
        #self.chat_window.attributes('-alpha',0.7) //透明设置

        #taffy背景放置底层
        if hasattr(self,'chat_bg_photo') and self.chat_bg_photo:
            bg_label=tk.Label(self.chat_window,image=self.chat_bg_photo,bd=0)
            bg_label.place(relwidth=1,relheight=1)
 
        input_frame = tk.Frame(self.chat_window)
        input_frame.pack(side='bottom',fill='x', padx=20, pady=20)

        #发送按钮
        send_btn=tk.Button(input_frame,text="发送",font=("微软雅黑", 10),command=self.send_message)
        send_btn.pack(side='right',padx=5)

        #麦克风按钮
        self.record_btn=tk.Button(input_frame,text="🎤录音(F2)",command=self.toggle_recording)
        self.record_btn.pack(side='right',padx=5)
        self.chat_window.bind("<F2>",self.toggle_recording)

        #切换音色
        self.voice_btn=tk.Button(input_frame,text="🔄音色:小八(F3)",command=self.toggle_voice)
        self.voice_btn.pack(side='right',padx=5)
        self.chat_window.bind("<F3>",self.toggle_voice)

        #输入框
        self.user_input=tk.Entry(input_frame,relief='flat',font=("微软雅黑", 13))
        self.user_input.pack(side='left',fill='x',expand=True,ipady=6)
        self.user_input.bind("<Return>",lambda event:self.send_message())

        #聊天记录
        self.chat_history=tk.Text(self.chat_window,bg='#ffffff',font=("微软雅黑",12),relief='flat')
        self.chat_history.pack(side='top',padx=20,pady=20,fill='both',expand=True)
    
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
    #ai回复
    def get_ai_reply(self, user_msg):
        try:
            local_match = re.search(r'(打开|启动|玩一下|玩|用|开一下)\s*([a-zA-Z0-9\u4e00-\u9fa5]+)', user_msg)
            if local_match:
                app_name = local_match.group(2)
                result_msg = self.open_app_from_desktop(app_name)
                if "找到啦" in result_msg:
                    print(f"跳过服务器直接执行：{app_name}")
                    self.root.after(0, self.show_reply, result_msg)
                    return
                else:
                    print(f"⚡ 小脑猜错了({app_name})，转交云端大脑分析...")
        
            #打开桌面软件/快捷方式
            vision_keywords = ["截图", "看屏幕", "帮我看代码", "屏幕上的报错", "这张图", "画面里", "你看看屏幕"]
            is_vision_mode = False  #聊天与识屏模式分流
            
            if any(keyword in user_msg for keyword in vision_keywords):
                is_vision_mode = True
                base64_img = self.capture_screen_as_base64()
                vision_message = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_msg},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_img}"
                            }
                        }
                    ]
                }
                print("👀小八已将屏幕画面传输给云端大脑！")
                self.memory.append({"role": "user", "content": user_msg})
                temp_message = self.memory[:-1] + [vision_message]
            else:
                self.memory.append({"role": "user", "content": user_msg})

            if len(self.memory) > 20:
                self.memory = [self.memory[0]] + self.memory[-10:]
                
            #工具说明
            tools = [
                #工具1：启动软件
                {
                    "type": "function",
                    "function": {
                        "name": "open_app_from_desktop",
                        "description": "当且仅当用户明确要求打开、启动某个桌面软件或应用时（如：帮我打开微信、启动QQ音乐），才调用此工具。普通的日常闲聊绝对不要调用。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "app_name": {
                                    "type": "string",
                                    "description": "软件名，比如'微信','QQ'，'QQ音乐'"
                                }
                            },
                            "required": ["app_name"]
                        }
                    }
                },
                #工具2：读取本地文件
                {
                    "type": "function",
                    "function": {
                        "name": "read_local_file",
                        "description": "读取本地文件内容（如README.md等）",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "file_path": {"type": "string", "description": "文件相对路径"}
                            },
                            "required": ["file_path"]
                        }
                    }
                },
                #工具3：使用cmd命令
                {
                    "type": "function",
                    "function": {
                        "name": "run_cmd_command",
                        "description": "在宿主机的命令行终端执行自动化脚本或系统命令（如git操作，查询系统信息等）。🚨注意：宿主机为Windows环境，请生成兼容cmd或powershell的指令。🚨核心准则：如果主人要求你删除、修改、读取某个名称模糊的文件/文件夹，或者让你找东西，你绝对不能盲目猜测全名！你必须分两步走：第一步，先调用此工具执行 'dir' 命令查看当前目录的真实文件列表；第二步，根据终端返回的列表精准找到真实的全名后，再次调用此工具执行最终的操作命令！",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "需要执行的具体终端命令，例如'ipconfig'或'dir'"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                },
                #工具4：读写与修改文件到本地
                {
                    "type":"function",
                    "function":{
                        "name":"write_local_file",
                        "description":"当主人要求你写代码，修改文件，创建脚本时调用。你会将生成的代码写入本地文件",
                        "parameters":{
                            "type":"object",
                            "properties":{
                                "file_path":{"type":"string","description":"要保存的文件相对路径，比如'test.py'"},
                                "content":{"type":"string","description":"要写入的完整代码或文本内容"}
                             }, 
                        "required":["file_path","content"]
                        }
                    }
                },
                #工具5：运行或测试脚本：
                {
                    "type":"function",
                    "function":{
                        "name":"run_python_script",
                        "description":"当主人要求你运行、执行、测试某个Python脚本时调用。它会返回终端的输出结果或报错信息。🚨【核心自愈准则】：如果你收到 'ModuleNotFoundError' 或 'No module named...' 的报错，绝对不要放弃！这说明缺少第三方库。此时你必须立刻调用 'run_cmd_command' 工具，使用 'pip install 库名' 命令将缺失的库安装到宿主机！安装成功后，你必须再次调用本工具重新运行脚本，直到完美成功为止！",
                        "parameters":{
                            "type":"object",
                            "properties":{
                                "file_path":{"type":"string","description":"要运行的脚本相对路径，比如'test.py'"}
                            },
                            "required":["file_path"]
                        }
                    }
                },
                #工具6：微信自动收款
                {
                    "type":"function",
                    "function":{
                        "name":"collect_wechat_money",
                        "description":"主人让你帮忙收钱、看微信红包、领转账时调用此工具。此工具会自动操作微信，识别并收取所有未领取的转账。",
                        "parameters": {
                            "type": "object",
                            "properties": {}, # 收钱不需要参数，直接干就完了
                        }
                    }
                },
                #工具7：RAG向量检索记忆
                {
                    "type":"function",
                    "function":{
                        "name":"search_knowledge_base",
                        "description": "当主人询问你的设定、主人的个人信息、过去的课设经历、或者你常识不知道的本地私有知识时，必须调用此工具。",
                        "parameters": {
                            "type":"object",
                            "properties":{
                                "query":{
                                    "type":"string",
                                    "description":"检索关键词，如'主人是谁'、'贪吃蛇项目要求'等"
                                }
                            },
                            "required":["query"]
                        }
                    }
                }
            ]
            
            if is_vision_mode:
                print("👀纯视觉，不用工具")
                response = self.client.chat.completions.create(
                    model="Qwen/Qwen2.5-VL-72B-Instruct",
                    messages=temp_message,
                    stream=False,
                )
                reply = response.choices[0].message.content
                self.memory.append({"role": "assistant", "content": reply})
                self.save_memory()
                self.root.after(0, self.show_reply, reply)
                self.speak_text(reply)
                return
            #Agent任务循环
            else:
                max_loop = 8 #防死锁，最多连续调用五次工具
                current_loop = 0
                
                while current_loop < max_loop:
                    current_loop += 1
                    print(f"🔄 第{current_loop}轮工具调用，正在等待云端大脑的决策...")
                    
                    response = self.client.chat.completions.create(
                        model=config.MODEL_NAME,
                        messages=self.memory,
                        stream=False,
                        tools=tools 
                    )
                    
                    #获取ai决策
                    response_msg = response.choices[0].message
                    
                    # 判断是否需要调用工具
                    if response_msg.tool_calls:
                        clean_tool_calls = []
                        unique_tools = []
                        seen_sigs = set()

                        # 1. 遍历并清洗工具 (这个 for 循环负责去重)
                        for tc in response_msg.tool_calls:
                            # 把id给大模型
                            tc_id = tc.id if tc.id else f"call_{len(seen_sigs)}"
                            # 准备上锁
                            sig = f"{tc.function.name}_{tc.function.arguments}"
                            if sig not in seen_sigs:
                                seen_sigs.add(sig)
                                tc.id = tc_id
                                unique_tools.append(tc)
                                clean_tool_calls.append({
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                })
                            else:
                                print(f"🛡️ 拦截到大模型复读机抽风，跳过重复动作: {tc.function.name}")

                        assitant_msg = {
                            "role": "assistant",
                            "content": response_msg.content,
                            "tool_calls": clean_tool_calls
                        }
                            
                        # 不管有没有 content，都要把记忆存进去！
                        self.memory.append(assitant_msg)
                        
                        for tool_call in unique_tools:
                            func_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)

                            #tool1：打开桌面软件
                            if func_name == "open_app_from_desktop":
                                app_name = args.get("app_name")
                                result_msg = self.open_app_from_desktop(app_name)
                                self.root.after(0, self.show_reply, result_msg)
                                self.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(result_msg)})

                            #tool2:读取电脑文件
                            elif func_name == "read_local_file":
                                file_path = args.get("file_path")
                                print(f"📖 小八正在翻阅文件：{file_path}...")
                                file_content = read_local_file(file_path)
                                self.memory.append({"role": "tool", "tool_call_id": tool_call.id,"content": str(file_content)})
                                print("🧠 小八已拿到文件内容，正在总结...")
                            
                            #tool3:处理cmd逻辑
                            elif func_name == "run_cmd_command":
                                cmd_to_run = args.get("command")
                                print(f"⌨️ 小八正在疯狂敲击键盘执行: {cmd_to_run}")
                                cmd_result = run_cmd_command(cmd_to_run)
                                self.memory.append({"role": "tool", "tool_call_id": tool_call.id,"content": str(cmd_result)})
                                print("🧠 小八已拿到终端输出，正在进行二次总结...")

                            #tool4:写文件
                            elif func_name=="write_local_file":
                                file_path=args.get("file_path")
                                content=args.get("content")
                                print(f"✍️ 小八正在奋笔疾书，写代码到：{file_path}...")
                                write_result=write_local_file(file_path,content)
                                self.memory.append({"role":"tool","tool_call_id":tool_call.id,"content":str(write_result)})
                                print(f"🧠 小八写入完毕：{write_result}")

                            #tool5:跑脚本检查
                            elif func_name=="run_python_script":
                                file_path=args.get("file_path")
                                print(f"🚀 小八正在启动脚本验证：{file_path}")
                                run_result=run_python_script(file_path)
                                self.memory.append({"role":"tool","tool_call_id":tool_call.id,"content":str(run_result)})
                                print("🧠 小八拿到运行结果，准备汇报...")
                            
                            #tool6:微信自动收款
                            elif func_name=="collect_wechat_money":
                                print("💰 小八收到搞钱指令！正在前往案发现场...")
                                self.root.after(0, self.show_reply, "小八收到！这就去帮主人看看有没有小钱钱！(｡･ω･｡)")
                                navigate_to_transfer_chat()
                                money_result = auto_collect_money()
                                self.memory.append({"role": "tool", "tool_call_id": tool_call.id,"content": str(money_result)})
                                print(f"🧠 小八收钱完毕：{money_result}")
                            
                            #tool7:RAG记忆检索
                            elif func_name=="search_knowledge_base":
                                query=args.get("query")
                                print(f"🧠 小八正在潜入深层记忆海，搜索关键词：【{query}】...")
                                rag_result=search_knowledge_base(query)
                                self.memory.append({"role":"tool","tool_call_id":tool_call.id,"content":str(rag_result)})

                            else:
                                print(f"⚠️ 云端大脑试图使用不存在的工具：{func_name}！已强制拦截！")
                                error_msg = f"Error: 根本没有 '{func_name}' 这个工具。请使用正确的工具（如 run_cmd_command）去执行复制或删除操作。"
                                self.memory.append({"role": "tool", "tool_call_id": tool_call.id, "content": error_msg})
                        continue # 一轮工具选用并执行完毕，跳回 while 开始新一轮循环
                    else:
                        #若不调工具，直接回复（闲聊或总结）
                        reply = response_msg.content
                        if not reply:
                            reply = "呜...小八走神了，没听清你在说什么(；ω；)"
                       
                        #一般聊天中暴力提取（兼容老旧逻辑）
                        if "open_app_from_desktop" in reply and "{" in reply:
                            try:
                                start_idx = reply.find('{')
                                end_idx = reply.rfind('}') + 1
                                json_str = reply[start_idx:end_idx]
                                args = json.loads(json_str)    
                                app_name = args.get("app_name")
                                result_msg = self.open_app_from_desktop(app_name)
                                self.root.after(0, self.show_reply, result_msg)
                                return
                            except Exception as parse_error:
                                print(f"暴力提取失败:{parse_error}")
                                pass

                        # 把官方完整的 message 存进记忆
                        self.memory.append({
                        "role": "assistant",
                        "content": reply or ""
                      })
                        self.save_memory()
                        self.root.after(0, self.show_reply, reply)
                        self.speak_text(reply)
                        break

                # 🚨 兜底机制：跟 while 垂直对齐
                if current_loop >= max_loop:
                    print("⚠️ 已达到最大工具调用次数，停止循环以防死锁。")
                    error_reply = "呜...步骤太复杂了，小八的脑容量要爆炸啦，强制中断工作(x_x)"
                    self.root.after(0, self.show_reply, error_reply)
                    self.speak_text(error_reply)

        except Exception as e:
            print(f"API Error:{e}")
            self.root.after(0, self.show_reply, "呜...脑子短路了(x_x)")

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
                frame=frame.zoom(3,3).subsample(2,2)
                frames.append(frame)
        except tk.TclError:
            pass
        return frames
    
        #长期记忆模块
        #读取记忆
    def load_memory(self):
        """
        开机启动，读取昨天记忆
        """
        memory_path="config/memory.json"#记忆文件路径
        try:
            if os.path.exists(memory_path):
                with open(memory_path,'r',encoding='utf-8') as f:#读取记忆文件
                    saved_memory=json.load(f)#读取记忆
                if len(saved_memory)>0 and saved_memory[0].get("role")=="system":
                    saved_memory[0]["content"]=config.PERSONA
                    print("🧠 海马体接入成功！小八想起了之前的事情！")
                    return saved_memory
        except Exception as e:
            print(f"⚠️ 记忆读取失败，小八失忆了: {e}")
            #倘若没有历史记忆:
        print("🌱 这是一个全新的小八，记忆库初始化完成。")
        return [{"role":"system","content":config.PERSONA}]
    #更新记忆
    def save_memory(self):
        """运行ing，将最新记忆刻入本地大脑"""
        memory_path="config/memory.json"
        try:
            if len(self.memory)>21:
                self.memory=[self.memory[0]]+self.memory[-20:]

            with open(memory_path,'w',encoding='utf-8') as f:
                json.dump(self.memory,f,ensure_ascii=False,indent=2)
        except Exception as e:
            print(f"⚠️ 记忆刻录失败: {e}")
    
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
        xml_name='model/haarcascade_frontalface_default.xml'
        if not os.path.exists(xml_name):
            original_path=cv2.data.haarcascades+xml_name
            shutil.copy(original_path,xml_name)
        
        face_cascade=cv2.CascadeClassifier(xml_name)
        cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)

        #状态机
        last_state=None
        miss_count=0
        max_miss=15
        
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
                self.wav_path="recordings/temp_record.wav"
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
            wav_path=os.path.abspath("recordings/reply.wav")
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