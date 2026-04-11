"""
svg_to_ppt.py - SVG 转 PPTX 渲染器
支持：SVG 直接导入 + PNG 降级 + 源码存入备注
PowerPoint 2021+ 可直接编辑 SVG 图形
"""

import re
import cairosvg
from pptx import Presentation
from pptx.util import Inches, Inches as Width
from pptx.enum.shapes import MSO_SHAPE_TYPE
import io
import os
import sys
import tempfile


def extract_svg_blocks(md_text):
    """提取所有 SVG 代码块"""
    return re.findall(r'<svg.*?</svg>', md_text, re.DOTALL)


def add_svg_to_slide(slide, svg_content, slide_index, prs):
    """尝试插入 SVG，失败则降级为 PNG"""
    slide_width = prs.slide_width
    slide_height = prs.slide_height

    # 方案1：PowerPoint 2021+ 原生 SVG 支持（最佳：完全可编辑）
    try:
        from pptx.shapes.picture import PictureShape
        from pptx.oxml.ns import qn
        from lxml import etree

        # 写入临时 SVG 文件
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False, mode='w', encoding='utf-8') as tmp:
            tmp.write(svg_content)
            tmp_path = tmp.name

        try:
            # 直接添加 SVG 文件（pptx 内部会转换为 ODP 兼容格式）
            # 注意：python-pptx 的 add_picture 对 SVG 支持因版本而异
            slide.shapes.add_picture(tmp_path, 0, 0,
                                     width=slide_width,
                                     height=slide_height)
            print(f"  -> Slide {slide_index}: SVG (native)")
            return True
        finally:
            os.unlink(tmp_path)
    except ImportError:
        pass

    # 方案2：PNG 降级渲染（通用保底）
    try:
        png_data = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=1920,
            output_height=1080
        )
        stream = io.BytesIO(png_data)
        slide.shapes.add_picture(stream, 0, 0,
                                 width=slide_width,
                                 height=slide_height)
        print(f"  -> Slide {slide_index}: PNG (cairosvg fallback)")
        return True
    except Exception as e:
        print(f"  -> Slide {slide_index}: PNG failed: {e}")
        return False


def add_svg_to_notes(slide, svg_content, slide_index):
    """将 SVG 源码存入幻灯片备注，供用户直接编辑"""
    try:
        notes_slide = slide.notes_slide
        notes_tf = notes_slide.notes_text_frame
        notes_tf.text = f"=== Slide {slide_index} SVG Source ===\n"
        notes_tf.text += "(You can copy the code below and save as .svg to edit)\n\n"
        notes_tf.text += svg_content
    except Exception:
        pass  # 备注不可用时忽略


def build_ppt_from_md(input_md_file, output_ppt_file):
    """主函数"""
    print(f"Reading: {input_md_file} ...")

    if not os.path.exists(input_md_file):
        print(f"File not found: {input_md_file}")
        return

    with open(input_md_file, "r", encoding="utf-8") as f:
        text = f.read()

    svg_blocks = extract_svg_blocks(text)

    if not svg_blocks:
        print("No SVG found in file.")
        return

    print(f"Found {len(svg_blocks)} SVG slides")

    # 16:9 宽屏
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    success = 0
    for i, svg_content in enumerate(svg_blocks):
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        # 尝试插入 SVG/PNG
        if add_svg_to_slide(slide, svg_content, i + 1, prs):
            success += 1

        # 同时存入备注（完全可编辑的源码备份）
        add_svg_to_notes(slide, svg_content, i + 1)

    prs.save(output_ppt_file)
    print(f"PPTX saved: {output_ppt_file} ({success}/{len(svg_blocks)} SVG slides)")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.pptx"
    build_ppt_from_md(input_file, output_file)
