import os 
import subprocess
import sys
def read_local_file(file_path):
    """
    读取指定路径的本地文本文件内容。
    """
    #限制只读项目目录下文件
    base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path=os.path.join(base_dir,file_path)

    try:
        if os.path.exists(full_path):
            with open(full_path,'r',encoding='utf-8') as f:
                return f.read(2000)
        else:
            return "找不到这个文件，请确认路径是否正确。"
    except Exception as e:
        return f"读取出错:{str(e)}" 
    
def run_cmd_command(command):
    """
    让小八终端执行自动化脚本
    内置防卡死机制
    """
    dangerous_keywords=['rm -rf','format','mkfs','shutdown','reboot']
    if any(k in command.lower() for k in dangerous_keywords):
        return f"🚨 小八拒绝执行高危命令: {command}！坚决保护主人的电脑！"
    print(f"🔧 小八正在后台终端执行: {command}")
    try:
        #防循坏超时卡死
        result=subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode==0:
            output=result.stdout.strip()
            # 限制返回长度
            return f"执行成功：\n{output[:1500]}"if output else "执行成功，无终端输出。"
        else:
            error=result.stderr.strip()
            return f"执行报错 (Exit Code{result.returncode}):\n{error[:1500]}"
    except subprocess.TimeoutExpired:
        return f"⏱️ 命令执行超时 (超过15秒)！已强制中断。"
    except Exception as e:
        return f"❌ 系统级异常: {str(e)}"
#写文件权限函数
def write_local_file(file_path,content):
    """
    在目录下创建或修改，覆盖文件。
    """

    try:
        base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path=os.path.join(base_dir,file_path)
        os.makedirs(os.path.dirname(full_path),exist_ok=True)
        with open(full_path,'w',encoding='utf-8') as f:
            f.write(content)
        return f"✅ 已成功写入文件: {file_path}"
    except Exception as e:
        return f"❌ 写文件失败: {str(e)}"
    
def run_python_script(file_path):
    """
    运行指定python脚本并返回终端输出：
    """
    try:
        base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path=os.path.join(base_dir,file_path)
        if not os.path.exists(full_path):
            return f"❌运行失败，找不到文件{file_path}"
        
        #执行命令获取标准输出
        result=subprocess.run(
            [sys.executable,full_path],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode==0:
          output = result.stdout.strip()
          return f"🚀 运行成功！输出如下：\n{output[:1000]}" if output else "🚀 运行成功，但脚本没有任何终端打印输出（可能缺少 print 语句）。"
        else:
            return f"⚠️ 运行报错啦！错误信息: \n{result.stderr.strip()[:1000]}"
    except subprocess.TimeoutExpired:
        return "⏱️ 脚本运行超时，已强制停止。"