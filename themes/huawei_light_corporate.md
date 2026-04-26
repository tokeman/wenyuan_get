# Huawei PPT 风格主题 — Mode B: Light Corporate

> 适用场景：内部报告、技术文档、培训材料、合作伙伴沟通、工作汇报

---

## 配色体系

### 核心色板

| 角色 | 色值 HEX | RGB | 用途 |
|------|----------|-----|------|
| 背景色 | `#FFFFFF` | R255 G255 B255 | 页面主背景 |
| 标题色 | `#990000` | R153 G0 B0 | 幻灯片标题、章节标题 |
| 正文色 | `#333333` | R51 G51 B51 | 正文文字（深灰，非纯黑） |
| 强调蓝 | `#002FA7` | R0 G47 B167 | 图表、图标、数据高亮 |
| 辅助青 | `#00857C` | R0 G133 B124 | 次要强调，流程图 |
| 浅灰底 | `#F2F4F7` | R242 G244 B247 | 内容卡片底色 |
| 边框色 | `#D9DEE3` | R217 G222 B227 | 表格线、分割线 |
| 华为红 | `#C7000B` | R199 G0 B11 | 点缀（仅Logo/关键数据） |

### 设计要点

- 白色背景 + 暗红标题 = 华为企业内部 PPT 经典搭配
- 正文 `#333333` 深灰，视觉柔和
- 红色严格限制为点缀色，禁止大面积使用
- 蓝色和青色服务于数据可视化

### 图表配色（按优先级）

| 顺序 | 色值 | 名称 | 用途 |
|------|------|------|------|
| 1 | `#C7000B` | 华为红 | 核心指标、当前年度 |
| 2 | `#002FA7` | 深蓝 | 对比项、次要指标 |
| 3 | `#00857C` | 青色 | 第三类别 |
| 4 | `#F5A623` | 琥珀 | 警示、特殊标注 |
| 5 | `#6B4C9A` | 紫色 | 额外类别 |
| 6 | `#2D8C3C` | 绿色 | 额外类别 |

**规则：** 同一页面最多 4 种颜色

---

## 字体规范

### 字号规范

| 元素 | 中文字号 | 英文字号 | 字重 | 颜色 |
|------|----------|----------|------|------|
| 封面标题 | 36-44pt | 36-44pt | Medium/Bold | `#990000` |
| 章节标题 | 30-32pt | 32-35pt | Medium | `#990000` |
| 正文 | 18-20pt | 20-22pt | Regular | `#333333` |
| 子条目 | 18pt | 18pt | Regular | `#333333` |
| 脚注 | 10-12pt | 10-12pt | Light | `#999999` |
| 数据大字 | 48-72pt | 48-72pt | Bold | `#002FA7` 或 `#C7000B` |

### 排版规则

- **字重偏轻**：层次感通过字号和颜色差异建立，非加粗
- 行距：1.3-1.5 倍
- 中英混排：同字号
- **绝对禁止**：衬线字体、装饰性字体

---

## 布局规范

### 尺寸
- 16:9（13.33" × 7.5"）

### 布局原则
- **居中版式优先**
- **充足留白**：页边距 ≥ 0.6"（约1.5cm）
- **网格化排版**：版心边界距页面边缘 0.8"

### 页面结构

| 页面类型 | 布局要求 |
|----------|----------|
| 封面页 | 居中标题 + 副标题，白色背景 |
| 目录页 | 编号列表或图标网格（≤4-5项） |
| 章节分隔页 | 大号章节编号 + 标题（可用 `#F2F4F7` 底色） |
| 内容页 | 标题 + 视觉元素 + 文字（必须含图表/图标） |
| 数据页 | 标题 + 图表 + 注解 |
| 对比页 | 左右并列或前后对比 |
| 关键数据页 | 大数字（48-72pt）+ 标签 + 上下文 |
| 结尾页 | 居中"谢谢" + 联系方式 |

---

## SVG 模板示例

