# 文元获取工具 (wenyuan_get) 设计说明书

## 概述

**工具名称：** wenyuan_get
**功能：** 输入论文关键词，通过 AI 自动生成 SVG 可视化报告卡片，并打包为 PPTX 文件
**定位：** 科研工作者和 AI 研究者的论文汇报辅助工具

---

## 核心价值

1. **全自动**：输入关键词 → 输出可编辑 PPTX，全程无需手动排版
2. **高质量 SVG**：1280×720 宽屏比例，专业的四宫格/三栏布局
3. **离线渲染**：SVG → PNG → PPTX 全部本地执行，无 API 依赖
4. **多模型支持**：Gemini CLI（免费联网检索）/ DeepSeek API（稳定可控）
5. **主题定制**：支持华为亮白等多种企业级配色主题

---

## 技术架构

```
用户输入（关键词）
    │
    ▼
┌─────────────────────────────┐
│ LLM 生成层（可插拔）          │
│  • Gemini CLI（默认，联网）   │
│  • DeepSeek API（需配置key）  │
└────────┬────────────────────┘
         │ output.md (含SVG代码)
         ▼
┌─────────────────────────────┐
│ svg_to_ppt.py（本地渲染）    │
│  • R 版本：PNG 渲染版        │
│  • E 版本：SVG+PNG 双轨版   │
└────────┬────────────────────┘
         │ *.pptx
         ▼
    最终输出文件
```

---

## 输入输出

### 输入
- 关键词/主题（字符串）
- 可选：指定论文列表
- 可选：主题名称（--theme）
- 可选：模型名称（--model）

### 输出
- `*_R.pptx` — PNG 渲染版，兼容性最强
- `*_E.pptx` — SVG+PNG 双轨版，飞书/邮件转发不白屏（PPT 2021+ 显示矢量）
- `output.md` — LLM 生成的原始 SVG 代码

---

## SVG 设计规范

| 属性 | 规范 |
|------|------|
| 分辨率 | 1280×720（宽屏 PPT 比例） |
| 背景 | 纯白或极浅冷灰（#F5F7FA） |
| 卡片阴影 | feDropShadow 弥散阴影 |
| 配色 | 主题化：华为亮白 + 更多企业主题 |
| 排版 | 四宫格或三栏（自动选择） |
| 图形 | 纯 SVG 绘制：矩形、圆、箭头、雷达简图 |
| 字体 | font-family="Noto Sans CJK SC, sans-serif"（中文必须） |

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
wenyuan_get.sh <关键词> [--theme "主题名"] [--model "模型名"] [-R|-E|-B]
```
- 解析命令行参数
- 调用 Python 构建 prompt（兼容多字节字符）
- 调用 LLM 生成 SVG（Gemini CLI 或 DeepSeek API）
- 调用 svg_to_ppt.py 输出 PPTX

### 2. svg_to_ppt.py（渲染器）
```bash
python3 svg_to_ppt.py [input.md] [output_prefix] ["R"|"E"|"B"]
```
- **R 版本**：cairosvg 渲染为 PNG，最佳兼容性
- **E 版本**：SVG + PNG 双轨嵌入，PowerPoint 2021+ 显示矢量，飞书/邮件降级 PNG

### 3. prompt_template.md（Prompt 模板）
- 内置 Role 定义
- SVG 格式规范
- 用户指定的论文/关键词

### 4. config.json（DeepSeek API 配置）
```json
{
  "deepseek": {
    "api_key": "YOUR_KEY_HERE",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat"
  }
}
```

### 5. themes/（主题目录）
- `huawei_light_corporate.md` — 华为亮白企业主题

---

## 依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Gemini CLI | latest | AI 生成（默认，联网免费） |
| DeepSeek API | — | AI 生成（可选，稳定可控） |
| python-pptx | ≥0.6.0 | PPTX 生成 |
| cairosvg | ≥2.9.0 | SVG → PNG 转码 |

安装命令：
```bash
pip install python-pptx cairosvg
gemini --auth  # Gemini CLI 认证（一次性）
# DeepSeek API: 创建 config.json 填入 key 即可
```

---

## 使用流程

```bash
# 方式一：Gemini CLI（默认，免费联网）
./wenyuan_get.sh "DeepSeek V4" --theme "华为亮白" -B

