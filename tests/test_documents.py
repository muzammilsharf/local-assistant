from odf import opendocument, teletype

from local_assistant.tools.documents import _build


def test_build_creates_valid_odt(tmp_path):
    output_path = tmp_path / "test_doc.odt"
    content = (
        "# Summary\n"
        "This is a brief summary of the document.\n"
        "# Key points\n"
        "- First key takeaway.\n"
        "* Second key takeaway.\n"
        "Concluding note."
    )

    _build("Document Title", content, output_path)

    assert output_path.exists()
    doc = opendocument.load(str(output_path))

    elements = [
        (elem.getAttribute("stylename"), teletype.extractText(elem).strip())
        for elem in doc.text.childNodes
    ]

    # Verify Title
    assert elements[0] == ("DocTitle", "Document Title")

    # Verify Headings
    headings = [text for style, text in elements if style == "DocHeading"]
    assert "Summary" in headings
    assert "Key points" in headings

    # Verify Bullets
    bullets = [text for style, text in elements if text.startswith("\u2022")]
    assert len(bullets) == 2
    assert bullets[0] == "\u2022 First key takeaway."
    assert bullets[1] == "\u2022 Second key takeaway."

    # Verify Body Paragraphs
    body = [text for style, text in elements if style == "DocBody"]
    assert "This is a brief summary of the document." in body
    assert "Concluding note." in body


def test_build_empty_lines(tmp_path):
    output_path = tmp_path / "empty_lines.odt"
    content = "\n\n# Summary\n\n\nOne point.\n\n"

    _build("Title", content, output_path)

    assert output_path.exists()
    doc = opendocument.load(str(output_path))
    # DocTitle + DocHeading + DocBody
    assert len(doc.text.childNodes) == 3
