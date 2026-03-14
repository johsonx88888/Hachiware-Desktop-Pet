import pyautogui
import time
import tkinter as tk
from tkinter import messagebox
import pyperclip

pyautogui.FAILSAFE=True

def start_collection_test():
    print("🚀 脚本已启动，请确保微信窗口在屏幕可见范围内...")
    time.sleep(2)
    print("🔍 正在扫描转账气泡...")
    bubble_loc=pyautogui.locateOnScreen('vision_targets/bubble.png',confidence=0.8)

    if bubble_loc:
        print("🎯 发现转账消息！正在弹出确认窗口...")

        # --- 置顶询问 ---
        root=tk.Tk()
        root.withdraw()
        root.attributes('-topmost',True)
        ans=messagebox.askyesno("小八助手", "发现一笔转账，要现在收款吗？")
        root.destroy()

        if ans:
            bx,by=pyautogui.center(bubble_loc)
            pyautogui.click(bx,by)
            print("🖱️ 已点击气泡，等待 1.5 秒加载...")
            time.sleep(1.5)
            print("🔍 正在寻找绿色确认按钮...")
            confirm_loc=pyautogui.locateOnScreen('vision_targets/confirm_btn.png',confidence=0.8)
            if confirm_loc:
                cx,cy=pyautogui.center(confirm_loc)
                pyautogui.click(cx,cy)
                print("💰收款成功！")
            else:
                print("❌ 哎呀，没找到确认按钮，可能是截图不匹配或网络卡顿。")
        else:print("🛑 按下了取消，放弃收款。")
    else:
        print("📭 没找到气泡。请检查 bubble.png 是否清晰，或者微信是否被遮挡。")

if __name__=="__main__":
    start_collection_test()
