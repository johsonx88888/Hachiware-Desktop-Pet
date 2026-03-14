import pyautogui    #模拟鼠标移动、点击、键盘敲击
import time         #强制程序暂停（sleep）,因为代码执行速度远快于窗口弹出的物理速度，必须留出缓冲时间
import subprocess   #静默启动宿主机的可执行文件
import pyperclip    #系统剪贴板交互

#开启紧急制动
pyautogui.FAILSAFE=True

print("🚀 警告：5秒后小八将接管你的键盘，请双手离开键盘和鼠标！")
print("💡 如果发生暴走，请立刻将鼠标甩到屏幕最角落！")
time.sleep(5)
print("正在打开记事本。。。")

subprocess.Popen(['notepad.exe'])
time.sleep(2)  #等待记事本打开再自动敲入文字内容
#模拟人类敲击键盘
print("⌨️ 小八开始疯狂输出...")
# interval=0.1 表示每个字母敲击间隔 0.1 秒
english_msg = "Hello Axin! I am Hachiware. "
pyperclip.copy(english_msg)   # 1. 把英文塞进剪贴板
pyautogui.hotkey('ctrl', 'v') # 2. 粘贴英文
pyautogui.press('enter')      # 3. 换行
chinese_msg="主人，我已成功接管你的键盘！"
pyperclip.copy(chinese_msg)#存到剪切板
pyautogui.hotkey('ctrl','v')#粘贴到记事本
print("✅ 任务完成，控制权已交还给主人。")