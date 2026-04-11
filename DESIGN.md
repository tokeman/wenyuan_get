# 文元获取工具 (wenyuan_get) 设计说明书

## 概述

**工具名称：** wenyan_get / wenyuan_get
**功能：** 输入论文关键词，通过 AI 自动检索、生成 SVG 可视化报告卡片，并打包为 PPTX 文件
**定位：** 科研工作者和 AI 研究者的论文汇报辅助工具

---

## 核心价值

1. **全自动**：输入关键词 → 输出可编辑 PPTX，全程无需手动排版
2. **高质量 SVG**：1280×720 宽屏比例，专业的四宫格/三栏布局
3. **离线渲染**：SVG → PNG → PPTX 全部本地执行，无 API 依赖
4. **Gemini 加持**：联网检索最新论文，自动提炼核心信息

---

## 技术架构

```
用户输入（关键词）
    │
    ▼
┌─────────────────┐
│ Gemini CLI      │  ← 联网检索论文 + 生成 SVG
│ (gemini -p)    │
└────────┬────────┘
         │ output.md (含SVG代码)
         ▼
┌─────────────────┐
│ Python 脚本     │  ← 本地渲染，无API调用
│ svg_to_ppt.py   │
└────────┬────────┘
         │ *.pptx
         ▼
    最终输出文件
```

---

## 输入输出

### 输入
- 关键词/主题（字符串）
- 可选：指定论文列表

### 输出
- `AI_Paper_Report.pptx` — 16:9 宽屏幻灯片
- 每页一张 SVG 卡片（可拖入 PowerPoint 直接使用）

---

## SVG 设计规范

| 属性 | 规范 |
|------|------|
| 分辨率 | 1280×720（宽屏 PPT 比例） |
| 背景 | 纯白或极浅冷灰（#F5F7FA） |
| 卡片阴影 | feDropShadow 弥散阴影 |
| 配色 | 四套随机选择：深空蓝/珊瑚红/翠绿/天际蓝 |
| 排版 | 四宫格或三栏（自动选择） |
| 图形 | 纯 SVG 绘制：矩形、圆、箭头、雷达简图 |
| 字体 | Arial/sans-serif，无外部字体依赖 |

---

## SVG 内容结构

每张 SVG 卡片包含三个核心模块：

1. **背景与痛点（Pain Points）**
   - 2-3 个现有方法的致命局限
   - 图标：红色警示三角或灰色漏斗

2. **核心机制（Core Mechanism）**
   - 论文提出的创新架构或算法
   - 图标：蓝色流程箭头或聚类点阵

3. **突破性成果（Key Results）**
   - 2-3 个震撼的核心数据
   - 图标：绿色上升箭头或仪表盘

---

## 组件清单

### 1. wenyuan_get.sh（主入口）
```bash
wenyuan_get <关键词> [论文1] [论文2] ...
```
- 生成 prompt.txt
- 调用 gemini -p
- 输出到 output.md

### 2. svg_to_ppt.py（渲染器）
```bash
python3 svg_to_ppt.py [input.md] [output.pptx]
```
- 读取 Markdown 文件中的 SVG 代码块
- 渲染为 1920×1080 PNG
- 打包为 16:9 PPTX

### 3. prompt.txt（Prompt 模板）
- 内置 Role 定义
- SVG 格式规范
- 用户指定的论文/关键词

---

## 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Gemini CLI | latest | AI 生成（需联网） |
| python-pptx | ≥0.6.0 | PPTX 生成 |
| cairosvg | ≥2.9.0 | SVG → PNG 转码 |

安装命令：
```bash
pip install python-pptx cairosvg
gemini --auth  # 完成认证
```

---

## 使用流程

```bash
# 方式一：命令行（推荐）
wenyuan_get "multilingual LLM alignment"

# 方式二：指定论文
wenyuan_get "multilingual" \
  "C-Mining: Cultural Synthetic Data Generation" \
  "The Illusion of Multilingual Data Mixtures"

# 方式三：Python 直接调用
python3 -c "
from wenyuan_get import generate
generate(keywords='BCI neural interfaces', papers=[...])
"
```

---

## 目录结构

```
~/.openclaw/workspace/tools/wenyuan_get/
├── wenyuan_get.sh       # 主入口脚本
├── svg_to_ppt.py        # 渲染脚本
├── prompt_template.md   # Prompt 模板
├── DESIGN.md           # 本文档
└── README.md          # 使用说明
```

---

## 差异化优势

| 维度 | 传统方式 | wenyuan_get |
|------|----------|-------------|
| 速度 | 手动搜索+排版 2h+ | 全自动 3min |
| 格式 | 复制粘贴截图 | 矢量 SVG 直接用 |
| 可编辑 | 截图无法改 | 保留 SVG 结构 |
| 成本 | $5-20 API 费 | Gemini 免费配额 |
| 部署 | 需要 API Key | 纯本地 CLI |

---

## 版本计划

- **v1.0**：基础流程跑通
- **v1.1**：多论文并行生成
- **v1.2**：自定义配色/布局选项
- **v2.0**：支持更多输出格式（PDF、Keynote）