# 方式二：DeepSeek API（稳定可控）
./wenyuan_get.sh "DeepSeek V4" --model "deepseek-chat" -B

# 方式三：指定具体论文
./wenyuan_get.sh "BCI neural interfaces" \
  "Neural Digital Twins for Brain-Computer Interfaces" \
  "EEG Foundation Models: A Survey"
```

---

## 目录结构

```
wenyuan_get/
├── wenyuan_get.sh           # 主入口脚本（含 DeepSeek/Gemini 双支持）
├── svg_to_ppt.py            # 渲染脚本（R/E 双版本）
├── prompt_template.md       # Prompt 模板
├── config.example.json      # DeepSeek API 配置示例
├── config.json              # DeepSeek API 配置（本地）
├── themes/                  # 主题配色方案
│   └── huawei_light_corporate.md
├── DESIGN.md                # 本文档
└── README.md                # 使用说明
```

---

## R/E 双版本说明

| 版本 | 生成方式 | 适用场景 |
|------|----------|----------|
| **R**（Rendered） | cairosvg 渲染为 PNG | 兼容性最强，任何环境均正常显示 |
| **E**（Editable） | SVG+PNG 双轨嵌入 | PPT 2021+ 显示矢量；飞书/邮件转发显示 PNG |

### E 版本双轨原理

```
PowerPoint 解析流程：
1. 读取主 blip → PNG（图层保底）
2. 检查 extLst/svgBlip → 发现 SVG 扩展
3. PPT 2021+ 优先渲染 SVG（矢量，可取消组合编辑）
4. 旧版/飞书/邮件 → 自动降级 PNG 显示
```

PNG 渲染失败时，主 blip 自动降级指向 SVG，避免悬空引用报错。

---

## 差异化优势

| 维度 | 传统方式 | wenyuan_get |
|------|----------|-------------|
| 速度 | 手动搜索+排版 2h+ | 全自动 3min |
| 格式 | 复制粘贴截图 | 矢量 SVG 直接用 |
| 可编辑 | 截图无法改 | E版本可取消组合编辑 |
| 成本 | $5-20 API 费 | Gemini 免费 / DeepSeek 低成本 |
| 部署 | 需要 API Key | 零配置（Gemini）或 config.json（DeepSeek） |

---

## 企业版主题

### 🟥 华为亮白（华为 PPT 风格）

| 角色 | 色值 | RGB | 用途 |
|------|------|-----|------|
| 背景色 | #FFFFFF | R255 G255 B255 | 页面主背景 |
| 标题色 | #990000 | R153 G0 B0 | 幻灯片标题 |
| 正文色 | #333333 | R51 G51 B51 | 正文（深灰） |
| 强调蓝 | #002FA7 | R0 G47 B167 | 图表/数据高亮 |
| 辅助青 | #00857C | R0 G133 B124 | 次要强调 |
| 浅灰底 | #F2F4F7 | R242 G244 B247 | 内容卡片底色 |
| 边框色 | #D9DEE3 | R217 G222 B227 | 表格线/分割线 |
| 华为红 | #C7000B | R199 G0 B11 | 点缀（Logo/关键数据） |

详细规范见 `themes/huawei_light_corporate.md`

---

## 版本历史

| 版本 | 日期 | 变化 |
|------|------|------|
| v1.0 | 2026-04 | 基础流程跑通 |
| v1.1 | 2026-04 | 多论文并行生成 |
| v1.2 | 2026-04-26 | 企业版主题（华为亮白等）|
| v1.3 | 2026-04-29 | **DeepSeek API 支持（--model参数）** |
| v1.3 | 2026-04-29 | **E版本 SVG+PNG 双轨 Bug修复** |
