"""
apply_template.py
Reemplaza el bloque <style> de cada resumen HTML en output/
con la plantilla unificada de estilo revista científica.
También inyecta una barra de navegación de vuelta al índice.
"""
import re
from pathlib import Path

OUTPUT_DIR = Path("output")

# ── Nueva CSS unificada ────────────────────────────────────────────────────────
NEW_STYLE = """
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,400&family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');

  /* ── Reset & base ──────────────────────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --paper:      #fafaf8;
    --surface:    #ffffff;
    --panel:      #ffffff;
    --ink:        #18202a;
    --muted:      #5a6472;
    --line:       #d8dde4;
    --accent:     #174a7e;    /* azul journal */
    --accent-h:   #0d3259;
    --gold:       #b8860b;    /* acento dorado */
    --teal:       #0a6858;
    --soft-blue:  #eef3fb;
    --soft-gold:  #fdf6e3;
    --soft-teal:  #e6f4f1;
    --warn:       #fff8e1;
    --nav-h:      44px;
    --max-w:      960px;
  }

  html { scroll-behavior: smooth; }

  body {
    font-family: 'Lora', Georgia, serif;
    font-size: 16px;
    line-height: 1.75;
    background: var(--paper);
    color: var(--ink);
  }

  /* ── Nav bar ────────────────────────────────────────────────── */
  .top-nav {
    position: sticky; top: 0; z-index: 200;
    height: var(--nav-h);
    background: var(--accent);
    display: flex; align-items: center; gap: 12px;
    padding: 0 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,.25);
  }
  .top-nav a.back {
    color: rgba(255,255,255,.85);
    text-decoration: none;
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 500;
    display: flex; align-items: center; gap: 6px;
    padding: 5px 12px;
    border: 1px solid rgba(255,255,255,.3);
    border-radius: 20px;
    transition: background .15s;
  }
  .top-nav a.back:hover { background: rgba(255,255,255,.15); }
  .top-nav .nav-title {
    color: rgba(255,255,255,.6);
    font-family: 'Playfair Display', serif;
    font-size: 13px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .top-nav .journal-name {
    margin-left: auto;
    color: rgba(255,255,255,.5);
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-style: italic;
    white-space: nowrap;
  }

  /* ── Header / masthead ──────────────────────────────────────── */
  header {
    background: linear-gradient(160deg, #0d2a4a 0%, #174a7e 60%, #1a5c8a 100%);
    color: #fff;
    padding: 52px 28px 44px;
    border-bottom: 4px solid var(--gold);
  }
  header .inner {
    max-width: var(--max-w);
    margin: 0 auto;
  }
  .journal-stripe {
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 18px;
    display: flex; align-items: center; gap: 10px;
  }
  .journal-stripe::after {
    content: ''; flex: 1; height: 1px; background: rgba(184,134,11,.4);
  }
  h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(22px, 4vw, 40px);
    font-weight: 700;
    line-height: 1.15;
    letter-spacing: -.3px;
    margin-bottom: 16px;
  }
  .subtitle {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 16px;
    color: rgba(255,255,255,.78);
    max-width: 820px;
    margin-bottom: 28px;
  }
  .meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 12.5px;
    color: rgba(255,255,255,.8);
  }
  .meta div {
    background: rgba(255,255,255,.08);
    border: 1px solid rgba(255,255,255,.15);
    padding: 10px 14px;
    border-radius: 6px;
  }
  .meta div strong { color: var(--gold); display: block; margin-bottom: 2px; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }
  .meta a { color: rgba(255,255,255,.7); }
  .meta a:hover { color: #fff; }

  /* ── Main layout ────────────────────────────────────────────── */
  main, .inner {
    max-width: var(--max-w);
    margin: 0 auto;
  }
  main { padding: 40px 24px 80px; }

  /* ── Sections ───────────────────────────────────────────────── */
  section { margin-bottom: 48px; }

  h2 {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--accent);
    margin: 0 0 18px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--line);
    position: relative;
  }
  h2::before {
    content: '';
    position: absolute; bottom: -2px; left: 0;
    width: 48px; height: 2px;
    background: var(--gold);
  }
  h3 {
    font-family: 'Playfair Display', serif;
    font-size: 17px;
    color: var(--ink);
    margin: 0 0 8px;
  }
  p { margin: 0 0 16px; }
  a { color: var(--teal); }
  a:hover { color: var(--accent); }

  /* ── Lead / abstract ────────────────────────────────────────── */
  .lead {
    font-size: 17px;
    font-style: italic;
    color: #2a3540;
    background: var(--soft-blue);
    border-left: 4px solid var(--accent);
    padding: 22px 24px;
    border-radius: 0 8px 8px 0;
    margin-bottom: 24px;
    line-height: 1.7;
  }

  /* ── Tags ───────────────────────────────────────────────────── */
  .tag {
    display: inline-block;
    margin: 0 6px 8px 0;
    padding: 4px 11px;
    border-radius: 20px;
    background: var(--soft-blue);
    color: var(--accent);
    border: 1px solid #c2d2ea;
    font-family: 'Inter', sans-serif;
    font-size: 11.5px;
    font-weight: 600;
    letter-spacing: .2px;
  }

  /* ── Cards & grids ──────────────────────────────────────────── */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin: 18px 0;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
  }
  .card h3 { color: var(--accent); font-size: 15px; margin-bottom: 8px; }
  .important {
    background: var(--soft-gold);
    border-left: 4px solid var(--gold);
    padding: 18px 22px;
    border-radius: 0 8px 8px 0;
  }
  @media (min-width: 720px) {
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }
  }

  /* ── Tables ─────────────────────────────────────────────────── */
  table {
    width: 100%;
    border-collapse: collapse;
    background: var(--surface);
    border: 1px solid var(--line);
    margin: 20px 0;
    font-family: 'Inter', sans-serif;
    font-size: 13.5px;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
  }
  th, td {
    border: 1px solid var(--line);
    padding: 11px 14px;
    text-align: left;
    vertical-align: top;
  }
  th {
    background: var(--accent);
    color: #fff;
    font-weight: 600;
    font-size: 12px;
    letter-spacing: .4px;
    text-transform: uppercase;
  }
  tr:nth-child(even) td { background: #f7f9fc; }

  /* ── Figure list wrapper ────────────────────────────────────── */
  .figure-list {
    display: flex;
    flex-direction: column;
    gap: 32px;
  }

  /* ── Figure card ────────────────────────────────────────────── */
  figure {
    margin: 0;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
    transition: box-shadow .2s;
  }
  figure:hover { box-shadow: 0 6px 24px rgba(0,0,0,.12); }

  /* Two-panel layout on wide screens */
  @media (min-width: 680px) {
    figure {
      display: grid;
      grid-template-columns: 56% 44%;
      grid-template-rows: auto 1fr;
      min-height: 220px;
    }
    figure > img {
      grid-column: 1;
      grid-row: 1 / 3;
    }
    figure > figcaption {
      grid-column: 2;
      grid-row: 1;
    }
    figure > .figbody {
      grid-column: 2;
      grid-row: 2;
    }
  }

  figure > img {
    width: 100%;
    height: 100%;
    max-height: 520px;
    object-fit: contain;
    background: #0e1826;
    display: block;
    border-right: 1px solid var(--line);
  }

  /* On mobile: image full width on top */
  @media (max-width: 679px) {
    figure > img {
      max-height: 280px;
      border-right: none;
      border-bottom: 1px solid var(--line);
    }
  }

  figcaption {
    padding: 18px 20px 10px;
    font-family: 'Inter', sans-serif;
    font-size: 12.5px;
    color: var(--muted);
    border-bottom: 1px solid var(--line);
  }
  figcaption strong {
    display: block;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 5px;
  }
  .caption {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 13px;
    color: #3a4650;
    line-height: 1.55;
  }

  .figbody {
    padding: 16px 20px 18px;
    background: var(--soft-teal);
    font-family: 'Inter', sans-serif;
    font-size: 13.5px;
    color: #1e3530;
    line-height: 1.65;
    border-left: 3px solid var(--teal);
  }
  .figbody p { margin: 0; }
  .figbody::before {
    content: '↳ Interpretación';
    display: block;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--teal);
    margin-bottom: 7px;
  }

  .small { color: var(--muted); font-size: 13px; }
  .refs li { margin-bottom: 10px; }

  /* ── Scrollbar ──────────────────────────────────────────────── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--paper); }
  ::-webkit-scrollbar-thumb { background: #b0bcc8; border-radius: 3px; }
"""

