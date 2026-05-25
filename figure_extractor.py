"""
figure_extractor.py
-------------------
Extrae todas las figuras (y charts) de un artículo científico en PDF
usando Docling, y las exporta en múltiples formatos:

  - JSON  → pipelines posteriores
  - MD    → revisión humana
  - TXT   → captions simples
  - CSV   → datasets / ML pipelines
  - PNG   → imágenes individuales

Uso:
    python figure_extractor.py paper.pdf

    python figure_extractor.py paper.pdf \
        --formats json md txt csv images

Requisitos:
    pip install docling pillow
"""

import argparse
import base64
import csv
import io
import json
import re
import sys

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# ── Docling ────────────────────────────────────────────────────────────────────
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import DocItemLabel


# ── Estructuras de datos ───────────────────────────────────────────────────────

@dataclass
class FigureRecord:
    """Representa una figura extraída del paper."""

    figure_id: str
    label: str
    caption: str

    page: Optional[int]
    bbox: Optional[dict]

    image_b64: Optional[str] = None
    image_path: Optional[str] = None

    # reservado para futuras mejoras OCR/VLM
    ocr_text: Optional[str] = None


@dataclass
class ExtractionResult:
    """Resultado completo de extracción."""

    source_file: str
    total_figures: int
    figures: list[FigureRecord] = field(default_factory=list)


# ── Utilidades ─────────────────────────────────────────────────────────────────

def clean_caption(text: str) -> str:
    """
    Limpia whitespace y caracteres problemáticos.
    """
    if not text:
        return ""

    text = " ".join(text.split())
    return text.strip()


def sanitize_filename(text: str, max_len: int = 40) -> str:
    """
    Convierte texto en nombre de archivo seguro.
    """
    text = clean_caption(text)

    if not text:
        return "no_caption"

    text = text[:max_len]

    text = re.sub(r"[^\w\s-]", "", text)
    text = text.replace(" ", "_")

    return text or "figure"


# ── Loader único Docling ───────────────────────────────────────────────────────

def load_doc(pdf_path: Path):
    """
    Convierte el PDF una sola vez y reutiliza el documento.
    """

    print(f"[+] Procesando PDF: {pdf_path.name}")

    pipeline_opts = PdfPipelineOptions()

    pipeline_opts.images_scale = 2.0
    pipeline_opts.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(
                pipeline_options=pipeline_opts
            )
        }
    )

    result = converter.convert(str(pdf_path))

    return result.document


# ── Extracción ─────────────────────────────────────────────────────────────────

def extract_figures(
    doc,
    source_file: str,
    embed_images: bool = False,
) -> ExtractionResult:
    """
    Extrae figuras + captions desde el documento Docling.
    """

    figure_labels = {
        DocItemLabel.PICTURE,
        DocItemLabel.CHART,
    }

    records: list[FigureRecord] = []

    counter = 0

    for item, _level in doc.iterate_items():

        if item.label not in figure_labels:
            continue

        counter += 1

        fig_id = f"fig_{counter:03d}"

        # ── Caption robusto ──────────────────────────────────────────────

        caption = ""

        try:
            caption = item.caption_text(doc)
        except Exception:
            pass

        caption = clean_caption(caption)

        # ── Provenance ───────────────────────────────────────────────────

        page_num: Optional[int] = None
        bbox: Optional[dict] = None

        if item.prov:

            prov = item.prov[0]

            page_num = prov.page_no

            if prov.bbox is not None:

                b = prov.bbox

                bbox = {
                    "l": b.l,
                    "t": b.t,
                    "r": b.r,
                    "b": b.b,
                }

        # ── Imagen opcional base64 ───────────────────────────────────────

        image_b64: Optional[str] = None

        pil_img = item.get_image(doc)

        if pil_img is not None and embed_images:

            buf = io.BytesIO()

            pil_img.save(buf, format="PNG")

            image_b64 = base64.b64encode(
                buf.getvalue()
            ).decode()

        records.append(
            FigureRecord(
                figure_id=fig_id,
                label=item.label.value,
                caption=caption,
                page=page_num,
                bbox=bbox,
                image_b64=image_b64,
            )
        )

    # ── Orden estable ────────────────────────────────────────────────────

    records.sort(
        key=lambda r: (
            r.page or 0,
            -(r.bbox["t"] if r.bbox else 0),
        )
    )

    # ── Reindexado ───────────────────────────────────────────────────────

    for i, rec in enumerate(records, start=1):
        rec.figure_id = f"fig_{i:03d}"

    print(f"[+] Figuras encontradas: {len(records)}")

    return ExtractionResult(
        source_file=source_file,
        total_figures=len(records),
        figures=records,
    )


# ── Exportadores ───────────────────────────────────────────────────────────────

def save_json(result: ExtractionResult, out_dir: Path) -> Path:
    """
    Guarda metadata completa en JSON.
    """

    out_path = out_dir / "figures.json"

    def record_to_dict(r: FigureRecord):

        d = asdict(r)

        # limpiar campos vacíos
        for k in list(d.keys()):
            if d[k] is None:
                del d[k]

        return d

    payload = {
        "source_file": result.source_file,
        "total_figures": result.total_figures,
        "figures": [
            record_to_dict(r)
            for r in result.figures
        ],
    }

    out_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"[+] JSON guardado en: {out_path}")

    return out_path


