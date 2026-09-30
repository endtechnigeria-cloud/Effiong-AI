"""
EFFIONG AI - File Service (the "+" upload button feeds this)
============================================================
Turns anything the user uploads into something the multi-brain can observe:

    image  -> vision input (also used for math-in-image problems)
    pdf    -> text via pypdf; scanned PDFs are sent whole to Gemini (native PDF understanding)
    docx / pptx / xlsx / csv / txt / code / json / html / md -> extracted text
    audio  -> transcript (Groq Whisper, else Gemini)
    video  -> sent to Gemini when small enough, plus sampled frames for other tiers
    zip    -> treated as a FOLDER: every readable file inside is read (zip-bomb safe)

Uploaded bytes are used for the current request only and are never stored on the server or in shared memory.
"""
from __future__ import annotations

import io
import mimetypes
import os
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src import config
from src.brain.vision import normalize_image
from src.core.health import HEALTH, safe_import
from src.services.audio_service import audio_service
from src.utilities.text_utils import sha256_bytes, truncate

Blob = Tuple[str, bytes]

TEXT_EXT = {".txt", ".md", ".markdown", ".rst", ".log", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg",
            ".xml", ".html", ".htm", ".css", ".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".c", ".cpp", ".h", ".cs",
            ".go", ".rs", ".php", ".rb", ".sh", ".sql", ".r", ".tex", ".bib", ".srt", ".vtt", ".svg", ".env.example"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic"}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".oga", ".flac", ".aac", ".webm_audio", ".opus"}
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".mpeg", ".mpg", ".3gp"}
SHEET_EXT = {".csv", ".tsv", ".xlsx", ".xlsm", ".xls"}

INLINE_LIMIT = 18_000_000  # Gemini inline-data ceiling (bytes)
PER_FILE_TEXT = 30_000
TOTAL_TEXT = 70_000


@dataclass
class Attachment:
    name: str
    mime: str
    size: int
    kind: str
    sha256: str
    text: str = ""
    notes: List[str] = field(default_factory=list)
    images: List[Blob] = field(default_factory=list)   # vision inputs
    docs: List[Blob] = field(default_factory=list)     # inline-file inputs (Gemini only)

    def meta(self) -> Dict[str, Any]:
        """JSON-safe description that is stored in chat history (no bytes)."""
        return {"name": self.name, "kind": self.kind, "mime": self.mime, "size": self.size, "sha256": self.sha256,
                "notes": self.notes[:3]}


def _ext(name: str) -> str:
    return os.path.splitext(name.lower())[1]


def _kind(name: str, mime: str) -> str:
    ext = _ext(name)
    if ext == ".zip" or mime == "application/zip":
        return "folder"
    if ext in IMAGE_EXT or mime.startswith("image/"):
        return "image"
    if ext == ".pdf" or mime == "application/pdf":
        return "pdf"
    if ext in (".docx", ".dotx"):
        return "docx"
    if ext in (".pptx", ".potx"):
        return "pptx"
    if ext in SHEET_EXT:
        return "sheet"
    if ext in AUDIO_EXT or mime.startswith("audio/"):
        return "audio"
    if ext in VIDEO_EXT or mime.startswith("video/"):
        return "video"
    if ext in TEXT_EXT or mime.startswith("text/") or mime in ("application/json", "application/xml"):
        return "text"
    return "other"


