"""
svg_to_ppt.py - SVG 转 PPTX 渲染器（支持 R/E 双版本）

R 版本（Rendered）：cairosvg 渲染为 PNG，最佳兼容性
E 版本（Editable）：SVG 文件直接打包，PowerPoint 2021+ 可通过"图片转为形状"完全编辑
"""

import re
import cairosvg
from pptx import Presentation
from pptx.util import Inches
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
        try:
            png = cairosvg.svg2png(
                bytestring=svg.encode('utf-8'),
                output_width=1920, output_height=1080
            )
            slide.shapes.add_picture(io.BytesIO(png), 0, 0,
                                 width=prs.slide_width, height=prs.slide_height)
            print(f"  Slide {i+1}: PNG")
        except Exception as e:
            print(f"  Slide {i+1}: PNG failed ({e}), skipped")
        _add_notes(slide, f"[R] SVG source (slide {i+1}):\n{svg}")

    prs.save(output_file)
    print(f"R saved: {output_file}")


# ─────────────────────────────────────────
# E 版本：SVG 直接嵌入（XML 级别注入）
# PowerPoint 2021+ 支持 SVG 直接导入，可取消组合编辑
# ─────────────────────────────────────────
def render_e(svg_blocks, output_file):
    """SVG 源码直嵌版 — PowerPoint 2021+ 可完全编辑"""
    print(f"Building E (Editable SVG): {output_file}")

    # 1. 创建基础 PPTX
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)
    for _ in svg_blocks:
        prs.slides.add_slide(prs.slide_layouts[6])
    prs.save(output_file)

    # 2. 解压 PPTX，注入 SVG
    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(output_file, 'r') as z:
            z.extractall(tmpdir)

        media_dir = os.path.join(tmpdir, 'ppt', 'media')
        os.makedirs(media_dir, exist_ok=True)

        # Bug 2 fix: 先检查 [Content_Types].xml 是否已有 svg 条目
        ct_path = os.path.join(tmpdir, '[Content_Types].xml')
        ct_tree = etree.parse(ct_path)
        ct_root = ct_tree.getroot()
        svg_ct_ns = 'http://schemas.openxmlformats.org/package/2006/content-types'
        already_has_svg = any(
            el.get('Extension') == 'svg'
            for el in ct_root.findall(f'{{{svg_ct_ns}}}Default')
        )

        for i, svg in enumerate(svg_blocks):
            slide_idx = i + 1
            svg_filename = f'image_{slide_idx}.svg'
            svg_abs = os.path.join(media_dir, svg_filename)

            # 写 SVG 文件
            with open(svg_abs, 'w', encoding='utf-8') as f:
                f.write(svg)

            # 注入 XML（传 svg_filename，不含路径）
            _inject_svg_into_slide(tmpdir, slide_idx, svg_filename)

        # Bug 2 fix: svg 类型声明只插入一次（在所有幻灯片处理完后）
        if not already_has_svg:
            new_ct = etree.SubElement(ct_root, f'{{{svg_ct_ns}}}Default')
            new_ct.set('Extension', 'svg')
            new_ct.set('ContentType', 'image/svg+xml')
            ct_tree.write(ct_path, xml_declaration=True, encoding='UTF-8', standalone=True)

        # 重新打包
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root_dir, dirs, files in os.walk(tmpdir):
                for file in files:
                    filepath = os.path.join(root_dir, file)
                    arcname = os.path.relpath(filepath, tmpdir)
                    zout.write(filepath, arcname)

        print(f"E saved: {output_file} ({len(svg_blocks)} SVG embedded)")

    finally:
        shutil.rmtree(tmpdir)


def _inject_svg_into_slide(tmpdir, slide_idx, svg_filename):
    """
    向 slide XML 中注入 SVG 图片引用

    Bug 修复记录：
    - Bug 1: Target 路径改为相对于 .rels 文件的路径（../media/...）
    - Bug 2: [Content_Types].xml 的 svg 条目在 render_e 顶层统一处理
    - Bug 3: cNvPicPr 添加 picLocks，id 改为唯一值
    """
    slide_path = os.path.join(tmpdir, 'ppt', 'slides', f'slide{slide_idx}.xml')
    rels_path  = os.path.join(tmpdir, 'ppt', 'slides', '_rels', f'slide{slide_idx}.xml.rels')

    slide_w, slide_h = 12192000, 6858000   # EMU: 16×9 inches
    rel_id = f'rId9999_{slide_idx}'

    # ── 1. 注入 slide XML ──
    tree = etree.parse(slide_path)
    root = tree.getroot()

    pic_xml = f'''<p:pic
        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
        xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
        xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <p:nvPicPr>
        <p:cNvPr id="{100 + slide_idx}" name="SVG Image {slide_idx}"/>
        <p:cNvPicPr>
          <a:picLocks noChangeAspect="1"/>
        </p:cNvPicPr>
        <p:nvPr/>
      </p:nvPicPr>
      <p:blipFill>
        <a:blip r:embed="{rel_id}"/>
        <a:stretch><a:fillRect/></a:stretch>
      </p:blipFill>
      <p:spPr>
        <a:xfrm>
          <a:off x="0" y="0"/>
          <a:ext cx="{slide_w}" cy="{slide_h}"/>
        </a:xfrm>
        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
      </p:spPr>
    </p:pic>'''

    sp_tree = root.find(
        './/{http://schemas.openxmlformats.org/presentationml/2006/main}spTree'
    )
    if sp_tree is not None:
        sp_tree.append(etree.fromstring(pic_xml))
        tree.write(slide_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # ── 2. 更新 .rels（Bug 1 fix: 相对路径）──
    rels_tree = etree.parse(rels_path)
    rels_root = rels_tree.getroot()

    new_rel = etree.SubElement(rels_root, 'Relationship')
    new_rel.set('Id', rel_id)
    new_rel.set(
        'Type',
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'
    )
    new_rel.set('Target', f'../media/{svg_filename}')  # ← Bug 1 修复

    rels_tree.write(rels_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # ── 3. [Content_Types].xml 的 svg 条目已由 render_e 统一处理，
    #    此处不再操作（避免 Bug 2：重复插入）


def _add_notes(slide, text):
    """存入备注"""
    try:
        slide.notes_slide.notes_text_frame.text = text
    except Exception:
        pass


# ─────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────
def build_ppt_from_md(input_md_file, output_prefix, mode='B'):
    """
    Args:
        input_md_file:  markdown 文件（含 SVG 代码块）
        output_prefix:  输出文件名前缀（不含扩展名）
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
