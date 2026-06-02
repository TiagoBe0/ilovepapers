"""
generate_html_static.py
-----------------------
Convierte resumen_*.txt + *_figures/ → HTML con template CSS.
Sin API ni dependencias externas (solo markdown library).

Uso:
    python generate_html_static.py              # todos los pendientes
    python generate_html_static.py --paper ID   # uno solo
    python generate_html_static.py --force      # regenerar todos
"""

import argparse
import json
import re
import sys
from pathlib import Path

import markdown as md_lib

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
PAPPERS_DIR = BASE / "pappers"
OUTPUT_DIR  = BASE / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── CSS (idéntico al template existente) ──────────────────────────────────────
TEMPLATE_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --paper:      #fafaf8;  --surface:    #ffffff;  --panel:      #ffffff;
    --ink:        #18202a;  --muted:      #5a6472;  --line:       #d8dde4;
    --accent:     #174a7e;  --accent-h:   #0d3259;  --gold:       #b8860b;
    --teal:       #0a6858;  --soft-blue:  #eef3fb;  --soft-gold:  #fdf6e3;
    --soft-teal:  #e6f4f1;  --warn:       #fff8e1;
    --nav-h:      44px;     --max-w:      960px;
  }

  html { scroll-behavior: smooth; }
  body { font-family: 'Lora', Georgia, serif; font-size: 16px; line-height: 1.75;
         background: var(--paper); color: var(--ink); }

  /* Nav */
  .top-nav { position: sticky; top: 0; z-index: 200; height: var(--nav-h);
    background: var(--accent); display: flex; align-items: center; gap: 12px;
    padding: 0 20px; box-shadow: 0 2px 8px rgba(0,0,0,.25); }
  .top-nav a.back { color: rgba(255,255,255,.85); text-decoration: none;
    font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500;
    display: flex; align-items: center; gap: 6px; padding: 5px 12px;
    border: 1px solid rgba(255,255,255,.3); border-radius: 20px; transition: background .15s; }
  .top-nav a.back:hover { background: rgba(255,255,255,.15); }
  .top-nav .nav-title { color: rgba(255,255,255,.6); font-family: 'Playfair Display', serif;
    font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .top-nav .journal-name { margin-left: auto; color: rgba(255,255,255,.5);
    font-family: 'Inter', sans-serif; font-size: 11px; font-style: italic; white-space: nowrap; }

  /* Header */
  header { background: linear-gradient(160deg, #0d2a4a 0%, #174a7e 60%, #1a5c8a 100%);
    color: #fff; padding: 52px 28px 44px; border-bottom: 4px solid var(--gold); }
  header .inner { max-width: var(--max-w); margin: 0 auto; }
  .journal-stripe { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600;
    letter-spacing: 2.5px; text-transform: uppercase; color: var(--gold); margin-bottom: 18px;
    display: flex; align-items: center; gap: 10px; }
  .journal-stripe::after { content: ''; flex: 1; height: 1px; background: rgba(184,134,11,.4); }
  h1 { font-family: 'Playfair Display', serif; font-size: clamp(22px, 4vw, 40px);
    font-weight: 700; line-height: 1.15; letter-spacing: -.3px; margin-bottom: 16px; }
  .subtitle { font-family: 'Lora', serif; font-style: italic; font-size: 16px;
    color: rgba(255,255,255,.78); max-width: 820px; margin-bottom: 28px; }
  .meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 10px; font-family: 'Inter', sans-serif; font-size: 12.5px; color: rgba(255,255,255,.8); }
  .meta div { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15);
    padding: 10px 14px; border-radius: 6px; }
  .meta div strong { color: var(--gold); display: block; margin-bottom: 2px;
    font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
  .meta a { color: rgba(255,255,255,.7); }
  .meta a:hover { color: #fff; }

  /* Layout */
  main, .inner { max-width: var(--max-w); margin: 0 auto; }
  main { padding: 40px 24px 80px; }
  section { margin-bottom: 48px; }

  /* Typography */
  h2 { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700;
    color: var(--accent); margin: 0 0 18px; padding-bottom: 10px;
    border-bottom: 2px solid var(--line); position: relative; }
  h2::before { content: ''; position: absolute; bottom: -2px; left: 0;
    width: 48px; height: 2px; background: var(--gold); }
  h3 { font-family: 'Playfair Display', serif; font-size: 17px; color: var(--ink); margin: 0 0 8px; }
  p { margin: 0 0 16px; }
  ul, ol { padding-left: 24px; margin: 0 0 16px; }
  li { margin-bottom: 6px; }
  a { color: var(--teal); }
  a:hover { color: var(--accent); }
  code { font-family: monospace; background: #f0f4f8; padding: 2px 5px; border-radius: 3px; font-size: 14px; }
  pre { background: #1a2332; color: #e2e8f0; padding: 16px 20px; border-radius: 8px;
    overflow-x: auto; margin: 0 0 16px; font-size: 13px; }
  blockquote { border-left: 4px solid var(--accent); padding: 12px 20px;
    background: var(--soft-blue); margin: 0 0 16px; border-radius: 0 6px 6px 0; }

  .lead { font-size: 17px; font-style: italic; color: #2a3540; background: var(--soft-blue);
    border-left: 4px solid var(--accent); padding: 22px 24px; border-radius: 0 8px 8px 0;
    margin-bottom: 24px; line-height: 1.7; }
  .tag { display: inline-block; margin: 0 6px 8px 0; padding: 4px 11px; border-radius: 20px;
    background: var(--soft-blue); color: var(--accent); border: 1px solid #c2d2ea;
    font-family: 'Inter', sans-serif; font-size: 11.5px; font-weight: 600; letter-spacing: .2px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px; margin: 18px 0; }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 8px;
    padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
  .card h3 { color: var(--accent); font-size: 15px; margin-bottom: 8px; }
  .important { background: var(--soft-gold); border-left: 4px solid var(--gold);
    padding: 18px 22px; border-radius: 0 8px 8px 0; margin-bottom: 16px; }

  table { width: 100%; border-collapse: collapse; background: var(--surface);
    border: 1px solid var(--line); margin: 20px 0; font-family: 'Inter', sans-serif;
    font-size: 13.5px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
  th, td { border: 1px solid var(--line); padding: 11px 14px; text-align: left; vertical-align: top; }
  th { background: var(--accent); color: #fff; font-weight: 600; font-size: 12px;
    letter-spacing: .4px; text-transform: uppercase; }
  tr:nth-child(even) td { background: #f7f9fc; }

  /* Figures */
  .figure-list { display: flex; flex-direction: column; gap: 32px; }
  figure { margin: 0; background: var(--surface); border: 1px solid var(--line);
    border-radius: 10px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,.07);
    transition: box-shadow .2s; }
  figure:hover { box-shadow: 0 6px 24px rgba(0,0,0,.12); }
  @media (min-width: 680px) {
    figure { display: grid; grid-template-columns: 56% 44%;
      grid-template-rows: auto 1fr; min-height: 220px; }
    figure > img { grid-column: 1; grid-row: 1 / 3; }
    figure > figcaption { grid-column: 2; grid-row: 1; }
    figure > .figbody { grid-column: 2; grid-row: 2; }
  }
  figure > img { width: 100%; height: 100%; max-height: 520px; object-fit: contain;
    background: #0e1826; display: block; border-right: 1px solid var(--line); }
  @media (max-width: 679px) {
    figure > img { max-height: 280px; border-right: none; border-bottom: 1px solid var(--line); } }
  figcaption { padding: 18px 20px 10px; font-family: 'Inter', sans-serif; font-size: 12.5px;
    color: var(--muted); border-bottom: 1px solid var(--line); }
  figcaption strong { display: block; font-size: 11px; letter-spacing: 1px;
    text-transform: uppercase; color: var(--accent); margin-bottom: 5px; }
  .caption { font-family: 'Lora', serif; font-style: italic; font-size: 13px;
    color: #3a4650; line-height: 1.55; }
  .figbody { padding: 16px 20px 18px; background: var(--soft-teal);
    font-family: 'Inter', sans-serif; font-size: 13.5px; color: #1e3530;
    line-height: 1.65; border-left: 3px solid var(--teal); }
  .figbody p { margin: 0; }
  .figbody::before { content: 'Figura del paper'; display: block; font-size: 10px;
    font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase;
    color: var(--teal); margin-bottom: 7px; }

  .small { color: var(--muted); font-size: 13px; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--paper); }
  ::-webkit-scrollbar-thumb { background: #b0bcc8; border-radius: 3px; }
"""


# ── Parser de metadata ─────────────────────────────────────────────────────────

def extract_metadata(text: str) -> dict:
    """Extrae título, autores, revista/DOI del encabezado markdown."""
    meta = {"title": "", "subtitle": "", "autores": "", "revista": "", "doi": "", "open": ""}

    # Título desde "# Resumen — Titulo"
    m = re.search(r'^#\s+Resumen\s*[—–-]+\s*(.+)$', text, re.MULTILINE)
    if m:
        meta["title"] = m.group(1).strip()

    # Fallback: primer h1
    if not meta["title"]:
        m = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if m:
            meta["title"] = m.group(1).strip()

    # Fallback: línea "Título:"
    if not meta["title"]:
        m = re.search(r'[Tt][ií]tulo\s*:\s*(.+)', text)
        if m:
            meta["title"] = m.group(1).strip()

    # Autores
    m = re.search(r'\*\*Autores\*\*\s*:\s*(.+)', text)
    if not m:
        m = re.search(r'Autores?\s*:\s*(.+)', text)
    if m:
        meta["autores"] = m.group(1).strip()

    # Revista
    m = re.search(r'\*\*Revista\*\*\s*:\s*(.+)', text)
    if not m:
        m = re.search(r'Revista\s*:\s*(.+)', text)
    if m:
        meta["revista"] = m.group(1).strip()

    # DOI (puede estar en la línea de revista o sola)
    m = re.search(r'DOI\s*:\s*([\S]+)', text)
    if not m:
        m = re.search(r'10\.\d{4,}/\S+', text)
    if m:
        meta["doi"] = m.group(1).strip().rstrip(')')

    # arXiv
    if not meta["doi"]:
        m = re.search(r'arXiv\s*:\s*([\S]+)', text)
        if m:
            meta["doi"] = "arXiv:" + m.group(1).strip()

    # Open Access
    m = re.search(r'\*\*Open Access\*\*\s*:\s*(.+)', text)
    if m:
        meta["open"] = m.group(1).strip()

    return meta


def strip_metadata_block(text: str) -> str:
    """Elimina el bloque de encabezado (título + metadatos + primera línea ---) del texto."""
    # Quitar la primera línea # Resumen ...
    text = re.sub(r'^#\s+Resumen\s*[—–-]+\s*.+\n', '', text, flags=re.MULTILINE)
    # Quitar líneas **Key**: value al inicio
    text = re.sub(r'^\*\*(?:Autores|Revista|DOI|Open Access|arXiv)\*\*\s*:.+\n', '', text, flags=re.MULTILINE)
    # Quitar separadores --- sueltos al inicio
    text = re.sub(r'^---\s*\n', '', text, count=2, flags=re.MULTILINE)
    return text.strip()


# ── Figuras ────────────────────────────────────────────────────────────────────

def load_figures(paper_id: str) -> list[dict]:
    path = PAPPERS_DIR / f"{paper_id}_figures" / "figures.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("figures", [])


def find_image_file(paper_id: str, fig: dict) -> Path | None:
    images_dir = PAPPERS_DIR / f"{paper_id}_figures" / "images"
    fig_id = fig["figure_id"]
    # buscar por prefijo fig_id
    for f in sorted(images_dir.glob(f"{fig_id}_*.png")):
        return f
    for f in sorted(images_dir.glob(f"{fig_id}.png")):
        return f
    # usar image_path del json si existe
    if fig.get("image_path"):
        p = PAPPERS_DIR / f"{paper_id}_figures" / fig["image_path"]
        if p.exists():
            return p
    return None


def build_figure_html(paper_id: str, figures: list[dict]) -> str:
    if not figures:
        return "<p class='small'>No se encontraron figuras en este paper.</p>"

    parts = []
    for fig in figures:
        fig_id = fig["figure_id"]
        caption = fig.get("caption", "").strip() or "Sin caption"
        page = fig.get("page")
        page_str = f"pagina {page}" if page else "pagina desconocida"

        img_file = find_image_file(paper_id, fig)
        if img_file:
            rel = f"../pappers/{paper_id}_figures/images/{img_file.name}"
            img_tag = f'<img src="{rel}" alt="{fig_id} — {page_str}" loading="lazy">'
        else:
            img_tag = '<div style="height:200px;background:#1a2332;display:flex;align-items:center;justify-content:center;color:#888;font-size:13px;">imagen no disponible</div>'

        # figbody: caption completo o descripción de posición
        figbody_text = caption if caption != "Sin caption" else f"Figura en {page_str}."

        parts.append(f"""        <figure>
          {img_tag}
          <figcaption>
            <strong>{fig_id.upper()} · {page_str}</strong>
            <p class="caption">{caption}</p>
          </figcaption>
          <div class="figbody"><p>{figbody_text}</p></div>
        </figure>""")

    return '<div class="figure-list">\n' + "\n\n".join(parts) + "\n      </div>"


# ── Conversión markdown → HTML ─────────────────────────────────────────────────

MD = md_lib.Markdown(extensions=["tables", "fenced_code", "nl2br"])


def md_to_html(text: str) -> str:
    MD.reset()
    return MD.convert(text)


def remove_emojis(text: str) -> str:
    return re.sub(
        r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0000FE00-\U0000FE0F]+',
        '', text
    ).strip()


# ── Construcción del HTML completo ─────────────────────────────────────────────

def build_html(paper_id: str) -> str:
    txt_path = PAPPERS_DIR / f"resumen_{paper_id}.txt"
    raw = txt_path.read_text(encoding="utf-8")

    meta    = extract_metadata(raw)
    body_md = strip_metadata_block(raw)
    body_md = remove_emojis(body_md)
    body_html = md_to_html(body_md)

    figures   = load_figures(paper_id)
    figs_html = build_figure_html(paper_id, figures)
    fig_count = len(figures)

    title_safe = meta["title"] or paper_id
    # Subtítulo del header
    subtitle = f"Resumen en español de <strong>{title_safe}</strong>."

    # Metadatos del header
    meta_items = []
    if meta["autores"]:
        meta_items.append(f'<div><strong>Autores</strong>{meta["autores"]}</div>')
    if meta["revista"]:
        meta_items.append(f'<div><strong>Revista</strong>{meta["revista"]}</div>')
    if meta["doi"]:
        doi_val = meta["doi"]
        if doi_val.startswith("10."):
            doi_link = f'<a href="https://doi.org/{doi_val}" target="_blank">{doi_val}</a>'
        elif doi_val.startswith("arXiv:"):
            arxiv_id = doi_val.replace("arXiv:", "")
            doi_link = f'<a href="https://arxiv.org/abs/{arxiv_id}" target="_blank">{doi_val}</a>'
        else:
            doi_link = doi_val
        meta_items.append(f'<div><strong>DOI / arXiv</strong>{doi_link}</div>')
    meta_items.append(f'<div><strong>PDF local</strong><a href="../pappers/{paper_id}.pdf">ver PDF</a></div>')
    meta_html = "\n        ".join(meta_items)

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Resumen — {title_safe}</title>
  <style>{TEMPLATE_CSS}
  </style>
</head>
<body>

<nav class="top-nav">
  <a href="../index.html" class="back">&#8592; Indice</a>
  <span class="nav-title" id="nav-title-text"></span>
  <span class="journal-name">ilovepappers Journal</span>
</nav>
<script>
  document.getElementById('nav-title-text').textContent =
    document.querySelector('h1') ? document.querySelector('h1').textContent.slice(0, 60) : '';
</script>

<header>
  <div class="inner">
    <div class="journal-stripe">ilovepappers Journal &middot; Resumen en Espanol</div>
    <h1>{title_safe}</h1>
    <p class="subtitle">{subtitle}</p>
    <div class="meta">
        {meta_html}
    </div>
  </div>
</header>

<main>

  <section>
    {body_html}
  </section>

  <section>
    <h2>Figuras del Paper ({fig_count})</h2>
    {figs_html}
  </section>

</main>
</body>
</html>"""


# ── CLI ────────────────────────────────────────────────────────────────────────

def find_pending() -> list[str]:
    pending = []
    for txt in sorted(PAPPERS_DIR.glob("resumen_*.txt")):
        paper_id = txt.stem.removeprefix("resumen_")
        if (PAPPERS_DIR / f"{paper_id}_figures").is_dir():
            if not (OUTPUT_DIR / f"{paper_id}_resumen.html").exists():
                pending.append(paper_id)
    return pending


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--paper", default=None, help="Solo este paper_id")
    p.add_argument("--force", action="store_true", help="Regenerar aunque ya exista")
    return p.parse_args()


def main():
    args = parse_args()

    if args.paper:
        papers = [args.paper]
    elif args.force:
        papers = [
            txt.stem.removeprefix("resumen_")
            for txt in sorted(PAPPERS_DIR.glob("resumen_*.txt"))
            if (PAPPERS_DIR / f"{txt.stem.removeprefix('resumen_')}_figures").is_dir()
        ]
    else:
        papers = find_pending()

    if not papers:
        print("No hay papers pendientes.")
        return

    print(f"Procesando {len(papers)} papers...\n")
    ok = fail = 0

    for i, paper_id in enumerate(papers, 1):
        out = OUTPUT_DIR / f"{paper_id}_resumen.html"
        try:
            html = build_html(paper_id)
            out.write_text(html, encoding="utf-8")
            figures = load_figures(paper_id)
            print(f"  [{i:02d}] OK  {out.name}  ({len(figures)} figuras)")
            ok += 1
        except Exception as e:
            print(f"  [{i:02d}] FAIL {paper_id}: {e}")
            fail += 1

    print(f"\nListo. OK: {ok} | FAIL: {fail}")


if __name__ == "__main__":
    main()
