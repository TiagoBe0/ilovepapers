"""
generate_html_resumenes.py
--------------------------
Para cada paper que tenga resumen_*.txt + *_figures/ pero sin HTML en output/,
llama a la Claude API para generar el HTML completo con figuras y template CSS.

Uso:
    ANTHROPIC_API_KEY=sk-ant-... python generate_html_resumenes.py
    ANTHROPIC_API_KEY=sk-ant-... python generate_html_resumenes.py --paper 3DCNN_predicciones_propiedades_atomisticas_Peivaste_2023
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

import anthropic

# ── Rutas ──────────────────────────────────────────────────────────────────────
PAPPERS_DIR = Path(__file__).parent / "pappers"
OUTPUT_DIR  = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL = "claude-sonnet-4-6"
MAX_FIGURES_VISION = 12   # máximo de figuras a enviar al modelo por imagen

# ── CSS del template (copiado de apply_template.py) ───────────────────────────
TEMPLATE_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --paper:      #fafaf8;
    --surface:    #ffffff;
    --panel:      #ffffff;
    --ink:        #18202a;
    --muted:      #5a6472;
    --line:       #d8dde4;
    --accent:     #174a7e;
    --accent-h:   #0d3259;
    --gold:       #b8860b;
    --teal:       #0a6858;
    --soft-blue:  #eef3fb;
    --soft-gold:  #fdf6e3;
    --soft-teal:  #e6f4f1;
    --warn:       #fff8e1;
    --nav-h:      44px;
    --max-w:      960px;
  }

  html { scroll-behavior: smooth; }
  body { font-family: 'Lora', Georgia, serif; font-size: 16px; line-height: 1.75; background: var(--paper); color: var(--ink); }

  .top-nav { position: sticky; top: 0; z-index: 200; height: var(--nav-h); background: var(--accent); display: flex; align-items: center; gap: 12px; padding: 0 20px; box-shadow: 0 2px 8px rgba(0,0,0,.25); }
  .top-nav a.back { color: rgba(255,255,255,.85); text-decoration: none; font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 6px; padding: 5px 12px; border: 1px solid rgba(255,255,255,.3); border-radius: 20px; transition: background .15s; }
  .top-nav a.back:hover { background: rgba(255,255,255,.15); }
  .top-nav .nav-title { color: rgba(255,255,255,.6); font-family: 'Playfair Display', serif; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .top-nav .journal-name { margin-left: auto; color: rgba(255,255,255,.5); font-family: 'Inter', sans-serif; font-size: 11px; font-style: italic; white-space: nowrap; }

  header { background: linear-gradient(160deg, #0d2a4a 0%, #174a7e 60%, #1a5c8a 100%); color: #fff; padding: 52px 28px 44px; border-bottom: 4px solid var(--gold); }
  header .inner { max-width: var(--max-w); margin: 0 auto; }
  .journal-stripe { font-family: 'Inter', sans-serif; font-size: 10px; font-weight: 600; letter-spacing: 2.5px; text-transform: uppercase; color: var(--gold); margin-bottom: 18px; display: flex; align-items: center; gap: 10px; }
  .journal-stripe::after { content: ''; flex: 1; height: 1px; background: rgba(184,134,11,.4); }
  h1 { font-family: 'Playfair Display', serif; font-size: clamp(22px, 4vw, 40px); font-weight: 700; line-height: 1.15; letter-spacing: -.3px; margin-bottom: 16px; }
  .subtitle { font-family: 'Lora', serif; font-style: italic; font-size: 16px; color: rgba(255,255,255,.78); max-width: 820px; margin-bottom: 28px; }
  .meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 10px; font-family: 'Inter', sans-serif; font-size: 12.5px; color: rgba(255,255,255,.8); }
  .meta div { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15); padding: 10px 14px; border-radius: 6px; }
  .meta div strong { color: var(--gold); display: block; margin-bottom: 2px; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
  .meta a { color: rgba(255,255,255,.7); }
  .meta a:hover { color: #fff; }

  main, .inner { max-width: var(--max-w); margin: 0 auto; }
  main { padding: 40px 24px 80px; }
  section { margin-bottom: 48px; }

  h2 { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: var(--accent); margin: 0 0 18px; padding-bottom: 10px; border-bottom: 2px solid var(--line); position: relative; }
  h2::before { content: ''; position: absolute; bottom: -2px; left: 0; width: 48px; height: 2px; background: var(--gold); }
  h3 { font-family: 'Playfair Display', serif; font-size: 17px; color: var(--ink); margin: 0 0 8px; }
  p { margin: 0 0 16px; }
  a { color: var(--teal); }
  a:hover { color: var(--accent); }

  .lead { font-size: 17px; font-style: italic; color: #2a3540; background: var(--soft-blue); border-left: 4px solid var(--accent); padding: 22px 24px; border-radius: 0 8px 8px 0; margin-bottom: 24px; line-height: 1.7; }
  .tag { display: inline-block; margin: 0 6px 8px 0; padding: 4px 11px; border-radius: 20px; background: var(--soft-blue); color: var(--accent); border: 1px solid #c2d2ea; font-family: 'Inter', sans-serif; font-size: 11.5px; font-weight: 600; letter-spacing: .2px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 18px 0; }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 18px 20px; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
  .card h3 { color: var(--accent); font-size: 15px; margin-bottom: 8px; }
  .important { background: var(--soft-gold); border-left: 4px solid var(--gold); padding: 18px 22px; border-radius: 0 8px 8px 0; }
  @media (min-width: 720px) { .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; } }

  table { width: 100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--line); margin: 20px 0; font-family: 'Inter', sans-serif; font-size: 13.5px; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.06); }
  th, td { border: 1px solid var(--line); padding: 11px 14px; text-align: left; vertical-align: top; }
  th { background: var(--accent); color: #fff; font-weight: 600; font-size: 12px; letter-spacing: .4px; text-transform: uppercase; }
  tr:nth-child(even) td { background: #f7f9fc; }

  .figure-list { display: flex; flex-direction: column; gap: 32px; }
  figure { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,.07); transition: box-shadow .2s; }
  figure:hover { box-shadow: 0 6px 24px rgba(0,0,0,.12); }
  @media (min-width: 680px) {
    figure { display: grid; grid-template-columns: 56% 44%; grid-template-rows: auto 1fr; min-height: 220px; }
    figure > img { grid-column: 1; grid-row: 1 / 3; }
    figure > figcaption { grid-column: 2; grid-row: 1; }
    figure > .figbody { grid-column: 2; grid-row: 2; }
  }
  figure > img { width: 100%; height: 100%; max-height: 520px; object-fit: contain; background: #0e1826; display: block; border-right: 1px solid var(--line); }
  @media (max-width: 679px) { figure > img { max-height: 280px; border-right: none; border-bottom: 1px solid var(--line); } }
  figcaption { padding: 18px 20px 10px; font-family: 'Inter', sans-serif; font-size: 12.5px; color: var(--muted); border-bottom: 1px solid var(--line); }
  figcaption strong { display: block; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--accent); margin-bottom: 5px; }
  .caption { font-family: 'Lora', serif; font-style: italic; font-size: 13px; color: #3a4650; line-height: 1.55; }
  .figbody { padding: 16px 20px 18px; background: var(--soft-teal); font-family: 'Inter', sans-serif; font-size: 13.5px; color: #1e3530; line-height: 1.65; border-left: 3px solid var(--teal); }
  .figbody p { margin: 0; }
  .figbody::before { content: '↳ Interpretación'; display: block; font-size: 10px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; color: var(--teal); margin-bottom: 7px; }

  .small { color: var(--muted); font-size: 13px; }
  .refs li { margin-bottom: 10px; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--paper); }
  ::-webkit-scrollbar-thumb { background: #b0bcc8; border-radius: 3px; }
"""

