"""Extract only the audited source table pages; requires pypdfium2.

Use the bundled Python runtime documented in data/README.md. Extraction and
source acquisition are separate from the dependency-free numerical analysis.
"""

from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parent.parent


def main():
    for name, page_number in (("heat-2023-24", 66), ("nuggets-2025-26", 57)):
        document = pdfium.PdfDocument(str(ROOT / "data/raw" / (name + ".pdf")))
        page = document[page_number - 1]
        textpage = page.get_textpage()
        output = ROOT / "data/extracted" / name
        output.mkdir(parents=True, exist_ok=True)
        (output / ("page-%03d.txt" % page_number)).write_text(textpage.get_text_range())
        textpage.close()
        preview = ROOT / "data/qa"
        preview.mkdir(parents=True, exist_ok=True)
        page.render(scale=1.8).to_pil().save(str(preview / (name + "-table.png")))
        page.close()
        document.close()


if __name__ == "__main__":
    main()
