from __future__ import annotations

from engine.ingest import prepare

TINY_PDF = b"""%PDF-1.1
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
trailer<</Root 1 0 R>>
%%EOF
"""


def test_ingest_pdf_native(tmp_path):
    d = tmp_path / "j"
    d.mkdir()
    (d / "source").mkdir()
    info = prepare(d, "x.pdf", TINY_PDF)
    assert info["kind"] in ("pdf", "images")
    assert (d / "source.pdf").read_bytes().startswith(b"%PDF")


def test_ingest_txt_native(tmp_path):
    d = tmp_path / "j"
    d.mkdir()
    (d / "source").mkdir()
    info = prepare(d, "n.md", b"# hello\nworld")
    assert info["kind"] == "text"


def test_ingest_png(tmp_path):
    d = tmp_path / "j"
    d.mkdir()
    (d / "source").mkdir()
    info = prepare(d, "a.png", b"\x89PNG\r\n")
    assert info["kind"] == "images"
    assert (d / info["files"][0]).is_file()


def test_ingest_docx_to_images(tmp_path):
    import zipfile
    from io import BytesIO

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>',
        )
        z.writestr(
            "word/document.xml",
            '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Docx body text here</w:t></w:r></w:p></w:body></w:document>",
        )
    d = tmp_path / "j"
    d.mkdir()
    (d / "source").mkdir()
    info = prepare(d, "a.docx", buf.getvalue())
    assert info["kind"] == "images"
    assert info["files"]
    assert (d / info["files"][0]).is_file()
