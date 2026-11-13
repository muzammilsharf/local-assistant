import re
from datetime import datetime
from pathlib import Path

from odf.opendocument import OpenDocumentText
from odf.style import ParagraphProperties, Style, TextProperties
from odf.text import H, P

from ..config import OUTPUT_DIR


def _safe_name(title):
    name = re.sub(r"[^\w\- ]", "", title).strip().replace(" ", "_")
    return name[:60] or "document"


def _unique_path(name):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.odt"
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = OUTPUT_DIR / f"{name}_{stamp}.odt"
    return path


def _build(title, content, path):
    doc = OpenDocumentText()

    title_style = Style(name="DocTitle", family="paragraph")
    title_style.addElement(TextProperties(fontsize="22pt", fontweight="bold"))
    title_style.addElement(ParagraphProperties(marginbottom="0.4cm"))

    heading_style = Style(name="DocHeading", family="paragraph")
    heading_style.addElement(TextProperties(fontsize="15pt", fontweight="bold"))
    heading_style.addElement(ParagraphProperties(margintop="0.4cm", marginbottom="0.2cm"))

    body_style = Style(name="DocBody", family="paragraph")
    body_style.addElement(TextProperties(fontsize="12pt"))
    body_style.addElement(ParagraphProperties(marginbottom="0.25cm"))

    for style in (title_style, heading_style, body_style):
        doc.styles.addElement(style)

    doc.text.addElement(P(stylename=title_style, text=title))
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            doc.text.addElement(
                H(outlinelevel=1, stylename=heading_style, text=line.lstrip("# ").strip())
            )
        elif line.startswith(("- ", "* ")):
            doc.text.addElement(P(stylename=body_style, text="\u2022 " + line[2:]))
        else:
            doc.text.addElement(P(stylename=body_style, text=line))

    doc.save(str(path))


def create_document(title: str, content: str) -> str:
    """Create a LibreOffice .odt document in the user's Documents/Sam folder.

    Args:
        title: Short document title. It is also used as the file name.
        content: The full document text. Start a line with '# ' for a heading
            and with '- ' for a bullet point. Other lines are paragraphs.
    """
    path = _unique_path(_safe_name(title))
    _build(title, content, path)
    shown = str(path).replace(str(Path.home()), "~")
    return f"Created {shown}"
