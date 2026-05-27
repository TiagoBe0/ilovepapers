"""
build_index_cards.py
--------------------
Genera las <article class="card"> para todos los papers con resumen HTML
y las inserta en index.html reemplazando el bloque de cards existente.
"""

import json
import re
import sys
from pathlib import Path

BASE        = Path(__file__).parent
PAPPERS_DIR = BASE / "pappers"
OUTPUT_DIR  = BASE / "output"
INDEX       = BASE / "index.html"

# ── Tags por paper_id (keywords → tags CSS) ──────────────────────────────────
# Tags disponibles en el filtro: Radiación, MD, Fusión, Materiales, IA, Biología, Software
TAG_RULES = [
    # (substring en paper_id o título, tag)
    (r'radiac|irradiac|cascada|damage|nordlund|vacanci|void|defect|PKA|dpa', 'Radiación'),
    (r'MD|molecular|lammps|dinamica|ablacion|kMC|boleininger|thermal_transport|grafos_MD|steinhardt|voxel_void|hemani', 'MD'),
    (r'fusion|tungsteno|tokamak|lucareali|tonks', 'Fusión'),
    (r'3dcnn|cnn|cgcnn|carnet|autoencoder|vae|cvae|djinn|dgcnn|pointnet|voxelnet|torchpoint|partnet|unet|OMC25|review_DL|OE.BERT|DGP_multitarea|ML_vacancias|MLIP|backprop|IA|machine|learning|neural|deep|surrogate|graph|grafos|fingerprint|FaVAD', 'IA'),
    (r'biolog|entomol|tonks', 'Biología'),
    (r'software|chemiscope|torchpoint|visualiz', 'Software'),
    (r'materiales|material|cristal|HEA|silice|silicio|nanoporoso|ferroelec|fotocatal|TiO2|elastica|constante|bond|steinhardt|thermal|transport|ugwumadu|stem|MLIP|hafnio|HfO', 'Materiales'),
    (r'IA|3dcnn|cnn|autoencoder|vae|cvae|djinn|dgcnn|pointnet|voxelnet|torchpoint|partnet|unet|OE.BERT|DGP|ML_vacanci|MLIP|review_DL|OMC25|backprop', 'IA'),
]

def get_tags(paper_id: str, title: str) -> list[str]:
    combined = (paper_id + " " + title).lower()
    found = []
    seen = set()
    for pattern, tag in TAG_RULES:
        if tag not in seen and re.search(pattern, combined, re.I):
            found.append(tag)
            seen.add(tag)
    return found or ["Materiales"]


# ── Extracción de metadata (reutilizada de generate_html_static.py) ──────────