class FileService:
    # ------------------------------------------------------------------ public
    def ingest(self, name: str, data: bytes, mime: Optional[str] = None, _depth: int = 0) -> Attachment:
        mime = mime or mimetypes.guess_type(name)[0] or "application/octet-stream"
        att = Attachment(name=name, mime=mime, size=len(data), kind=_kind(name, mime), sha256=sha256_bytes(data))
        max_bytes = config.limits()["max_file_mb"] * 1024 * 1024
        if len(data) > max_bytes:
            att.notes.append(f"Skipped: larger than {int(config.limits()['max_file_mb'])} MB limit.")
            return att
        try:
            getattr(self, f"_read_{att.kind}")(att, data, _depth)
        except Exception as exc:  # a broken file must never break the chat
            HEALTH.flag(f"files:{att.kind}", f"{exc.__class__.__name__}: {exc}")
            att.notes.append(f"Could not fully read this file ({exc.__class__.__name__}).")
        att.text = truncate(att.text, PER_FILE_TEXT)
        return att

    def ingest_many(self, files: List[Tuple[str, bytes, Optional[str]]]) -> List[Attachment]:
        limit = int(config.limits()["max_files_per_message"])
        return [self.ingest(n, d, m) for n, d, m in files[:limit]]

    # ------------------------------------------------------------------ readers
    def _read_text(self, att: Attachment, data: bytes, _d: int) -> None:
        att.text = data.decode("utf-8", errors="replace")

    def _read_image(self, att: Attachment, data: bytes, _d: int) -> None:
        mime, norm = normalize_image(data, att.mime)
        att.images.append((mime, norm))
        Image = safe_import("PIL.Image", "vision")
        if Image is not None:
            try:
                im = Image.open(io.BytesIO(data))
                att.text = f"[Image {att.name}: {im.size[0]}x{im.size[1]} px]"
            except Exception:
                att.text = f"[Image {att.name}]"

    def _read_pdf(self, att: Attachment, data: bytes, _d: int) -> None:
        pypdf = safe_import("pypdf", "pdf-read")
        text = ""
        if pypdf is not None:
            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = reader.pages
            att.notes.append(f"{len(pages)} pages")
            text = "\n".join((p.extract_text() or "") for p in pages[:40])
        att.text = text
        if len(text.strip()) < 200 and len(data) <= INLINE_LIMIT and config.get_keys("GEMINI_API_KEY"):
            att.docs.append(("application/pdf", data))
            att.notes.append("scanned/graphic PDF - sent whole to the vision brain")

    def _read_docx(self, att: Attachment, data: bytes, _d: int) -> None:
        docx = safe_import("docx", "word-read")
        if docx is None:
            att.notes.append("Word reader unavailable")
            return
        doc = docx.Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables[:10]:
            for row in table.rows[:40]:
                parts.append(" | ".join(c.text.strip() for c in row.cells))
        att.text = "\n".join(parts)

    def _read_pptx(self, att: Attachment, data: bytes, _d: int) -> None:
        pptx = safe_import("pptx", "ppt-read")
        if pptx is None:
            att.notes.append("PowerPoint reader unavailable")
            return
        prs = pptx.Presentation(io.BytesIO(data))
        out = []
        for i, slide in enumerate(prs.slides, 1):
            out.append(f"## Slide {i}")
            for shape in slide.shapes:
                if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                    out.append(shape.text_frame.text.strip())
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
                out.append("Notes: " + slide.notes_slide.notes_text_frame.text.strip())
        att.text = "\n".join(out)

    def _read_sheet(self, att: Attachment, data: bytes, _d: int) -> None:
        pd = safe_import("pandas", "sheet-read")
        if pd is None:
            att.text = data.decode("utf-8", errors="replace")
            return
        ext = _ext(att.name)
        if ext in (".csv", ".tsv"):
            df_map = {"data": pd.read_csv(io.BytesIO(data), sep="\t" if ext == ".tsv" else None, engine="python", nrows=2000)}
        else:
            df_map = pd.read_excel(io.BytesIO(data), sheet_name=None, nrows=2000)
        out = []
        for sheet, df in list(df_map.items())[:6]:
            out.append(f"## Sheet: {sheet}  ({df.shape[0]} rows x {df.shape[1]} cols)\nColumns: {', '.join(map(str, df.columns))}")
            out.append(df.head(60).to_csv(index=False))
            try:
                desc = df.describe(include="number")
                if not desc.empty:
                    out.append("Numeric summary:\n" + desc.round(3).to_csv())
            except Exception:
                pass
        att.text = "\n".join(out)

    def _read_audio(self, att: Attachment, data: bytes, _d: int) -> None:
        transcript = audio_service.transcribe(data, att.name, att.mime)
        if transcript:
            att.text = f"[Audio transcript of {att.name}]\n{transcript}"
        else:
            att.notes.append("Could not transcribe audio (no speech-to-text tier available).")

    def _read_video(self, att: Attachment, data: bytes, _d: int) -> None:
        if len(data) <= INLINE_LIMIT and config.get_keys("GEMINI_API_KEY"):
            att.docs.append((att.mime if att.mime.startswith("video/") else "video/mp4", data))
            att.notes.append("video sent to the vision brain")
        frames = self._sample_frames(data, _ext(att.name) or ".mp4")
        att.images.extend(frames)
        if frames:
            att.text = f"[Video {att.name}: {len(frames)} sampled frames attached]"
        elif not att.docs:
            att.notes.append("Video too large or unreadable - no frames could be sampled.")

    @staticmethod
    def _sample_frames(data: bytes, ext: str, count: int = 4) -> List[Blob]:
        """Grab a few evenly spaced frames (downscaled JPEGs) so non-Gemini tiers can 'see' the video."""
        imageio = safe_import("imageio.v3", "video-read")
        Image = safe_import("PIL.Image", "vision")
        if imageio is None or Image is None:
            return []
        import tempfile

        samples: List[bytes] = []
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            path = tmp.name
        try:
            for idx, frame in enumerate(imageio.imiter(path, plugin="FFMPEG")):
                if idx > 900:
                    break
                if idx % 20 == 0:
                    img = Image.fromarray(frame).convert("RGB")
                    img.thumbnail((960, 960))
                    buf = io.BytesIO()
                    img.save(buf, "JPEG", quality=80)
                    samples.append(buf.getvalue())
        except Exception as exc:
            HEALTH.flag("files:video", f"frame sampling failed: {exc.__class__.__name__}")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
        if not samples:
            return []
        step = max(1, len(samples) // count)
        return [("image/jpeg", b) for b in samples[::step][:count]]

    def _read_folder(self, att: Attachment, data: bytes, depth: int) -> None:
        if depth >= 1:
            att.notes.append("Nested archives are not opened.")
            return
        try:
            zf = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile:
            att.notes.append("Not a valid zip file.")
            return
        infos = [i for i in zf.infolist() if not i.is_dir() and not i.filename.startswith("__MACOSX")]
        if sum(i.file_size for i in infos) > 120_000_000:
            att.notes.append("Folder too large when unpacked (zip-bomb protection).")
            return
        listing, budget = [], 45
        for info in infos[:200]:
            listing.append(f"{info.filename} ({info.file_size:,} bytes)")
        att.text = f"[Folder {att.name}: {len(infos)} files]\n" + "\n".join(listing[:120]) + "\n"
        att.notes.append(f"{len(infos)} files in folder")
        for info in infos:
            if budget <= 0 or len(att.text) > PER_FILE_TEXT * 1.5:
                break
            if info.file_size > 15_000_000 or _ext(info.filename) == ".zip":
                continue
            child = self.ingest(os.path.basename(info.filename) or info.filename, zf.read(info), None, depth + 1)
            if child.kind in ("other",) and not child.text:
                continue
            budget -= 1
            att.text += f"\n--- {info.filename} ---\n{truncate(child.text, 4000)}\n"
            att.images.extend(child.images[:2])
            att.docs.extend(child.docs[:1])


def build_model_inputs(atts: List[Attachment]) -> Tuple[str, List[Blob], List[Blob]]:
    """Merge all attachments into (text_context, image_blobs, inline_doc_blobs) for the brain."""
    chunks: List[str] = []
    images: List[Blob] = []
    docs: List[Blob] = []
    budget = TOTAL_TEXT
    for a in atts:
        header = f"### Attached {a.kind}: {a.name}" + (f" ({'; '.join(a.notes)})" if a.notes else "")
        body = truncate(a.text, min(PER_FILE_TEXT, budget)) if a.text else ""
        budget -= len(body)
        chunks.append(header + ("\n" + body if body else ""))
        images.extend(a.images[:4])
        docs.extend(a.docs[:2])
        if budget <= 0:
            chunks.append("(further attachment text omitted - size limit)")
            break
    return "\n\n".join(chunks), images[:8], docs[:3]


file_service = FileService()
