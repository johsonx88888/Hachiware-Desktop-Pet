import os 
import subprocess
import sys
import json
import chromadb
import uuid
import datetime
from openai import OpenAI

#1、读取文件
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

#2、跑本地cmd命令
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
            encoding='utf-8',
            errors='replace',
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
    
#3、改写文件
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
    
#4、运行脚本
def run_python_script(file_path):
    """
    运行指定python脚本并返回终端输出：（与exe和开发环境自适应）
    """
    try:
        base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path=os.path.join(base_dir,file_path)
        if not os.path.exists(full_path):
            return f"❌运行失败，找不到文件{file_path}"
        #判断运行环境
        if getattr(sys,'frozen',False):
            #sys.executable是exe本身，改用系统python
            interpreter="python"
        else:
            #开发环境，直接用当前venv带的解释器
            interpreter=sys.executable

        #执行命令获取标准输出
        result=subprocess.run(
            [interpreter,full_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=15,
            shell=True
        )

        if result.returncode==0: 
          output = result.stdout.strip()
          return f"🚀 运行成功！输出如下：\n{output[:1000]}" if output else "🚀 运行成功，但脚本没有任何终端打印输出（可能缺少 print 语句）。"
        else:
            return f"⚠️ 运行报错啦！错误信息: \n{result.stderr.strip()[:1000]}"
    except subprocess.TimeoutExpired:
        return "⏱️ 脚本运行超时，已强制停止。"
    except Exception as e:              # 🚨 加上通用异常兜底，防止未知错误导致整个工具链卡死
        return f"❌ 系统级异常: {str(e)}"
    
#5、RAG本地检索
def search_knowledge_base(query:str):
    """在本地ChromaDB检索相关信息"""
    print(f"\n🔍 小八正在翻阅记忆库，寻找关于【{query}】的线索...")
    base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path=os.path.join(base_dir,"chroma_db_storage")
    config_file=os.path.join(base_dir,"config","api_config.json")
    if not os.path.exists(db_path):
        return "本地知识库不存在，请先运行入库脚本 build_rag_db.py。"
    try:   #倘若向量记忆库存在
        chroma_client=chromadb.PersistentClient(path=db_path)
        collection=chroma_client.get_collection(name="hachiware_brain")
    except Exception as e:
        return f"连接知识库失败：{str(e)}"
    #读取api接入大模型
    try:
        with open(config_file,'r',encoding='utf-8') as f:
            api_key=json.load(f).get("SILICONFLOW_API_KEY","")
    except Exception:
        return "读取API密钥失败，无法将问题转化为向量检索"
    
    #初始化大模型客户端
    client=OpenAI(api_key=api_key,base_url="https://api.siliconflow.cn/v1")

    #向量化检索
    try:
        response=client.embeddings.create(input=query,model="BAAI/bge-m3")
        query_vector=response.data[0].embedding
        #关键参数
        results=collection.query(query_embeddings=[query_vector],n_results=3) 
    except Exception as e:
        return f"检索失败：{e}"
    
    if not results['documents'] or not results['documents'][0]:
        return "❌抱歉，记忆库中没有找到与此相关的信息。"
    
    #格式化检索格式
    retrieved_text="【以下是检索到的本地私有记忆，请根据这些信息回答用户】：\n"
    for i,doc in enumerate(results['documents'][0]):
        source=results['metadatas'][0][i].get('source','未知出处')
        retrieved_text+=f"---参考片段{i+1} (来源：{source}) ---\n{doc}\n"

    print("✅ 记忆检索完成，已把绝密资料递交给小八的大脑！\n")    
    return retrieved_text

#6、实时记忆
def add_to_knowledge_base(text_to_memorize:str):
    """将重要信息实时写入小八的长期向量记忆库"""
    print(f"\n🧠 小八正在将重要情报刻入DNA：【{text_to_memorize}】...")
    base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path=os.path.join(base_dir,"chroma_db_storage")
    config_file=os.path.join(base_dir,"config","api_config.json")

    if not os.path.exists(db_path):
        return "❌ 记忆库还未初始化，请先运行 build_rag_db.py 创建底层数据库。"
    #1、连接向量库
    try:
        chroma_client=chromadb.PersistentClient(path=db_path)
        collection=chroma_client.get_collection(name="hachiware_brain")
    except Exception as e:
        return f"❌ 记忆存储失败，无法打开脑库：{str(e)}"
    #2、读取API并调用BAAI模型进行文本向量化
    try:
        with open(config_file,'r',encoding='utf-8') as f:
            api_key=json.load(f).get("SILICONFLOW_API_KEY","")
        client=OpenAI(api_key=api_key,base_url="https://api.siliconflow.cn/v1")
        response=client.embeddings.create(input=text_to_memorize,model="BAAI/bge-m3")
        vector=response.data[0].embedding
    except Exception as e:
        return f"❌ 记忆向量化失败：{str(e)}"
    #3、写入ChromaDB
    try:
        memory_id=f"chat_memory_{uuid.uuid4().hex[:8]}"
        current_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.add(
            ids=[memory_id],
            embeddings=[vector],
            documents=[text_to_memorize],
            metadatas=[{"source":"chat_realtime","time":current_time}]
        )
        return "✅ 记忆已永久保存至小八的向量库中！"
    except Exception as e:
        return f"❌写入向量库失败：{e}"


