"""
svg_to_ppt.py - SVG 转 PPTX 渲染器
支持双模式：
  - R 版本（Rendered）：cairosvg 渲染为 PNG，兼容性最强
  - E 版本（Editable）：SVG 文件直接导入，PowerPoint 2021+ 可完全编辑

PowerPoint 2021+: 右键 SVG 形状 → "转为形状" 即可编辑每个元素
"""

import re
import cairosvg
from pptx import Presentation
from pptx.util import Inches
import io
import os
import sys
import tempfile


def extract_svg_blocks(md_text):
    """提取所有 SVG 代码块"""
    return re.findall(r'<svg.*?</svg>', md_text, re.DOTALL)


def render_r_version(svg_blocks, output_file):
    """R 版本：所有 SVG 渲染为 PNG 嵌入 PPTX（兼容性最好）"""
    print(f"Building R (Rendered) version: {output_file}")

    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    for i, svg in enumerate(svg_blocks):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        png_data = cairosvg.svg2png(
            bytestring=svg.encode('utf-8'),
            output_width=1920,
            output_height=1080
        )
        stream = io.BytesIO(png_data)
        slide.shapes.add_picture(stream, 0, 0,
                               width=prs.slide_width,
                               height=prs.slide_height)
        # 备注存源码
        try:
            notes = slide.notes_slide.notes_text_frame
            notes.text = f"[R version] SVG source for slide {i+1}:\n" + svg
        except:
            pass
        print(f"  Slide {i+1}: PNG rendered")

    prs.save(output_file)
    print(f"R version saved: {output_file}")


def render_e_version(svg_blocks, output_file):
    """E 版本：SVG 文件直接导入 PPTX（PowerPoint 2021+ 可完全编辑）"""
    print(f"Building E (Editable) version: {output_file}")

    # 创建临时 SVG 文件夹（和 PPTX 同目录）
    svg_dir = output_file.replace('.pptx', '_svg_files')
    os.makedirs(svg_dir, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    for i, svg in enumerate(svg_blocks):
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # 保存单个 SVG 文件
        svg_path = os.path.join(svg_dir, f'slide_{i+1:02d}.svg')
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg)

        # 插入 SVG 文件到 PPTX
        try:
            slide.shapes.add_picture(svg_path, 0, 0,
                                   width=prs.slide_width,
                                   height=prs.slide_height)
            print(f"  Slide {i+1}: SVG file embedded ({svg_path})")
        except Exception as e:
            # 回退到 PNG
            png_data = cairosvg.svg2png(
                bytestring=svg.encode('utf-8'),
                output_width=1920,
                output_height=1080
            )
            stream = io.BytesIO(png_data)
            slide.shapes.add_picture(stream, 0, 0,
                                   width=prs.slide_width,
                                   height=prs.slide_height)
            print(f"  Slide {i+1}: PNG fallback ({e})")

        # 备注存源码
        try:
            notes = slide.notes_slide.notes_text_frame
            notes.text = f"[E version] Raw SVG source for slide {i+1}:\n" + svg
        except:
            pass

    prs.save(output_file)
    print(f"E version saved: {output_file} (SVG files in: {svg_dir}/)")


def build_ppt_from_md(input_md_file, output_prefix, mode='B'):
    """
    主函数

    Args:
        input_md_file:  输入 markdown 文件路径
        output_prefix:  输出文件名前缀（不含扩展名）
        mode: 'R' = Rendered PNG | 'E' = Editable SVG | 'B' = Both
    """
    print(f"Reading: {input_md_file} ...")

    if not os.path.exists(input_md_file):
        print(f"File not found: {input_md_file}")
        return

    with open(input_md_file, "r", encoding="utf-8") as f:
        text = f.read()

    svg_blocks = extract_svg_blocks(text)

    if not svg_blocks:
        print("No SVG found.")
        return

    print(f"Found {len(svg_blocks)} SVG slides")

    if mode in ('R', 'B'):
        render_r_version(svg_blocks, f"{output_prefix}_R.pptx")
    if mode in ('E', 'B'):
        render_e_version(svg_blocks, f"{output_prefix}_E.pptx")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output.md"
    output_prefix = sys.argv[2] if len(sys.argv) > 2 else "output"
    mode = sys.argv[3].upper() if len(sys.argv) > 3 else "B"

    build_ppt_from_md(input_file, output_prefix, mode)
