import re
import cairosvg
from pptx import Presentation
from pptx.util import Inches
import io
import os

def build_ppt_from_md(input_md_file="output.md", output_ppt_file="AI_Paper_Report.pptx"):
    print(f"Reading: {input_md_file} ...")

    if not os.path.exists(input_md_file):
        print(f"File not found: {input_md_file}")
        return

    with open(input_md_file, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract all SVG code blocks
    svg_blocks = re.findall(r'<svg.*?</svg>', text, re.DOTALL)

    if not svg_blocks:
        print("No SVG found in file.")
        return

    print(f"Found {len(svg_blocks)} SVG slides, rendering...")

    # Init PPT (16:9)
    prs = Presentation()
    prs.slide_width = Inches(16)
    prs.slide_height = Inches(9)

    for i, svg_content in enumerate(svg_blocks):
        try:
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=1920,
                output_height=1080
            )
            image_stream = io.BytesIO(png_data)
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            slide.shapes.add_picture(
                image_stream,
                0, 0,
                width=prs.slide_width,
                height=prs.slide_height
            )
            print(f"  -> Slide {i+1} done")
        except Exception as e:
            print(f"  -> SVG {i+1} failed: {e}")

    prs.save(output_ppt_file)
    print(f"PPTX saved: {output_ppt_file}")

if __name__ == "__main__":
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else "output.md"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "AI_Paper_Report.pptx"
    build_ppt_from_md(input_file, output_file)