NAV_BAR = '''<nav class="top-nav">
  <a href="../index.html" class="back">← Índice</a>
  <span class="nav-title" id="nav-title-text"></span>
  <span class="journal-name">ilovepappers Journal</span>
</nav>
<script>
  document.getElementById('nav-title-text').textContent =
    document.querySelector('h1') ? document.querySelector('h1').textContent.slice(0, 60) : '';
</script>'''


# ── Helpers ────────────────────────────────────────────────────────────────────

def find_papers_needing_html():
    """Retorna lista de paper_ids que tienen resumen_*.txt + *_figures/ pero sin HTML."""
    needed = []
    for txt in sorted(PAPPERS_DIR.glob("resumen_*.txt")):
        paper_id = txt.stem.removeprefix("resumen_")
        figures_dir = PAPPERS_DIR / f"{paper_id}_figures"
        out_html = OUTPUT_DIR / f"{paper_id}_resumen.html"
        if figures_dir.is_dir() and not out_html.exists():
            needed.append(paper_id)
    return needed


def load_figures_json(paper_id: str) -> list[dict]:
    path = PAPPERS_DIR / f"{paper_id}_figures" / "figures.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("figures", [])


def load_image_b64(paper_id: str, fig: dict) -> str | None:
    images_dir = PAPPERS_DIR / f"{paper_id}_figures" / "images"
    # buscar por figure_id prefix
    for img_file in sorted(images_dir.glob(f"{fig['figure_id']}_*.png")):
        return base64.b64encode(img_file.read_bytes()).decode()
    # fallback: nombre exacto
    for img_file in sorted(images_dir.glob(f"{fig['figure_id']}.png")):
        return base64.b64encode(img_file.read_bytes()).decode()
    return None


