import pyautogui
import time
import pygetwindow as gw
import tkinter as tk
from tkinter import messagebox
import os

pyautogui.FAILSAFE = True


# 强制把微信窗口置顶
def bring_wechat_to_front():
    try:
        wechat_wins = gw.getWindowsWithTitle("微信")
        if wechat_wins:
            win = wechat_wins[0]
            if win.isMinimized:
                win.restore()  # 还原窗口大小
            # 置顶
            win.activate()
            print("✨ 小八：哈！微信被我抓出来啦！")
            time.sleep(0.5)
            return True
        else:
            # 若微信被后台隐藏图标托管
            print("📭 小八：常规方法没找到，尝试使用全局唤醒魔法 (Ctrl+Alt+W)...")
            pyautogui.hotkey("ctrl", "alt", "w")
            time.sleep(1)  # 等待微信窗口弹出
            wechat_wins_retry = gw.getWindowsWithTitle("微信")
            if wechat_wins_retry:
                wechat_wins_retry[0].activate()
                return True
            return False
    except Exception as e:
        print(f"❌ 微信窗口调度失败: {e}")
        return False

#寻找有转账消息的对话框
def navigate_to_transfer_chat():
   print("🔍 小八：正在左侧扫描谁给我发钱了...")
   if not bring_wechat_to_front():  #先把微信弹出来
        return False
   try:
       target_chat=pyautogui.locateOnScreen("vision_targets/chat_list_transfer.png",confidence=0.7)
       if target_chat:
           pyautogui.click(pyautogui.center(target_chat))
           print("🚀 小八：抓到了！正在进入对话框...")
           time.sleep(1)
           return True
   except:
       pass
   print("📭 小八：左侧列表好像没看到新的转账提醒。")
   return False

#去重识别
def get_unique_bubbles(image_path,confidence=0.9,tolerance=30):
    """去除多余初次识别的转账气泡"""
    try:
        all_boxes=list(pyautogui.locateAllOnScreen(image_path,confidence=confidence))
    except Exception:
        return []
    
    unique_boxes=[]
    for box in all_boxes:
        is_duplicate=False
        for u_box in unique_boxes:
            if abs(box.left-u_box.left)<tolerance and abs(box.top-u_box.top)<tolerance:
                is_duplicate=True
                break
        if not is_duplicate:
            unique_boxes.append(box)

    unique_boxes.sort(key=lambda b:b.top)
    return unique_boxes
       

# 自动收款
def auto_collect_money():
    """赛博收款,视觉搜索并自动点击"""
    print("🚀 ：全自动收款流程启动！")
    # --- A. 翻窗 ---
    if not bring_wechat_to_front():
        return "找不到微信窗口，收款失败。"

    collected_count = 0  # 记账本：记录收了几笔
    max_scrolls = 5
    scroll_count = 0

    while True:
        all_bubbles = get_unique_bubbles("vision_targets/bubble.png", confidence=0.9)

        collected_in_this_screen=False #标记当前页面是否捞到钱

        # --- 情况 1：当前屏幕没看到转账 ---
        if not all_bubbles:
            if scroll_count < max_scrolls:
                print(f"🔄 屏幕没钱了，尝试往上滚一滚 (第 {scroll_count + 1} 次)...") 
                pyautogui.scroll(500)
                time.sleep(1)
                scroll_count += 1
                continue  # 跳回开头重新寻找
            else:
                # 滚完了也没找到，结算退出
                if collected_count > 0:
                    return f"🎉 扫荡完毕！小八一共帮你收了 {collected_count} 笔钱！"
                else:
                    return "📭 看了一圈，没有未领取的转账哦。"

        # --- 情况 2：看到转账了 ---
        for bubble_loc in reversed(all_bubbles):
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            ans = messagebox.askyesno(
                "小八提醒", f"发现第 {collected_count + 1} 笔钱！要收下吗？(｡･ω･｡)"
            )  # 弹出待确认窗口
            root.destroy()

            if ans:
                # 1.点击转账窗口
                bx, by = pyautogui.center(bubble_loc)
                pyautogui.click(bx, by)
                print(f"🖱️已点击第 {collected_count + 1}笔转账，请确认按钮...")

                # 2.循环寻找确认按钮
                confirm_btn = None
                for i in range(5):   #循环点击
                    try:
                        confirm_btn = pyautogui.locateOnScreen(
                            "vision_targets/confirm_btn.png", confidence=0.9
                        )
                        if confirm_btn:
                            break
                    except:
                        pass
                    time.sleep(1)
                #发现旧账则退出
                if not confirm_btn:
                    print("⚠️ 小八：哎呀，点到旧的转账记录啦！正在自动撤退...")
                    pyautogui.press("esc")
                    time.sleep(0.5)
                    continue

                # 3.点击确认（真账）
                if confirm_btn:
                    cx, cy = pyautogui.center(confirm_btn)
                    pyautogui.click(cx, cy)
                    print("💰 收款成功！")
                    collected_count += 1
                    collected_in_this_screen = True
                    scroll_count = 0
                    # 收完钱后，按下 ESC 关闭确认小窗口，露出背后的聊天记录
                    time.sleep(1)  # 等动画播完
                    pyautogui.press("esc")
                    time.sleep(0.5)
                    time.sleep(1)  # 等窗口关掉
                    print("🔄 准备扫描下一笔...")
                    break
            else:
                return f"🛑 用户取消。本次共收到 {collected_count} 笔"
        if not collected_in_this_screen:
            if scroll_count < max_scrolls:
                print(f"🔄 这一屏全是旧账，尝试往上滚一滚 (第 {scroll_count + 1} 次)...")
                wechat_wins = gw.getWindowsWithTitle("微信")
                if wechat_wins:
                    win=wechat_wins[0]
                    pyautogui.click(win.center.x, win.top + 20)
                    pyautogui.moveTo(win.center.x,win.center.y)  #鼠标悬停，确保回到微信窗口
                pyautogui.scroll(500)
                time.sleep(1)
                scroll_count+=1
            else:
                if collected_count>0:
                    return f"🎉 扫荡完毕！小八一共帮你收了 {collected_count} 笔钱！"
                else:
                        return "📭 看了一圈，没有未领取的转账哦。"


if __name__ == "__main__":
    navigate_to_transfer_chat()
    result = auto_collect_money() 
    print(result)