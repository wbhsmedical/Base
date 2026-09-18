"""Turn non-native files into page PNGs. Text / image / PDF stay native."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TEXT_EXT = {".txt", ".md", ".json", ".csv", ".tsv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
PDF_EXT = {".pdf"}
# Office-ish: unzip XML and rasterize extracted text as a "scan".
ZIP_XML = {
    ".docx": "word/document.xml",
    ".pptx": None,  # one image per slide xml
}


def prepare(job_dir: Path, filename: str, data: bytes) -> dict:
    ext = Path(filename).suffix.lower()
    raw = job_dir / "input"
    raw.mkdir(exist_ok=True)
    (raw / filename).write_bytes(data)

    if ext in PDF_EXT:
        return _pdf(job_dir, data)

    if ext in IMAGE_EXT:
        dest = job_dir / "source" / filename
        dest.write_bytes(data)
        return {"kind": "images", "files": [str(dest.relative_to(job_dir))]}

    if ext in TEXT_EXT:
        p = job_dir / "source.txt"
        p.write_bytes(data)
        return {"kind": "text", "files": ["source.txt"]}

    text = _extract_text(filename, data)
    pages = _rasterize(job_dir / "source", text or f"(no extractable text from {filename})")
    rel = [str(p.relative_to(job_dir)) for p in pages]
    return {"kind": "images", "files": rel, "converted_from": filename}


def prepare_many(job_dir: Path, items: list[tuple[str, bytes]]) -> dict:
    """Several uploads → one ingest dict. Image names stay distinct."""
    files: list[str] = []
    kind = "images"
    converted = []
    for name, data in items:
        info = prepare(job_dir, name, data)
        files.extend(info.get("files") or [])
        kind = info.get("kind") or kind
        if "converted_from" in info:
            converted.append(info["converted_from"])
    out = {"kind": kind, "files": files}
    if converted:
        out["converted_from"] = converted
    return out


def _pdf(job_dir: Path, data: bytes) -> dict:
    p = job_dir / "source.pdf"
    p.write_bytes(data)
    # Page PNGs if poppler is here; otherwise one native PDF (OpenRouter file-parser).
    if shutil.which("pdftoppm"):
        out = job_dir / "source"
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftoppm", "-png", str(p), str(out / "page")], check=True)
        rel = [str(x.relative_to(job_dir)) for x in sorted(out.glob("page*.png"))]
        if rel:
            return {"kind": "images", "files": rel, "converted_from": "source.pdf"}
    return {"kind": "pdf", "files": ["source.pdf"]}


def _extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".docx":
        return _xml_texts(data, prefix="word/document.xml")
    if ext == ".pptx":
        return _pptx_text(data)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return f"Binary file {filename} ({len(data)} bytes). Not decoded."


def _xml_texts(data: bytes, prefix: str) -> str:
    import re
    import zipfile
    from io import BytesIO

    z = zipfile.ZipFile(BytesIO(data))
    if prefix not in z.namelist():
        return ""
    xml = z.read(prefix).decode("utf-8", "replace")
    return "\n".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml))


def _pptx_text(data: bytes) -> str:
    import re
    import zipfile
    from io import BytesIO

    z = zipfile.ZipFile(BytesIO(data))
    slides = sorted(n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml"))
    chunks = []
    for i, name in enumerate(slides, 1):
        xml = z.read(name).decode("utf-8", "replace")
        lines = re.findall(r"<a:t[^>]*>([^<]*)</a:t>", xml)
        chunks.append(f"— slide {i} —\n" + "\n".join(lines))
    return "\n\n".join(chunks)


def _rasterize(out_dir: Path, text: str, width: int = 1280, height: int = 1660) -> list[Path]:
    """Paint text onto white PNG pages (scanned-page stand-in)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()

    def line_w(s: str) -> float:
        box = font.getbbox(s)
        return box[2] - box[0]

    words = text.replace("\r", "").split("\n")
    pages: list[Path] = []
    y_limit = height - 80
    page_i = 0
    img = None
    draw = None
    y = 60

    def new_page():
        nonlocal img, draw, y, page_i
        if img is not None:
            path = out_dir / f"page-{page_i:02d}.png"
            img.save(path)
            pages.append(path)
        page_i += 1
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        y = 60

    new_page()
    for line in words:
        buf = line if line else " "
        while buf:
            cut = buf
            while line_w(cut) > width - 120 and len(cut) > 8:
                cut = cut[:-1]
            if cut != buf and " " in cut:
                cut = cut.rsplit(" ", 1)[0]
            if y > y_limit:
                new_page()
            draw.text((60, y), cut, fill="black", font=font)
            y += 36
            rest = buf[len(cut) :]
            buf = rest.lstrip() if rest.strip() else ""
    if img is not None:
        path = out_dir / f"page-{page_i:02d}.png"
        img.save(path)
        pages.append(path)
    return pages
