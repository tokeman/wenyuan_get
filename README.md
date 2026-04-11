# wenyuan_get

> AI 论文可视化工具 — 输入关键词，自动生成高质量 SVG 汇报卡片并打包为 PPTX

[English](#english) | [中文](#中文)

---

## 中文说明

### 核心功能

`wenyuan_get` 是一款 AI 论文可视化工具，通过 Gemini CLI 联网检索论文、自动生成专业 SVG 汇报卡片，并打包为可直接导入 PowerPoint 的 PPTX 文件。

### 核心优势

| 优势 | 说明 |
|------|------|
| 🚀 **全自动** | 输入关键词 → 输出 PPTX，全程无需手动排版 |
| 🎨 **矢量 SVG** | 1280×720 宽屏比例，可无限缩放不失真 |
| 📊 **专业设计** | 四宫格/三栏布局，随机配色方案，无需设计经验 |
| 💾 **离线渲染** | SVG → PNG → PPTX 全部本地执行，无 API 调用成本 |
| 🔓 **零配置** | 无需 API Key，Gemini CLI 免费配额即可运行 |

### 工作流程

```
关键词输入
    ↓
Gemini CLI（联网检索论文 + 生成 SVG）
    ↓
SVG 代码保存到 output.md
    ↓
svg_to_ppt.py（本地渲染）
    ↓
AI_Paper_Report.pptx
```

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourname/wenyuan_get.git
cd wenyuan_get

# 2. 安装 Python 依赖
pip install python-pptx cairosvg

# 3. 配置 Gemini CLI（一次性）
# 方式A：在有浏览器的机器上运行
gemini --auth

# 方式B：手动复制 token
# 本地: cat ~/.gemini/state.json
# 复制到服务器: ~/.gemini/state.json
```

### 使用方式

```bash
# 方式一：命令行（推荐）
./wenyuan_get.sh "multilingual LLM alignment"

# 方式二：指定具体论文
./wenyuan_get.sh "BCI neural interfaces" \
  "Neural Digital Twins for Brain-Computer Interfaces" \
  "EEG Foundation Models: A Survey"

# 方式三：Python 模块调用
python -m wenyuan_get "harness engineering"
```

### 输出

- `AI_Paper_Report.pptx` — 16:9 宽屏幻灯片（每页一张 SVG 卡片）
- `output.md` — Gemini 生成的原始 SVG 代码

### SVG 设计规范

| 属性 | 值 |
|------|-----|
| 分辨率 | 1280×720（宽屏 PPT 比例） |
| 布局 | 四宫格（痛点-验证-机制-效果）或三栏 |
| 配色 | 四套随机选择：深空蓝/珊瑚红/翠绿/天际蓝 |
| 字体 | Noto Sans CJK（中日韩字符支持） |
| 图形 | 纯 SVG 绘制：矩形、圆、箭头、雷达简图 |

### 目录结构

```
wenyuan_get/
├── wenyuan_get.sh          # 主入口脚本
├── svg_to_ppt.py           # 本地渲染器（SVG → PPTX）
├── prompt_template.md      # Prompt 模板
├── __init__.py             # Python 模块接口
├── DESIGN.md               # 设计说明书
├── README.md               # 本文档
└── LICENSE                # MIT License
```

### 系统要求

- Python 3.8+
- Gemini CLI (`npm install -g gemini`)
- Google 账号（用于 Gemini CLI 认证，免费配额）
- 内存 2GB+

### 相关工具

| 工具 | 用途 |
|------|------|
| [python-pptx](https://python-pptx.readthedocs.io/) | PPTX 文件生成 |
| [CairoSVG](https://cairosvg.org/) | SVG → PNG 转码 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | AI 生成 + 联网检索 |

### License

MIT License

---

## English

### Overview

`wenyuan_get` is an AI paper visualization tool that generates professional SVG report cards from keywords using Gemini CLI, then packages them into PowerPoint-ready PPTX files.

### Quick Start

```bash
# Install dependencies
pip install python-pptx cairosvg
npm install -g gemini
gemini --auth  # One-time Google authentication

# Run
./wenyuan_get.sh "your research keywords"
```

### Key Features

- **Fully Automated**: Keyword → PPTX, no manual formatting
- **Vector SVG**: 1280×720 widescreen, infinitely scalable
- **Professional Design**: 4-quadrant / 3-column layouts, random color themes
- **Offline Rendering**: SVG → PNG → PPTX locally, zero API cost
- **Zero Config**: Works with Gemini CLI free tier, no API key needed

### Architecture

```
User Input (keywords)
    ↓
Gemini CLI (web search + SVG generation)
    ↓
output.md (SVG code)
    ↓
svg_to_ppt.py (local rendering)
    ↓
AI_Paper_Report.pptx
```

### License

MIT License
