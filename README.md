# Hachiware Desktop Pet
>**基于 OpenCV 视觉追踪与大模型交互的智能桌面助理**
> *An AI-powered desktop assistant featuring computer vision tracking and LLM integration.*

---
## 项目亮点（Highlights）
* **视觉锁定（Vision Tracking）**：利用 **OpenCV** 实现实时人脸/目标检测，让小八的眼神始终跟随你的坐标。
* **Agent 智能体架构（ReAct Loop）**：重构了底层的 LLM 路由逻辑，引入基于 ReAct 范式的自主状态循环。小八不仅能进行多轮对话，还能根据任务复杂度自主决定工具的调用链路。
* **系统级本地交互（System-level Interaction）**：深度集成 Function Calling，赋予小八操作宿主机系统的能力。目前已支持后台静默执行终端命令（CMD/PowerShell）、读取本地文件（如日志分析），并能自动捕获终端报错进行自我纠正。
* **语音引擎（Voice Synthesis）**：集成 **FunAudioLLM / CosyVoice** 技术，赋予小八标志性的个性化嗓音。
* **轻量化设计（Lightweight Design）**：核心逻辑基于 Python 编写，采用双缓冲技术优化 Tkinter 画布绘图，完美兼容 Windows 桌面环境，资源占用极低。

---

## 技术栈（Tech Stack）
* **Language**: Python 3.12
* **Vision**: OpenCV (opencv-python)
* **GUI**: Tkinter (Desktop Widget logic)
* **Intelligence**: DeepSeek API (Agent Reasoning) / Qwen-VL (Vision Logic)
* **Voice**: FunAudioLLM / CosyVoice (TTS)

---

## 快捷启动 (Quick Start)

### 1.克隆项目 (Clone) 

```bash 
git clone https://github.com/johsonx88888/Hachiware-Desktop-Pet.git
```

### 2. 安装依赖 (Install Dependencies)
```bash
pip install -r requirements.txt
```

### 3. 点火运行 (Run)
```bash
python src/desktop_pet.py
```