# ── Barra de navegación HTML ───────────────────────────────────────────────────
NAV_BAR = '''<nav class="top-nav">
  <a href="../index.html" class="back">← Índice</a>
  <span class="nav-title" id="nav-title-text"></span>
  <span class="journal-name">ilovepappers Journal</span>
</nav>
<script>
  document.getElementById('nav-title-text').textContent =
    document.querySelector('h1') ? document.querySelector('h1').textContent.slice(0, 60) : '';
</script>
'''

# ── Stripe de revista en el header ────────────────────────────────────────────
JOURNAL_STRIPE = '<div class="journal-stripe">ilovepappers Journal · Resumen en Español</div>\n      '


def apply_template(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8")

    # 1. Reemplazar bloque <style>...</style>
    text = re.sub(
        r'<style>.*?</style>',
        f'<style>{NEW_STYLE}\n  </style>',
        text,
        flags=re.DOTALL,
    )

    # 2. Insertar barra de navegación justo antes de <header>
    if '<nav class="top-nav">' not in text:
        text = text.replace('<header>', NAV_BAR + '\n<header>', 1)

    # 3. Insertar journal stripe dentro del header > .inner, antes del h1
    if 'journal-stripe' not in text:
        text = re.sub(
            r'(<div class="inner">\s*\n?\s*<h1)',
            lambda m: m.group(1).replace(
                '<h1', JOURNAL_STRIPE + '<h1'
            ),
            text,
        )

    html_path.write_text(text, encoding="utf-8")
    print(f"  ✓  {html_path.name}")


def main():
    targets = [p for p in OUTPUT_DIR.glob("*.html")
               if not p.name.startswith("index")]
    if not targets:
        print("[!] No se encontraron HTMLs en output/")
        return
    print(f"Aplicando plantilla a {len(targets)} archivos...\n")
    for p in sorted(targets):
        apply_template(p)
    print("\nListo.")


if __name__ == "__main__":
    main()
