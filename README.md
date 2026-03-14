# Hachiware Desktop Pet
> **基于 OpenCV 视觉追踪与大模型交互的智能桌面助理**
> *An AI-powered desktop assistant featuring computer vision tracking and LLM integration.*

---
##  2026-03-14 更新：加入静态skill
* **全自动微信收款**：引入 **PyAutoGUI** 联动视觉算法，实现从“收到转账”到“点击确认”的全链路自动化。
---

##  项目功能（Core Features）
* **视觉锁定（Vision Tracking）**：利用 **OpenCV** 实现实时人脸/目标检测，让小八的眼神始终跟随你的坐标。
* **Agent 智能体架构（ReAct Loop）**：重构了底层的 LLM 路由逻辑，引入基于 ReAct 范式的自主状态循环。小八不仅能进行多轮对话，还能根据任务复杂度自主决定工具的调用链路。
* **微信自动化操作（WeChat RPA）**：基于 PyAutoGUI 实现了桌面自动化功能。支持让小八自动寻找微信转账对话框并收取转账，内部加入了坐标去重防误点和滚轮查漏逻辑。
* **系统级本地交互（System-level Interaction）**：深度集成 Function Calling，赋予小八操作宿主机系统的能力。目前已支持后台静默执行终端命令（CMD/PowerShell）、编写并运行 Python 脚本，并能自动捕获终端报错进行自我纠正。
* **高清界面适配（High DPI UI）**：修复了 Windows 系统缩放导致的 Tkinter 窗口模糊或缩小问题，确保在高清屏幕下也能保持 5:6 的正常比例和清晰度。
* **语音引擎（Voice Synthesis）**：集成 **FunAudioLLM / CosyVoice** 技术，赋予桌宠小八与taffy双重音色。
* **现代化工程管理（Modern Engineering）**：告别依赖地狱，采用 Rust 编写的极速包管理器 `uv` 进行环境构建，并支持通过 PyInstaller 打包为全环境自适应的免安装 `.exe` 程序。

---

##  技术栈（Tech Stack）
* **Language**: Python 3.12
* **Vision**: OpenCV (opencv-python)
* **Automation**: PyAutoGUI
* **GUI**: Tkinter (Desktop Widget logic)
* **Intelligence**: DeepSeek API (Agent Reasoning) / Qwen-VL (Vision Logic)
* **Voice**: FunAudioLLM / CosyVoice (TTS)
* **Engineering**: `uv` (Package Management), `TOML` (Configuration), PyInstaller (Build)

---

## 🎮 快速体验 (免安装绿色版 / For General Users)
如果你不想配置 Python 环境，只想立刻召唤小八：
1. 从好友（或 Releases 页面）获取最新的 `小八桌宠_免安装版.zip`。
2. **解压**压缩包到一个独立的文件夹中（🚨 请勿在压缩包内直接双击）。
3. 用记事本打开目录下的 `api_config.json`，在对应位置填入你的 API Key。
4. 双击运行 `desktop_pet.exe` 即可！

---

## 💻 开发者指南 (Quick Start for Developers)
本项目采用现代化的 `uv` 进行极速依赖管理，确保 100% 的环境一致性。

### 1. 克隆项目 (Clone) 
```bash 
git clone https://github.com/johsonx88888/Hachiware-Desktop-Pet.git
cd Hachiware-Desktop-Pet
```

### 2. 安装依赖 (Install Dependencies)
```bash
pip install uv
uv sync
```

### 3. 密钥配置 (Configuration)
初次运行或手动在根目录检查 api_config.json 文件，并填入您的 SILICONFLOW_API_KEY。

### 4. 点火运行 (Run)
```bash
uv run src/desktop_pet.py
```