def extract_metadata(text: str) -> dict:
    meta = {"title": "", "autores": "", "revista": "", "doi": "", "year": ""}

    m = re.search(r'^#\s+Resumen\s*[—–-]+\s*(.+)$', text, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()
    if not meta["title"]:
        m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if m:
            meta["title"] = m.group(1).strip()
    if not meta["title"]:
        m = re.search(r'[Tt][ií]tulo\s*:\s*(.+)', text)
        if m:
            meta["title"] = m.group(1).strip()

    m = re.search(r'\*\*Autores\*\*\s*:\s*(.+)', text)
    if not m:
        m = re.search(r'Autores?\s*:\s*(.+)', text)
    if m:
        raw = m.group(1).strip()
        # acortar: tomar hasta el primer ';' o '(' o primer apellido + et al.
        authors = re.sub(r'\(.*?\)', '', raw).strip()
        parts = re.split(r',\s*', authors)
        if len(parts) > 3:
            meta["autores"] = parts[0] + " et al."
        else:
            meta["autores"] = authors[:60]

    m = re.search(r'\*\*Revista\*\*\s*:\s*(.+)', text)
    if not m:
        m = re.search(r'Revista\s*:\s*(.+)', text)
    if m:
        meta["revista"] = m.group(1).strip()[:80]

    m = re.search(r'DOI\s*:\s*([\S]+)', text)
    if not m:
        m = re.search(r'10\.\d{4,}/\S+', text)
    if m:
        meta["doi"] = m.group(1).strip().rstrip(')')

    # Year: from DOI, arXiv, or paper_id
    m = re.search(r'(\b20[0-9]{2}\b|\b19[0-9]{2}\b)', meta["doi"])
    if not m:
        m = re.search(r'(\b20[0-9]{2}\b|\b19[0-9]{2}\b)', text[:500])
    if m:
        meta["year"] = m.group(1)

    return meta


# ── Figuras para el carousel ──────────────────────────────────────────────────

def pick_carousel_images(paper_id: str, max_imgs: int = 4) -> list[dict]:
    """Elige las mejores figuras para el carousel: primero las que tienen caption."""
    figs_json = PAPPERS_DIR / f"{paper_id}_figures" / "figures.json"
    if not figs_json.exists():
        return []

    figs = json.loads(figs_json.read_text(encoding="utf-8")).get("figures", [])
    images_dir = PAPPERS_DIR / f"{paper_id}_figures" / "images"

    def find_img(fig):
        for f in sorted(images_dir.glob(f"{fig['figure_id']}_*.png")):
            return f
        for f in sorted(images_dir.glob(f"{fig['figure_id']}.png")):
            return f
        return None

    # Separar figuras con caption vs sin caption
    with_cap = [f for f in figs if f.get("caption", "").strip()]
    without  = [f for f in figs if not f.get("caption", "").strip()]

    candidates = with_cap + without
    result = []
    for fig in candidates:
        img = find_img(fig)
        if img:
            result.append({
                "src": f"pappers/{paper_id}_figures/images/{img.name}",
                "caption": fig.get("caption", "").strip() or f"Figura {fig['figure_id']}",
                "tooltip": (fig.get("caption", "").strip() or fig["figure_id"])[:60],
            })
        if len(result) >= max_imgs:
            break

    return result


# ── Generación de una card ────────────────────────────────────────────────────

def build_card(paper_id: str, txt_path: Path) -> str:
    raw = txt_path.read_text(encoding="utf-8")
    meta = extract_metadata(raw)

    title  = meta["title"] or paper_id.replace("_", " ")
    year   = meta["year"] or "—"
    authors = meta["autores"] or "—"
    tags   = get_tags(paper_id, title)
    imgs   = pick_carousel_images(paper_id)

    tags_data  = " ".join(tags)
    tags_html  = "\n        ".join(f'<span class="tag">{t}</span>' for t in tags)
    resumen_url = f"output/{paper_id}_resumen.html"
    pdf_url     = f"pappers/{paper_id}.pdf"

    # Carousel slides
    if imgs:
        slides_html = "\n        ".join(
            f'<div class="fig-slide">'
            f'<img src="{im["src"]}" data-caption="{im["caption"][:80]}" alt="" loading="lazy">'
            f'<div class="fig-tooltip">{im["tooltip"]}</div>'
            f'</div>'
            for im in imgs
        )
        strip_inner = f'''<div class="fig-slides">
        {slides_html}
      </div>
      <div class="fig-dots"></div>'''
    else:
        strip_inner = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#556;font-size:11px;">sin figuras</div>'

    # Resumen button: always enabled (all have HTML)
    has_html = (OUTPUT_DIR / f"{paper_id}_resumen.html").exists()
    resumen_btn = (f'<a href="{resumen_url}" class="btn primary">Resumen</a>'
                   if has_html else
                   '<span class="btn disabled">Resumen</span>')

    return f'''
  <!-- {paper_id} -->
  <article class="card" data-tags="{tags_data}">
    <div class="fig-strip" onclick="openCurrentSlide(this)">
      {strip_inner}
    </div>
    <div class="card-body">
      <div class="card-top">
        <span class="year-badge">{year}</span>
        <div class="card-title">{title}</div>
      </div>
      <div class="card-authors">{authors}</div>
      <div class="tags">
        {tags_html}
      </div>
      <div class="card-actions">
        {resumen_btn}
        <a href="{pdf_url}" class="btn">PDF</a>
      </div>
    </div>
  </article>'''


# ── IDs ya presentes en index.html ───────────────────────────────────────────

def existing_paper_ids(html: str) -> set[str]:
    """Extrae los paper_ids que ya tienen card en el index."""
    # buscamos los href de Resumen y PDF para inferir el paper_id
    found = set()
    for m in re.finditer(r'href="output/([^"]+)_resumen\.html"', html):
        found.add(m.group(1))
    for m in re.finditer(r'href="pappers/([^"]+)\.pdf"', html):
        pid = m.group(1)
        # excluir sub-rutas con /
        if "/" not in pid:
            found.add(pid)
    return found


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    index_html = INDEX.read_text(encoding="utf-8")
    already    = existing_paper_ids(index_html)

    new_cards = []
    all_tags  = set()

    for txt in sorted(PAPPERS_DIR.glob("resumen_*.txt")):
        paper_id = txt.stem.removeprefix("resumen_")
        if paper_id in already:
            print(f"  SKIP (ya existe): {paper_id}")
            continue
        if not (PAPPERS_DIR / f"{paper_id}_figures").is_dir():
            print(f"  SKIP (sin figuras): {paper_id}")
            continue

        try:
            card = build_card(paper_id, txt)
            new_cards.append(card)
            tags = get_tags(paper_id, "")
            all_tags.update(tags)
            print(f"  OK: {paper_id}")
        except Exception as e:
            print(f"  FAIL: {paper_id}: {e}", file=sys.stderr)

    if not new_cards:
        print("Nada nuevo que agregar.")
        return

    # ── Insertar cards justo antes del <p class="no-results"> ──────────
    marker = '<p class="no-results"'
    if marker not in index_html:
        print("[ERROR] No se encontró el marcador de inserción en index.html")
        sys.exit(1)

    new_block = "\n".join(new_cards) + "\n\n  "
    updated = index_html.replace(marker, new_block + marker, 1)

    # ── Actualizar contador en el header ─────────────────────────────
    total_cards = len(re.findall(r'class="card"', updated))
    updated = re.sub(
        r'(<span class="count"[^>]*>)\d+ papers?(<)',
        lambda m: f'{m.group(1)}{total_cards} papers{m.group(2)}',
        updated
    )

    # ── Actualizar stagger de animaciones (hasta 40 cards) ───────────
    stagger_lines = "\n".join(
        f"  .card:nth-child({i+1})  {{ animation-delay: -{round((i * 1.37) % 5.0, 1)}s; }}"
        for i in range(min(total_cards, 40))
    )
    updated = re.sub(
        r'(/\* Stagger each card.*?\*/).*?(/\* .* \*/)',
        lambda m: m.group(1) + "\n" + stagger_lines + "\n\n  " + m.group(2),
        updated,
        flags=re.DOTALL,
        count=1
    )

    INDEX.write_text(updated, encoding="utf-8")
    print(f"\nAgregadas {len(new_cards)} cards. Total: {total_cards} papers.")

    # ── Mostrar tags nuevos para añadir al filterbar ──────────────────
    existing_filter_tags = set(re.findall(r'data-tag="([^"]+)"', index_html)) - {"all"}
    missing_tags = all_tags - existing_filter_tags
    if missing_tags:
        print(f"\nTags sin botón en filterbar: {', '.join(sorted(missing_tags))}")
        print("Considera agregar estos botones al <div class=\"filterbar\">.")


if __name__ == "__main__":
    main()
