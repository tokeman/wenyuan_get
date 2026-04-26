#!/bin/bash
# 文元获取工具 (wenyuan_get) - 主入口
# 用法: wenyuan_get.sh <关键词> [--theme "主题名"] [-R|-E|-B]
# 示例: wenyuan_get.sh "DeepSeek V4, GPT5.5" --theme "华为亮白" -B

set -e

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-$(pwd)}"
INPUT_KEYWORDS=""
PAPERS=""
MODE="B"
THEME=""
SHOW_HELP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --theme)
            THEME="$2"
            shift 2
            ;;
        -R|-E|-B)
            MODE="${1#-}"
            shift
            ;;
        -h|--help)
            SHOW_HELP=1
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
                PAPERS="${PAPERS}${PAPERS:+$'\n'}- $1"
            fi
            shift
            ;;
    esac
done

if [ $SHOW_HELP -eq 1 ] || [ -z "$INPUT_KEYWORDS" ]; then
    echo "用法: wenyuan_get.sh <关键词> [--theme '主题名'] [-R|-E|-B]"
    echo "  --theme: 指定主题（可选）"
    echo "          支持：华为亮白 / 靛蓝瓷 / 墨水经典 / 红太阳 / Theme A-E 等"
    echo "  -R: R 版本（PNG 渲染图）"
    echo "  -E: E 版本（SVG 直接导入）"
    echo "  -B: 双版本同时生成（默认）"
    echo "示例: wenyuan_get.sh 'DeepSeek V4, GPT5.5' --theme '华为亮白' -B"
    exit 0
fi

sanitized=$(echo "$INPUT_KEYWORDS" | tr ' ' '_' | tr -cd 'a-zA-Z0-9_')
OUTPUT_PREFIX="${WORK_DIR}/${sanitized}"
mkdir -p "$WORK_DIR"

# 使用 Python 构建 prompt（避免 sed 多字节字符问题）
python3 - "${TOOL_DIR}" "${INPUT_KEYWORDS}" "${PAPERS}" "${THEME}" << 'PYEOF'
import sys

tool_dir = sys.argv[1]
keywords = sys.argv[2]
papers = sys.argv[3] if len(sys.argv) > 3 else ""
theme = sys.argv[4] if len(sys.argv) > 4 else ""

with open(f"{tool_dir}/prompt_template.md") as f:
    template = f.read()

# 找到 [PAPERS] 和 [KEYWORDS] 位置
output = template.replace("[KEYWORDS]", keywords)

# 如果有论文列表
if papers:
    output = output.replace("[PAPERS]", f"\n{papers}")
else:
    output = output.replace("[PAPERS]", "")

# 如果指定了主题，追加主题引导
if theme:
    theme_guide = f"""

## 配色主题要求

请使用以下指定主题风格生成 SVG：

**指定主题: {theme}**

"""
    # 在 "## 输出要求" 前插入
    output = output.replace("## 输出要求", theme_guide + "\n## 输出要求")

with open("/root/.openclaw/workspace/prompt.txt", "w") as f:
    f.write(output)

print("Prompt generated OK", file=sys.stderr)
PYEOF

echo "=========================================="
echo "文元获取工具 | 关键词: ${INPUT_KEYWORDS}"
[ -n "$THEME" ] && echo "主题: ${THEME}"
echo "模式: $([ "$MODE" = "B" ] && echo "双版本 (R + E)" || echo "$MODE 版本")"
echo "=========================================="
echo "1. 生成 Prompt... ✅"
echo "2. 调用 Gemini CLI 生成 SVG..."

gemini -p "$(cat "${WORK_DIR}/prompt.txt")" > "${WORK_DIR}/output.md" 2>&1

if [ $? -eq 0 ]; then
    echo "   Gemini 生成完成 ✅"
else
    echo "❌ Gemini 调用失败"
    cat "${WORK_DIR}/output.md"
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
echo "   页数: ${SVG_COUNT} 页"