def image_rel_path(paper_id: str, fig: dict) -> str:
    images_dir = PAPPERS_DIR / f"{paper_id}_figures" / "images"
    for img_file in sorted(images_dir.glob(f"{fig['figure_id']}_*.png")):
        return f"../pappers/{paper_id}_figures/images/{img_file.name}"
    for img_file in sorted(images_dir.glob(f"{fig['figure_id']}.png")):
        return f"../pappers/{paper_id}_figures/images/{img_file.name}"
    return ""


# ── Llamadas a la API ──────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sos un divulgador científico de élite especializado en materiales, física computacional y machine learning.
Tu tarea es generar un resumen HTML completo y detallado de un paper científico en español.

REGLAS ESTRICTAS:
1. Devolvé ÚNICAMENTE el HTML completo. Sin texto previo, sin backticks, sin markdown alrededor.
2. El HTML debe comenzar con <!doctype html> y terminar con </html>.
3. No uses acentos ni caracteres especiales en los atributos HTML (alt, title), pero SÍ en el texto visible.
4. No uses emojis en el HTML.
5. Las rutas de imágenes son relativas: ya se te proveen, úsalas exactamente.
6. Cada figura debe tener: img con src, figcaption con caption original, div.figbody con análisis en español de 3-5 oraciones.
7. El análisis de cada figura debe explicar QUÉ muestra, POR QUÉ importa y CÓMO se conecta con el argumento central del paper.