### 封面页

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#FFFFFF"/>
  <!-- 标题 -->
  <text x="640" y="280" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="44" font-weight="500" fill="#990000" text-anchor="middle">
    报告标题
  </text>
  <!-- 副标题 -->
  <text x="640" y="360" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="20" fill="#333333" text-anchor="middle">
    副标题 · 2026年度
  </text>
  <!-- 华为红细线装饰 -->
  <rect x="560" y="420" width="160" height="4" fill="#C7000B"/>
  <!-- 页脚 -->
  <text x="1200" y="680" font-family="Arial" font-size="10" fill="#999999" text-anchor="end">
    Huawei Confidential
  </text>
</svg>
```

### 章节分隔页

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#F2F4F7"/>
  <!-- 大号章节编号 -->
  <text x="640" y="240" font-family="Arial" font-size="72" font-weight="700" 
        fill="#002FA7" text-anchor="middle">
    01
  </text>
  <!-- 章节标题 -->
  <text x="640" y="360" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="32" font-weight="500" fill="#990000" text-anchor="middle">
    章节标题
  </text>
  <!-- 华为红细线 -->
  <rect x="560" y="420" width="160" height="3" fill="#C7000B"/>
</svg>
```

### 内容页（标题 + 双栏）

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#FFFFFF"/>
  <!-- 标题 -->
  <text x="80" y="80" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="32" font-weight="500" fill="#990000">
    内容标题
  </text>
  <!-- 分割线 -->
  <line x1="80" y1="100" x2="1200" y2="100" stroke="#D9DEE3" stroke-width="1"/>
  
  <!-- 左栏正文 -->
  <text x="80" y="160" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="18" fill="#333333">
    <tspan x="80" dy="0">正文内容在此处...</tspan>
    <tspan x="80" dy="1.8em">第二段正文...</tspan>
  </text>
  
  <!-- 右栏浅灰卡片 -->
  <rect x="700" y="140" width="500" height="440" rx="8" 
        fill="#F2F4F7" stroke="#D9DEE3" stroke-width="1"/>
  <!-- 图表/图片区 -->
  <text x="950" y="380" font-family="Arial" font-size="14" fill="#999999" text-anchor="middle">
    图表区域
  </text>
  
  <!-- 页脚 -->
  <text x="1200" y="690" font-family="Arial" font-size="10" fill="#999999" text-anchor="end">
    Huawei Confidential
  </text>
</svg>
```

### 关键数据页

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#FFFFFF"/>
  <!-- 大数字 -->
  <text x="400" y="300" font-family="Arial" font-size="72" font-weight="700" 
        fill="#002FA7" text-anchor="middle">
    98.7%
  </text>
  <!-- 标签 -->
  <text x="400" y="380" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="20" fill="#333333" text-anchor="middle">
    客户满意度
  </text>
  <!-- 右侧红色标注 -->
  <text x="850" y="280" font-family="Arial" font-size="28" font-weight="700" 
        fill="#C7000B" text-anchor="middle">
    ↑ 12.3%
  </text>
  <text x="850" y="340" font-family="Noto Sans CJK SC, sans-serif" 
        font-size="16" fill="#333333" text-anchor="middle">
    同比增长
  </text>
  <!-- 华为红细线 -->
  <rect x="560" y="420" width="160" height="3" fill="#C7000B"/>
  <!-- 页脚 -->
  <text x="1200" y="690" font-family="Arial" font-size="10" fill="#999999" text-anchor="end">
    Huawei Confidential
  </text>
</svg>
```

---

## 设计禁忌

- ❌ 大面积红色背景
- ❌ 全局加粗字体
- ❌ 同一页面超过 4 种颜色
- ❌ 衬线字体
- ❌ 拥挤布局
- ❌ 标题下划线装饰（AI 生成典型特征）
- ❌ 深色模式混用

---

## 交付前检查

- [ ] 标题颜色 `#990000`
- [ ] 无衬线字体
- [ ] 字重偏轻/常规
- [ ] 留白充足
- [ ] 标题居中对齐
- [ ] 红色仅作点缀
- [ ] 背景白色/极浅灰
- [ ] 页脚含 "Huawei Confidential"
- [ ] 单页颜色 ≤ 4 种
