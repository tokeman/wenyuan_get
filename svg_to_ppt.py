"""
svg_to_ppt.py - SVG 转 PPTX 渲染器（支持 R/E 双版本）

R 版本（Rendered）：cairosvg 渲染为 PNG，最佳兼容性
E 版本（Editable）：SVG 文件直接打包，PowerPoint 2021+ 可通过"图片转为形状"完全编辑
"""

import re
import cairosvg
from pptx import Presentation
from pptx.util import Inches
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from lxml import etree
import io
import os
import sys
import zipfile
import shutil
import tempfile


def extract_svg_blocks(md_text):
    """提取所有 SVG 代码块"""
    return re.findall(r'<svg.*?</svg>', md_text, re.DOTALL)


# ─────────────────────────────────────────
# R 版本：PNG 渲染
# ─────────────────────────────────────────
def render_r(svg_blocks, output_file):
    """PNG 渲染版 — 兼容性最强"""
    print(f"Building R (Rendered): {output_file}")
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    for i, svg in enumerate(svg_blocks):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        png = cairosvg.svg2png(
            bytestring=svg.encode('utf-8'),
            output_width=1920, output_height=1080
        )
        slide.shapes.add_picture(io.BytesIO(png), 0, 0,
                              width=prs.slide_width, height=prs.slide_height)
        _add_notes(slide, f"[R] SVG source (slide {i+1}):\n{svg}")
        print(f"  Slide {i+1}: PNG")

    prs.save(output_file)
    print(f"R saved: {output_file}")


# ─────────────────────────────────────────
# E 版本：SVG 直接嵌入（XML 级别注入）
# PowerPoint 2021+ 支持 SVG 直接导入，可取消组合编辑
# ─────────────────────────────────────────
def render_e(svg_blocks, output_file):
    """SVG 源码直嵌版 — PowerPoint 2021+ 可完全编辑"""
    print(f"Building E (Editable SVG): {output_file}")

    # 1. 创建基础 PPTX（一张空白幻灯片）
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)
    for _ in svg_blocks:
        prs.slides.add_slide(prs.slide_layouts[6])
    prs.save(output_file)

    # 2. 直接操作 PPTX ZIP，注入 SVG
    tmpdir = tempfile.mkdtemp()
    try:
        # 解压 PPTX
        with zipfile.ZipFile(output_file, 'r') as z:
            z.extractall(tmpdir)

        # 创建 media 目录
        media_dir = os.path.join(tmpdir, 'ppt', 'media')
        os.makedirs(media_dir, exist_ok=True)

        # 注入每个 SVG
        for i, svg in enumerate(svg_blocks):
            slide_idx = i + 1  # 1-based
            svg_filename = f'image_{slide_idx}.svg'
            svg_path_in_zip = f'ppt/media/{svg_filename}'
            svg_abs = os.path.join(media_dir, svg_filename)

            # 写 SVG 文件
            with open(svg_abs, 'w', encoding='utf-8') as f:
                f.write(svg)

            # 注入 slide XML，更新关系文件和 [Content_Types].xml
            _inject_svg_into_slide(tmpdir, slide_idx, svg_path_in_zip)

        # 重新打包
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    filepath = os.path.join(root, file)
                    arcname = os.path.relpath(filepath, tmpdir)
                    zout.write(filepath, arcname)

        print(f"E saved: {output_file} ({len(svg_blocks)} SVG embedded)")

    finally:
        shutil.rmtree(tmpdir)


