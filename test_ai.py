#导入工具包
from openai import OpenAI

client=OpenAI(
    api_key="sk-eecywquccxwcdydhekiirfffrmzpifvpauiatrhxsqwvukhq",
    base_url="https://api.siliconflow.cn/v1"
)
print("正在呼叫小八的大脑（硅基流动版）...")

try:
    response=client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3",

        messages=[
            #调教
            {"role":"system","content":"你是一只吉伊卡哇，说话要带‘呀’，喜欢吃好吃的。"},
            #user says
            {"role":"user","content":"你好呀，我有16块钱，能买什么？"}
        ],
        #stream流式输出
        stream=False
    )
    print("连接成功，它说：")
    print(response.choices[0].message.content)
except Exception as e:
    print("出错了，报错信息如下：")
    print(e)