ESTRUCTURA HTML requerida (usa exactamente estas clases CSS):
- <nav class="top-nav"> con el botón volver y título
- <header> con <div class="inner">, <div class="journal-stripe">, <h1>, <p class="subtitle">, <div class="meta">
- <main> con secciones: Resumen ejecutivo (con <p class="lead"> y tags), Ideas clave (con .grid .card), [secciones del contenido], Figuras explicadas (con .figure-list)
- Podés agregar tablas, .important, .two-col según el contenido del paper
"""


def build_figure_content(paper_id: str, figures: list[dict]) -> list:
    """Construye el bloque de contenido con imágenes para el mensaje del usuario."""
    content = []
    figs_to_send = figures[:MAX_FIGURES_VISION]

    if figs_to_send:
        content.append({"type": "text", "text": f"\n\n=== FIGURAS DEL PAPER ({len(figures)} total, enviando {len(figs_to_send)}) ===\n"})

    for i, fig in enumerate(figs_to_send):
        caption = fig.get("caption", "") or "Sin caption"
        page = fig.get("page", "?")
        fig_id = fig["figure_id"]
        rel_path = image_rel_path(paper_id, fig)

        content.append({"type": "text", "text": f"\nFIGURA {i+1} — {fig_id} — Página {page}\nCaption: {caption}\nRuta imagen: {rel_path}\n"})

        img_b64 = load_image_b64(paper_id, fig)
        if img_b64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": img_b64}
            })
        else:
            content.append({"type": "text", "text": "[imagen no disponible]\n"})

    # Figuras restantes sin imagen
    if len(figures) > MAX_FIGURES_VISION:
        extra = figures[MAX_FIGURES_VISION:]
        content.append({"type": "text", "text": f"\n=== FIGURAS ADICIONALES (sin imagen, solo caption) ===\n"})
        for fig in extra:
            caption = fig.get("caption", "") or "Sin caption"
            page = fig.get("page", "?")
            rel_path = image_rel_path(paper_id, fig)
            content.append({"type": "text", "text": f"- {fig['figure_id']} (p.{page}): {caption}\n  Ruta: {rel_path}\n"})

    return content


def generate_html(client: anthropic.Anthropic, paper_id: str) -> str:
    txt_path = PAPPERS_DIR / f"resumen_{paper_id}.txt"
    resumen_md = txt_path.read_text(encoding="utf-8")
    figures = load_figures_json(paper_id)

    user_content = [
        {
            "type": "text",
            "text": f"""Generá el HTML completo para el paper con ID: {paper_id}

=== RESUMEN EN MARKDOWN (fuente de contenido) ===
{resumen_md}

=== CSS DEL TEMPLATE (incluirlo en <style> dentro de <head>) ===
{TEMPLATE_CSS}

=== NAVBAR HTML (incluirlo justo antes de <header>) ===
{NAV_BAR}

Instrucciones adicionales:
- El <title> debe ser el título corto del paper.
- En .meta incluir: Autores, Revista/DOI, PDF local (ruta: ../pappers/{paper_id}.pdf).
- Usar el contenido del markdown para las secciones principales.
- La sección "Figuras explicadas" va al final de <main>, antes del cierre.
- Para cada figura: usá el src de la ruta provista, analizá la imagen visualmente y escribí el div.figbody con interpretación técnica detallada en español sin acentos en atributos HTML.
"""
        }
    ]

    user_content.extend(build_figure_content(paper_id, figures))

    print(f"  [API] Llamando a Claude ({len(figures)} figuras)...")

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )

    html = response.content[0].text.strip()

    # Limpiar si Claude envolvió en backticks
    if html.startswith("```"):
        lines = html.split("\n")
        html = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    return html


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Genera HTMLs de resúmenes con figuras.")
    p.add_argument("--paper", default=None, help="Procesar solo este paper_id")
    p.add_argument("--force", action="store_true", help="Regenerar aunque ya exista el HTML")
    return p.parse_args()


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] Falta ANTHROPIC_API_KEY", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    args = parse_args()

    if args.paper:
        papers = [args.paper]
    else:
        papers = find_papers_needing_html()
        if args.force:
            papers = [
                txt.stem.removeprefix("resumen_")
                for txt in sorted(PAPPERS_DIR.glob("resumen_*.txt"))
                if (PAPPERS_DIR / f"{txt.stem.removeprefix('resumen_')}_figures").is_dir()
            ]

    if not papers:
        print("[OK] No hay papers pendientes.")
        return

    print(f"\nPapers a procesar: {len(papers)}\n")

    ok = 0
    fail = 0

    for i, paper_id in enumerate(papers, 1):
        out_path = OUTPUT_DIR / f"{paper_id}_resumen.html"
        print(f"[{i}/{len(papers)}] {paper_id}")

        try:
            html = generate_html(client, paper_id)
            out_path.write_text(html, encoding="utf-8")
            print(f"  [OK] → {out_path.name}")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            fail += 1

    print(f"\nListo. OK: {ok} | FAIL: {fail}")


if __name__ == "__main__":
    main()