def save_markdown(
    result: ExtractionResult,
    out_dir: Path,
) -> Path:
    """
    Genera Markdown legible.
    """

    out_path = out_dir / "figures.md"

    lines = [
        "# Figuras extraídas",
        "",
        f"**Fuente:** `{result.source_file}`",
        f"**Total figuras:** {result.total_figures}",
        "",
    ]

    for rec in result.figures:

        page_info = (
            f"Página {rec.page}"
            if rec.page
            else "Página desconocida"
        )

        lines.extend([
            "---",
            "",
            f"## {rec.figure_id.upper()} · "
            f"{rec.label.capitalize()} · "
            f"{page_info}",
            "",
        ])

        if rec.image_path:
            lines.extend([
                f"![{rec.figure_id}]({rec.image_path})",
                "",
            ])

        caption = rec.caption or "_Sin caption_"

        lines.extend([
            f"**Caption:** {caption}",
            "",
        ])

    out_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"[+] Markdown guardado en: {out_path}")

    return out_path


def save_txt(
    result: ExtractionResult,
    out_dir: Path,
) -> Path:
    """
    Guarda captions simples en TXT.
    """

    out_path = out_dir / "captions.txt"

    lines = []

    for rec in result.figures:

        page_info = (
            f"(p. {rec.page})"
            if rec.page
            else ""
        )

        caption = rec.caption or "[Sin caption]"

        lines.append(
            f"{rec.figure_id} {page_info}"
        )

        lines.append(caption)

        lines.append("")

    out_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(f"[+] TXT guardado en: {out_path}")

    return out_path


def save_csv(
    result: ExtractionResult,
    out_dir: Path,
) -> Path:
    """
    Exporta metadata tabular para ML/datasets.
    """

    out_path = out_dir / "captions.csv"

    with open(
        out_path,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "figure_id",
            "page",
            "label",
            "caption",
            "image_path",
        ])

        for rec in result.figures:

            writer.writerow([
                rec.figure_id,
                rec.page,
                rec.label,
                rec.caption,
                rec.image_path,
            ])

    print(f"[+] CSV guardado en: {out_path}")

    return out_path


def save_images(
    doc,
    result: ExtractionResult,
    out_dir: Path,
) -> Path:
    """
    Guarda imágenes PNG individuales.
    """

    images_dir = out_dir / "images"

    images_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure_labels = {
        DocItemLabel.PICTURE,
        DocItemLabel.CHART,
    }

    items_with_images = []

    for item, _ in doc.iterate_items():

        if item.label in figure_labels:
            items_with_images.append(item)

    items_with_images.sort(
        key=lambda it: (
            it.prov[0].page_no
            if it.prov else 0,

            -(
                it.prov[0].bbox.t
                if (
                    it.prov and
                    it.prov[0].bbox
                )
                else 0
            ),
        )
    )

    for item, rec in zip(
        items_with_images,
        result.figures,
    ):

        pil_img = item.get_image(doc)

        if pil_img is None:

            print(
                f"  [!] {rec.figure_id}: "
                f"sin imagen disponible."
            )

            continue

        safe_caption = sanitize_filename(
            rec.caption
        )

        fname = (
            f"{rec.figure_id}_"
            f"{safe_caption}.png"
        )

        img_path = images_dir / fname

        pil_img.save(
            img_path,
            format="PNG",
        )

        rec.image_path = str(
            img_path.relative_to(out_dir)
        )

        print(
            f"  [+] {rec.figure_id} "
            f"→ {img_path.name}"
        )

    print(f"[+] Imágenes guardadas en: {images_dir}")

    return images_dir


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_args():

    p = argparse.ArgumentParser(
        description=(
            "Extrae figuras y captions "
            "desde un PDF científico."
        )
    )

    p.add_argument(
        "pdf",
        type=Path,
        help="Ruta al PDF.",
    )

    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Directorio de salida "
            "(default: <pdf>_figures)"
        ),
    )

    p.add_argument(
        "--formats",
        nargs="+",
        choices=[
            "json",
            "md",
            "txt",
            "csv",
            "images",
        ],
        default=[
            "json",
            "md",
            "txt",
            "csv",
            "images",
        ],
        help="Formatos de salida.",
    )

    return p.parse_args()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():

    args = parse_args()

    pdf_path = args.pdf.resolve()

    if not pdf_path.exists():

        print(
            f"[!] Archivo no encontrado: "
            f"{pdf_path}",
            file=sys.stderr,
        )

        sys.exit(1)

    out_dir = (
        args.out or
        pdf_path.parent /
        f"{pdf_path.stem}_figures"
    )

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ── Cargar documento UNA sola vez ──────────────────────────────────

    doc = load_doc(pdf_path)

    # ── Embedding base64 opcional ──────────────────────────────────────

    embed_images = (
        "json" in args.formats and
        "images" not in args.formats
    )

    # ── Extracción ─────────────────────────────────────────────────────

    result = extract_figures(
        doc=doc,
        source_file=str(pdf_path),
        embed_images=embed_images,
    )

    if result.total_figures == 0:

        print(
            "[!] No se encontraron figuras."
        )

        sys.exit(0)

    # ── Exportar imágenes ──────────────────────────────────────────────

    if "images" in args.formats:

        save_images(
            doc,
            result,
            out_dir,
        )

    # ── Exportar JSON ──────────────────────────────────────────────────

    if "json" in args.formats:

        save_json(
            result,
            out_dir,
        )

    # ── Exportar Markdown ──────────────────────────────────────────────

    if "md" in args.formats:

        save_markdown(
            result,
            out_dir,
        )

    # ── Exportar TXT ───────────────────────────────────────────────────

    if "txt" in args.formats:

        save_txt(
            result,
            out_dir,
        )

    # ── Exportar CSV ───────────────────────────────────────────────────

    if "csv" in args.formats:

        save_csv(
            result,
            out_dir,
        )

    print(
        f"\n✓ Extracción completada.\n"
        f"Salida: {out_dir}"
    )


if __name__ == "__main__":
    main()
