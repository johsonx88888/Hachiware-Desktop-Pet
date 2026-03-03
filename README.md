# Hachiware Desktop Pet
>**基于 OpenCV 视觉追踪与大模型交互的智能桌面助理**
> *An AI-powered desktop assistant featuring computer vision tracking and LLM integration.*

---
## 项目亮点（Highlights）
* **视觉锁定（Vision Tracking）**：利用 **OpenCV** 实现实时人脸/目标检测，让小八的眼神始终跟随你的坐标。
* **双核对话（Dual-Core Interaction）**:接入**LLM（大语言模型）**逻辑，支持自然语言处理，告别死板的关键词回复。
* **语音引擎（Voice systhesis）**集成**FunAudioLLM / CosyVoice**技术，赋予小八标志性的“赛博嗓音”。
* **轻量化设计**：核心逻辑基于Python编写，采用双缓冲技术优化canvas绘图，完美兼容 Windows 桌面环境。
---

## 技术栈（Tech Stack）
* **Language**: Python 3.12.4
* **Vision**: OpenCV (opencv-python)
* **GUI**: Tkinter/PySide (Desktop Widget logic)
* **Intelligence**: Large Language Model API (FunAudioLLM/CosyVoice)

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