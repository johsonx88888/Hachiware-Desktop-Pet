import os
import json 
import chromadb
from openai import OpenAI
import config
from langchain_text_splitters import RecursiveCharacterTextSplitter

class KnowledgeBuilder:
    
    #初始化
    def __init__(self):
        print("正在启动RAG构建引擎...")
        #1、挂载持久存储器
        self.db_path="./chroma_db_storage"
        self.chroma_client=chromadb.PersistentClient(path=self.db_path)
        #2、链接或创建知识库空间
        self.collection=self.chroma_client.get_or_create_collection(
            name="hachiware_brain",
            metadata={"hnsw:space":"cosine"}
        )
        # 3、读取底层的 JSON 配置文件
        config_file = "config/api_config.json"
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                api_key = json.load(f).get("SILICONFLOW_API_KEY", "")
        except Exception as e:
            print(f"❌ 读取密钥失败，请确保 {config_file} 文件存在！错误信息: {e}")
            return
        # 4、连接云端API接口
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
    #文本向量化
    def get_embedding(self,text):
        """调用API将文本转为高维度向量矩阵"""
        try:
            response=self.client.embeddings.create(
                input=text,
                model="BAAI/bge-m3"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ 向量化失败:{e}")
            return None
        
    #将文本分块
    def build_from_folder(self,folder_path="knowledge_base"):
        """扫描文件夹并进行分块入库"""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"📂未找到{folder_path}文件夹，已自动创建。请往里放入txt或md文件。")
            return
        #递归切割
        text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n","\n",".","，",",","。","、"," ","!","?"]
        )
        files=[f for f in os.listdir(folder_path) if f.endswith((".txt",".md"))]
        if not files:
            print("⚠️ 知识库文件夹为空，没有可以学习的文档，小八觉得很空虚。")
            return 
        
        for file_name in files:
            file_path=os.path.join(folder_path,file_name)
            print(f"📖 正在精读文档: {file_name}...")
            with open(file_path,'r',encoding='utf-8') as f:
                content=f.read()

            if not content.strip():
                print(f"   ⚠️ {file_name} 是个空文件，跳过。")
                continue
            #智能分块
            chunks=text_splitter.split_text(content)
            ids=[]
            embeddings=[]
            documents=[]
            metadatas=[]
            
            for i,chunk in enumerate(chunks):
                print(f"🧬 正在将第 {i+1}/{len(chunks)} 块知识转化为向量...",end='\r')
                vec=self.get_embedding(chunk)
                if vec:
                    ids.append(f"{file_name}_chunk_{i}")
                    embeddings.append(vec)
                    documents.append(chunk)
                    metadatas.append({"source":file_name,"chunk_index":i})
            print()

            if ids:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"✅ 【{file_name}】 已成功刻入小八的深层记忆库！")

#   
if __name__=="__main__":
    builder=KnowledgeBuilder()
    builder.build_from_folder()
    

