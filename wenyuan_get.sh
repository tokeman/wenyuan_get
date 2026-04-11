#!/bin/bash
# 文元获取工具 (wenyuan_get) - 主入口
# 用法: wenyuan_get.sh <关键词> [论文1] [论文2] ... [-R|-E|-B]
# 示例: wenyuan_get.sh "BCI" -B

set -e

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-$(pwd)}"
INPUT_KEYWORDS=""
PAPERS=""
MODE="B"  # B=Both, R=Rendered, E=Editable

# 解析参数
while [[ $# -gt 0 ]]; do
    case "$1" in
        -R|-E|-B)
            MODE="${1#-}"
            shift
            ;;
        -*)
            echo "未知选项: $1"
            exit 1
            ;;
        *)
            if [ -z "$INPUT_KEYWORDS" ]; then
                INPUT_KEYWORDS="$1"
            else
                PAPERS="${PAPERS}${PAPERS:+\n}- $1"
            fi
            shift
            ;;
    esac
done

if [ -z "$INPUT_KEYWORDS" ]; then
    echo "用法: wenyuan_get <关键词> [论文1] [论文2] ... [-R|-E|-B]"
    echo "  -R: R 版本（PNG 渲染图，兼容性最强）"
    echo "  -E: E 版本（SVG 直接导入，PowerPoint 2021+ 可完全编辑）"
    echo "  -B: 双版本同时生成（默认）"
    echo "示例: wenyuan_get \"BCI neural interfaces\" -B"
    exit 1
fi

# 生成文件名（从关键词提取）
sanitized=$(echo "$INPUT_KEYWORDS" | tr ' ' '_' | tr -cd 'a-zA-Z0-9_\-\u4e00-\u9fff')
OUTPUT_PREFIX="${WORK_DIR}/${sanitized}"

mkdir -p "$WORK_DIR"

# 构建 Prompt
cat > "${WORK_DIR}/prompt.txt" << 'PROMPT_EOF'
# Role: AI Research Visualizer & Analyzer
你的任务是根据用户提供的"关键词"或"论文"，自动提取核心信息，并输出高质量的 SVG 汇报矢量图。

**重要格式要求：**
- 分辨率: `width="1280" height="720" viewBox="0 0 1280 720"`
- 命名空间: `xmlns="http://www.w3.org/2000/svg"`
- 字体: `font-family="Noto Sans CJK SC, sans-serif"`（确保中文正常显示）

**SVG 兼容性约束（PowerPoint 直接打开）：**
1. 禁止外部引用：不引用外部图片、样式表、字体文件
2. 禁止脚本：不包含 JavaScript、CSS 动画
3. 路径优先：复杂图形用 `<path>` 代替 `<text>`（避免字体缺失方框）
4. 精简滤镜：尽量用纯色填充，避免复杂 SVG 滤镜

---
请帮我检索并总结以下论文，分别生成汇报 SVG 卡片：
${PAPERS:+$(echo -e "$PAPERS")}
关键词: ${INPUT_KEYWORDS}
PROMPT_EOF

echo "=========================================="
echo "文元获取工具 | 关键词: ${INPUT_KEYWORDS}"
echo "模式: $([ "$MODE" = "B" ] && echo "双版本 (R + E)" || echo "$MODE 版本")"
echo "=========================================="
echo "1. 生成 Prompt... ✅"
echo "2. 调用 Gemini CLI 生成 SVG..."

# 调用 Gemini CLI
gemini -p "$(cat "${WORK_DIR}/prompt.txt")" > "${WORK_DIR}/output.md" 2>&1

if [ $? -eq 0 ]; then
    echo "   Gemini 生成完成 ✅"
else
    echo "❌ Gemini 调用失败"
    exit 1
fi

SVG_COUNT=$(grep -c '<svg' "${WORK_DIR}/output.md" 2>/dev/null || echo 0)
echo "   生成 ${SVG_COUNT} 张 SVG 卡片"

echo ""
echo "3. 渲染 SVG → PPTX..."

MODE_NAME="$MODE"
[ "$MODE" = "B" ] && MODE_NAME="B (双版本)"

python3 "${TOOL_DIR}/svg_to_ppt.py" \
    "${WORK_DIR}/output.md" \
    "${OUTPUT_PREFIX}" \
    "${MODE_NAME}" 2>&1

echo ""
echo "=========================================="
echo "✅ 完成！"
if [ "$MODE" = "B" ]; then
    echo "   R 版本: ${OUTPUT_PREFIX}_R.pptx"
    echo "   E 版本: ${OUTPUT_PREFIX}_E.pptx"
else
    echo "   文件: ${OUTPUT_PREFIX}_${MODE}.pptx"
fi
echo "   SVG 文件: ${OUTPUT_PREFIX}_E_svg_files/"
echo "   页数: ${SVG_COUNT} 页"
