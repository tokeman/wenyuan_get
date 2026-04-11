"""
文元获取工具 (wenyuan_get)
AI 论文可视化 → SVG 报告卡片 → PPTX 打包
"""

import subprocess
import os

DEFAULT_WORK_DIR = "/root/.openclaw/workspace/ai-research"

def generate(keywords: str, papers: list = None, output_dir: str = DEFAULT_WORK_DIR) -> str:
    """
    主生成函数

    Args:
        keywords: 论文关键词
        papers: 可选，指定论文列表
        output_dir: 输出目录

    Returns:
        PPTX 文件路径
    """
    os.makedirs(output_dir, exist_ok=True)

    # 构建命令
    cmd = [
        os.path.join(os.path.dirname(__file__), "wenyuan_get.sh"),
        keywords
    ]
    if papers:
        cmd.extend(papers)

    # 执行
    env = os.environ.copy()
    env["WORK_DIR"] = output_dir
    result = subprocess.run(
        " ".join(f'"{c}"' for c in cmd),
        shell=True,
        capture_output=True,
        text=True,
        env=env
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=__stderr__)

    pptx_path = os.path.join(output_dir, "AI_Paper_Report.pptx")
    return pptx_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python -m wenyuan_get <关键词> [论文1] [论文2] ...")
        sys.exit(1)

    keywords = sys.argv[1]
    papers = sys.argv[2:] if len(sys.argv) > 2 else None
    result = generate(keywords, papers)
    print(f"PPT 已生成: {result}")
