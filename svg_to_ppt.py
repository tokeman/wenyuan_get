"""
svg_to_ppt.py - SVG 转 PPTX 渲染器（支持 R/E 双版本）

R 版本（Rendered）：cairosvg 渲染为 PNG，最佳兼容性
E 版本（Editable）：SVG + PNG 双轨嵌入，飞书/邮件转发不白屏

双轨结构：PowerPoint 用 PNG 做主图保底，SVG 作为矢量扩展层叠加。
支持 SVG 的客户端（PPT 2021+）显示矢量，不支持的自动降级 PNG。
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
# E 版本：SVG + PNG 双轨嵌入
# PowerPoint 2021+ 显示矢量，客户端降级显示 PNG
# ─────────────────────────────────────────
def render_e(svg_blocks, output_file):
    """SVG+PNG 双轨版 — 飞书/邮件转发不白屏"""
    print(f"Building E (SVG+PNG dual-track): {output_file}")

    # 1. 创建基础 PPTX
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)
    for _ in svg_blocks:
        prs.slides.add_slide(prs.slide_layouts[6])
    prs.save(output_file)

    # 2. 解压，注入 SVG + PNG 双轨
    tmpdir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(output_file, 'r') as z:
            z.extractall(tmpdir)

        media_dir = os.path.join(tmpdir, 'ppt', 'media')
        os.makedirs(media_dir, exist_ok=True)

        has_any_png = False

        for i, svg in enumerate(svg_blocks):
            slide_idx = i + 1
            svg_filename = f'image_{slide_idx}.svg'
            png_filename = f'image_{slide_idx}_fallback.png'

            # 写 SVG 文件（始终写入）
            svg_abs = os.path.join(media_dir, svg_filename)
            with open(svg_abs, 'w', encoding='utf-8') as f:
                f.write(svg)

            # 写 PNG 备用图（可能失败）
            png_abs = os.path.join(media_dir, png_filename)
            png_bytes = None
            try:
                png_bytes = cairosvg.svg2png(
                    bytestring=svg.encode('utf-8'),
                    output_width=1920, output_height=1080
                )
                with open(png_abs, 'wb') as f:
                    f.write(png_bytes)
                has_any_png = True
            except Exception as e:
                print(f"  Slide {slide_idx}: PNG fallback failed ({e})")

            # Bug 1 fix: 只在有 PNG 时才注入 PNG 关系
            _inject_svg_png_dual(
                tmpdir, slide_idx,
                svg_filename, png_filename,
                has_png=(png_bytes is not None)
            )

        # Bug 2 fix: Content-Type 按实际存在的内容注册
        _ensure_content_types(tmpdir, include_png=has_any_png)

        # 重新打包（Windows fix: 路径分隔符转正斜杠）
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zout:
            for root_dir, dirs, files in os.walk(tmpdir):
                for file in files:
                    filepath = os.path.join(root_dir, file)
                    arcname = os.path.relpath(filepath, tmpdir).replace(os.sep, '/')
                    zout.write(filepath, arcname)

        print(f"E saved: {output_file} ({len(svg_blocks)} slides, SVG+PNG dual-track)")

    finally:
        shutil.rmtree(tmpdir)


def _ensure_content_types(tmpdir, include_png=True):
    """确保 [Content_Types].xml 有 png 和 svg 条目（按需）"""
    ct_path = os.path.join(tmpdir, '[Content_Types].xml')
    ct_tree = etree.parse(ct_path)
    ct_root = ct_tree.getroot()
    svg_ct_ns = 'http://schemas.openxmlformats.org/package/2006/content-types'

    existing_exts = {
        el.get('Extension')
        for el in ct_root.findall(f'{{{svg_ct_ns}}}Default')
    }
    types_to_add = [('svg', 'image/svg+xml')]
    if include_png:
        types_to_add.append(('png', 'image/png'))
    for ext, ct in types_to_add:
        if ext not in existing_exts:
            el = etree.SubElement(ct_root, f'{{{svg_ct_ns}}}Default')
            el.set('Extension', ext)
            el.set('ContentType', ct)

    ct_tree.write(ct_path, xml_declaration=True, encoding='UTF-8', standalone=True)


def _inject_svg_png_dual(tmpdir, slide_idx, svg_filename, png_filename, has_png):
    """
    双轨注入：slide XML + .rels + PNG 备用图

    结构：
      PNG 作为主 blip（兼容性保底）
      SVG 作为 extLst 扩展层（矢量覆盖，PowerPoint 2021+ 优先渲染）
    """
    slide_path = os.path.join(tmpdir, 'ppt', 'slides', f'slide{slide_idx}.xml')
    rels_path  = os.path.join(tmpdir, 'ppt', 'slides', '_rels', f'slide{slide_idx}.xml.rels')

    slide_w, slide_h = 12192000, 6858000   # EMU: 16×9 inches
    rel_id_png = f'rId_png_{slide_idx}'
    rel_id_svg = f'rId_svg_{slide_idx}'

    # ── 1. 注入 slide XML ──
    tree = etree.parse(slide_path)
    root = tree.getroot()

    if has_png:
        # 双轨结构：PNG 主图 + SVG 扩展层
        pic_xml = f'''<p:pic
            xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
            xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main">
          <p:nvPicPr>
            <p:cNvPr id="{100 + slide_idx}" name="SVG Image {slide_idx}"/>
            <p:cNvPicPr>
              <a:picLocks noChangeAspect="1"/>
            </p:cNvPicPr>
            <p:nvPr/>
          </p:nvPicPr>
          <p:blipFill>
            <a:blip r:embed="{rel_id_png}">
              <a:extLst>
                <a:ext uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}">
                  <asvg:svgBlip r:embed="{rel_id_svg}"/>
                </a:ext>
              </a:extLst>
            </a:blip>
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
    else:
        # 纯 SVG（无 PNG 时退化为简单引用）
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
            <a:blip r:embed="{rel_id_svg}"/>
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

    # ── 2. 更新 .rels（Bug 1 fix: 只写实际存在的文件对应关系）──
    rels_tree = etree.parse(rels_path)
    rels_root = rels_tree.getroot()
    img_type = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image'

    rels_to_add = [(rel_id_svg, f'../media/{svg_filename}')]
    if has_png:
        rels_to_add.insert(0, (rel_id_png, f'../media/{png_filename}'))

    for rel_id, target in rels_to_add:
        el = etree.SubElement(rels_root, 'Relationship')
        el.set('Id', rel_id)
        el.set('Type', img_type)
        el.set('Target', target)

    rels_tree.write(rels_path, xml_declaration=True, encoding='UTF-8', standalone=True)

    # ── 3. Content_Types 已在 _ensure_content_types 统一处理 ──


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
