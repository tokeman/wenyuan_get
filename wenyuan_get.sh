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
cat > "${WORK_DIR}/prompt.txt" << EOF
# Role: AI Research Visualizer & Analyzer
你的任务是根据用户提供的"关键词"或"论文"，自动提取核心信息，并输出高质量的 SVG 汇报矢量图。
(请确保输出包含完整的 <svg>...</svg> 代码块，采用宽屏 1280x720 比例，使用淡蓝色、青绿色等专业配色，布局采用四宫格或三栏式，重点突出痛点、核心机制和突破性数据指标。不要输出任何外部图片链接。)

**重要：字体必须使用 "Noto Sans CJK SC", "Noto Sans CJK TC", "WenQuanYi Micro Hei", sans-serif，以确保中文正常显示。**

---
请帮我检索并总结以下论文，分别生成汇报 SVG 卡片：
${PAPERS:+$(echo -e "$PAPERS")}
关键词: ${INPUT_KEYWORDS}
EOF

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
