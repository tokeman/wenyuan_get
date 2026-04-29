#!/bin/bash
# 文元获取工具 (wenyuan_get) - 主入口
# 用法: wenyuan_get.sh <关键词> [--theme "主题名"] [--model "模型名"] [-R|-E|-B]
# 示例: wenyuan_get.sh "DeepSeek V4" --theme "华为亮白" --model "deepseek-v4-pro" -B

set -e

TOOL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${WORK_DIR:-$(pwd)}"
INPUT_KEYWORDS=""
PAPERS=""
MODE="B"
THEME=""
MODEL=""
SHOW_HELP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --theme)
            THEME="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
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
    echo "用法: wenyuan_get.sh <关键词> [--theme '主题名'] [--model '模型名'] [-R|-E|-B]"
    echo "  --theme: 指定主题（可选）"
    echo "          支持：华为亮白 / 靛蓝瓷 / 墨水经典 / 红太阳 / Theme A-E 等"
    echo "  --model: 指定模型（可选，默认 gemini）"
    echo "          支持：gemini / deepseek-v4-pro / deepseek-chat 等"
    echo "  -R: R 版本（PNG 渲染图）"
    echo "  -E: E 版本（SVG 直接导入）"
    echo "  -B: 双版本同时生成（默认）"
    echo "示例: wenyuan_get.sh 'DeepSeek V4' --theme '华为亮白' --model 'deepseek-v4-pro' -B"
    exit 0
fi

sanitized=$(echo "$INPUT_KEYWORDS" | sed 's/[/\\:*?"<>|]/_/g; s/__*/_/g')
OUTPUT_PREFIX="${WORK_DIR}/${sanitized}"
mkdir -p "$WORK_DIR"

echo "=========================================="
echo "文元获取工具 | 关键词: ${INPUT_KEYWORDS}"
[ -n "$THEME" ] && echo "主题: ${THEME}"
[ -n "$MODEL" ] && echo "模型: ${MODEL}"
echo "模式: $([ "$MODE" = "B" ] && echo "双版本 (R + E)" || echo "$MODE 版本")"
echo "=========================================="
echo "1. 生成 Prompt... ✅"
echo "2. 调用 LLM 生成 SVG..."

# 使用 Python 调用 LLM（支持 Gemini 和 DeepSeek）
python3 - "${TOOL_DIR}" "${INPUT_KEYWORDS}" "${PAPERS}" "${THEME}" "${WORK_DIR}" "${MODEL}" << 'PYEOF'
import sys
import os
import json
import urllib.request
import urllib.error

tool_dir = sys.argv[1]
keywords = sys.argv[2]
papers = sys.argv[3] if len(sys.argv) > 3 else ""
theme = sys.argv[4] if len(sys.argv) > 4 else ""
work_dir = sys.argv[5] if len(sys.argv) > 5 else "/tmp"
model = sys.argv[6] if len(sys.argv) > 6 else ""

# 读取配置
config_path = f"{tool_dir}/config.json"
config = {}
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)

# 读取 prompt 模板
with open(f"{tool_dir}/prompt_template.md") as f:
    template = f.read()

output = template.replace("[KEYWORDS]", keywords)
if papers:
    output = output.replace("[PAPERS]", f"\n{papers}")
else:
    output = output.replace("[PAPERS]", "")

if theme:
    theme_guide = f"""

## 配色主题要求

请使用以下指定主题风格生成 SVG：

**指定主题: {theme}**

"""
    output = output.replace("## 输出要求", theme_guide + "\n## 输出要求")

with open(f"{work_dir}/prompt.txt", "w") as f:
    f.write(output)

# 读取 prompt 内容
with open(f"{work_dir}/prompt.txt") as f:
    prompt_content = f.read()

print(f"Using model: {model}", file=sys.stderr)

if model.startswith("deepseek") or model.startswith("gpt"):
    # OpenAI compatible (DeepSeek)
    cfg = config.get("deepseek", {})
    api_key = cfg.get("api_key", "")
    base_url = cfg.get("base_url", "https://api.deepseek.com")
    model_name = model or cfg.get("model", "deepseek-v4-pro")

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_content}],
        "max_tokens": 8192,
        "temperature": 0.7
    }

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.load(resp)
            content = result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        content = e.read().decode()
        raise Exception(f"HTTP {e.code}: {content}")

elif model == "gemini" or model == "":
    # Gemini CLI
    import subprocess
    result = subprocess.run(
        ["gemini", "-p", prompt_content],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "GOOGLE_GENAI_USE_GCA": "true",
             "PATH": os.environ.get("PATH", "")}
    )
    if result.returncode != 0:
        raise Exception(f"Gemini failed: {result.stderr}")
    content = result.stdout

else:
    raise Exception(f"Unknown model: {model}")

# 提取 SVG 内容
import re
svg_blocks = re.findall(r'<svg[^>]+>.*?</svg>', content, re.DOTALL)
if not svg_blocks:
    # 尝试从 markdown 代码块中提取
    svg_blocks = re.findall(r'```svg\s*(<svg[^>]+>.*?</svg>)\s*```', content, re.DOTALL)

if not svg_blocks:
    raise Exception(f"No SVG found. Content preview: {content[:500]}")

with open(f"{work_dir}/output.md", "w") as f:
    f.write("\n".join(svg_blocks))

print(f"Generated {len(svg_blocks)} SVG slides", file=sys.stderr)
PYEOF

LLM_EXIT=$?

if [ $LLM_EXIT -eq 0 ]; then
    echo "   LLM 生成完成 ✅"
else
    echo "❌ LLM 调用失败"
    cat "${WORK_DIR}/output.md" 2>/dev/null
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
