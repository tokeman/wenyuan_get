# wenyuan_get

> AI 论文可视化工具 — 输入关键词，自动生成高质量 SVG 汇报卡片并打包为 PPTX

---

## 核心功能

`wenyuan_get` 通过 AI（L Gemini CLI 或 DeepSeek API）联网检索论文、自动生成专业 SVG 汇报卡片，并打包为可直接导入 PowerPoint 的 PPTX 文件。

### 核心优势

| 优势 | 说明 |
|------|------|
| 🚀 **全自动** | 输入关键词 → 输出 PPTX，全程无需手动排版 |
| 🎨 **矢量 SVG** | 1280×720 宽屏比例，可无限缩放不失真 |
| 📊 **专业设计** | 四宫格/三栏布局，多套企业级主题配色 |
| 🔌 **多模型** | Gemini CLI（免费联网）/ DeepSeek API（稳定可控）|
| 💾 **离线渲染** | SVG → PNG → PPTX 全部本地执行，无 API 调用成本 |
| 📄 **双版本输出** | R=PNG渲染版（最强兼容）/ E=SVG+PNG双轨版（飞书/邮件不白屏）|

### 工作流程

```
关键词输入
    ↓
LLM 生成 SVG（Gemini CLI 或 DeepSeek API）
    ↓
SVG 代码保存到 output.md
    ↓
svg_to_ppt.py 本地渲染
    ↓
*_R.pptx（PNG渲染版）+ *_E.pptx（SVG+PNG双轨版）
```

---

## 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/tokeman/wenyuan_get.git
cd wenyuan_get

# 2. 安装 Python 依赖
pip install python-pptx cairosvg

# 3. 配置 LLM（二选一）

# 方式A：Gemini CLI（默认，免费联网检索）
gemini --auth  # 在有浏览器的机器上完成认证

# 方式B：DeepSeek API（稳定可控）
cp config.example.json config.json
# 编辑 config.json，填入你的 DeepSeek API Key
```

### 使用方式

```bash
# 方式一：Gemini CLI（默认，免费联网）
./wenyuan_get.sh "DeepSeek V4"

# 方式二：DeepSeek API
./wenyuan_get.sh "DeepSeek V4" --model "deepseek-chat"

# 方式三：指定主题 + 模型 + 双版本
./wenyuan_get.sh "DeepSeek V4" --theme "华为亮白" --model "deepseek-chat" -B

# 方式四：指定具体论文
./wenyuan_get.sh "BCI neural interfaces" \
  "Neural Digital Twins for Brain-Computer Interfaces" \
  "EEG Foundation Models: A Survey"
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--theme "主题名"` | 指定配色主题（如"华为亮白"）|
| `--model "模型名"` | 指定 LLM（默认 gemini，支持 deepseek-chat / deepseek-v4-pro 等）|
| `-R` | 仅生成 PNG 渲染版 |
| `-E` | 仅生成 SVG+PNG 双轨版 |
| `-B` | 双版本同时生成（默认）|

---

## 输出说明

| 文件 | 说明 |
|------|------|
| `*_R.pptx` | **PNG 渲染版** — cairosvg 渲染，兼容性最强 |
| `*_E.pptx` | **SVG+PNG 双轨版** — PowerPoint 2021+ 显示矢量，飞书/邮件降级 PNG |
| `output.md` | LLM 生成的原始 SVG 代码 |

### E 版本适用场景

- ✅ PowerPoint 2021+：直接显示矢量 SVG，可取消组合编辑
- ✅ 飞书/邮件转发：PNG fallback 不白屏
- ⚠️ PowerPoint 2019 及以下：降级显示 PNG

---

## SVG 设计规范

| 属性 | 值 |
|------|-----|
| 分辨率 | 1280×720（宽屏 PPT 比例 16:9） |
| 布局 | 四宫格（痛点-验证-机制-效果）或三栏 |
| 配色 | 主题化：华为亮白 + 更多企业主题 |
| 字体 | Noto Sans CJK SC（中日韩字符支持） |
| 图形 | 纯 SVG 绘制：矩形、圆、箭头、雷达简图 |

---

## 目录结构

```
wenyuan_get/
├── wenyuan_get.sh              # 主入口脚本（支持 Gemini / DeepSeek）
├── svg_to_ppt.py               # 本地渲染器（R/E 双版本）
├── prompt_template.md          # Prompt 模板
├── config.example.json         # DeepSeek API 配置示例
├── config.json                 # DeepSeek API 配置（本地）
├── themes/                     # 主题配色方案
│   └── huawei_light_corporate.md
├── __init__.py                 # Python 模块接口
├── DESIGN.md                   # 设计说明书
├── README.md                   # 本文档
└── LICENSE                     # MIT License
```

---

## 系统要求

- Python 3.8+
- Gemini CLI（`npm install -g gemini`）或 DeepSeek API Key
- 内存 2GB+

---

## 相关工具

| 工具 | 用途 |
|------|------|
| [python-pptx](https://python-pptx.readthedocs.io/) | PPTX 文件生成 |
| [CairoSVG](https://cairosvg.org/) | SVG → PNG 转码 |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | AI 生成 + 联网检索（默认）|
| [DeepSeek API](https://platform.deepseek.com/) | AI 生成（可选，stable）|

---

## License

MIT License