def _inject_svg_into_slide(tmpdir, slide_idx, svg_path_in_zip):
    """向 slide XML 中注入 SVG 图片引用"""
    ns = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    }

    slide_path = os.path.join(tmpdir, 'ppt', 'slides', f'slide{slide_idx}.xml')
    rels_path = os.path.join(tmpdir, 'ppt', 'slides', '_rels', f'slide{slide_idx}.xml.rels')
    ct_path   = os.path.join(tmpdir, '[Content_Types].xml')

    # ── 更新 slide XML：插入 `<p:pic>` 形状 ──
    tree = etree.parse(slide_path)
    root = tree.getroot()

    # 计算 offset（按 slide 顺序排布）
    # 每个 SVG 占满整页：x=0, y=0, cx=幻灯片宽, cy=幻灯片高
    slide_w = 12192000  # EMU: 16 inches × 914400
    slide_h = 6858000   # EMU: 9 inches × 914400
    off_x = 0
    off_y = 0
    ext_cx = slide_w
    ext_cy = slide_h

    # 新建 p:pic
    pic_xml = f'''
    <p:pic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
           xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <p:nvPicPr>
        <p:cNvPr id="2" name="SVG Image {slide_idx}"/>
        <p:cNvPicPr/>
        <p:nvPr/>
      </p:nvPicPr>
      <p:blipFill>
        <a:blip r:embed="rId9999_{slide_idx}"/>
        <a:stretch><a:fillRect/></a:stretch>
      </p:blipFill>
      <p:spPr>
        <a:xfrm>
          <a:off x="{off_x}" y="{off_y}"/>
          <a:ext cx="{ext_cx}" cy="{ext_cy}"/>
        </a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
      </p:spPr>
    </p:pic>
    '''.strip()

    # 找到 <p:spTree> 并插入
    sp_tree = root.find('.//{http://schemas.openxmlformats.org/presentationml/2006/main}spTree')
    if sp_tree is not None:
        pic_elem = etree.fromstring(pic_xml)
        sp_tree.append(pic_elem)
        tree.write(slide_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # ── 更新 slide rels：添加 image/svg+xml 关系 ──
    rels_tree = etree.parse(rels_path)
    rels_root = rels_tree.getroot()

    new_rel = etree.SubElement(rels_root, 'Relationship')
    new_rel.set('Id', f'rId9999_{slide_idx}')
    new_rel.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')
    new_rel.set('Target', svg_path_in_zip)

    rels_tree.write(rels_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # ── 更新 [Content_Types].xml：添加 image/svg+xml 内容类型 ──
    ct_tree = etree.parse(ct_path)
    ct_root = ct_tree.getroot()

    svg_ct = 'http://schemas.openxmlformats.org/package/2006/content-types'
    svg_ext = svg_path_in_zip.split('/')[-1]

    new_ct = etree.SubElement(ct_root, f'{{{svg_ct}}}Default')
    new_ct.set('Extension', 'svg')
    new_ct.set('ContentType', 'image/svg+xml')

    ct_tree.write(ct_path, xml_declaration=True, encoding='UTF-8', standalone=True)


def _add_notes(slide, text):
    """存入备注"""
    try:
        slide.notes_slide.notes_text_frame.text = text
    except:
        pass


# ─────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────
def build_ppt_from_md(input_md_file, output_prefix, mode='B'):
    """
    Args:
        input_md_file:   markdown 文件（含 SVG 代码块）
        output_prefix:   输出文件名前缀
        mode: 'R' 仅渲染版 | 'E' 仅编辑版 | 'B' 双版本
    """
    print(f"Reading: {input_md_file} ...")
    if not os.path.exists(input_md_file):
        print(f"File not found: {input_md_file}")
        return

    with open(input_md_file, 'r', encoding='utf-8') as f:
        text = f.read()

    svg_blocks = extract_svg_blocks(text)
    if not svg_blocks:
        print("No SVG found.")
        return

    print(f"Found {len(svg_blocks)} SVG slides")

    if mode in ('R', 'B'):
        render_r(svg_blocks, f"{output_prefix}_R.pptx")
    if mode in ('E', 'B'):
        render_e(svg_blocks, f"{output_prefix}_E.pptx")


if __name__ == '__main__':
    inp  = sys.argv[1] if len(sys.argv) > 1 else 'output.md'
    pref = sys.argv[2] if len(sys.argv) > 2 else 'output'
    mod  = sys.argv[3].upper() if len(sys.argv) > 3 else 'B'
    build_ppt_from_md(inp, pref, mod)
