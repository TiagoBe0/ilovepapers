# -*- coding: utf-8 -*-
"""
build_resumen_general.py
Agrupa todos los resúmenes web (parseados desde index.html) por áreas temáticas
relacionadas / que se citan entre sí, y genera `resumen_general.html`:
una síntesis general por tópico + las figuras estrella de cada paper con su caption.
"""
import json, re, html as _html
from pathlib import Path

cards = json.load(open("/tmp/cards.json", encoding="utf-8"))

# ── Títulos limpios para tarjetas cuyo título salió genérico ────────────────
TITLE_OVERRIDE = {
    15: "CVAE para detección de defectos en imágenes STEM",
    16: "CarNet: redes neuronales para tensores cartesianos",
    19: "Predicción multitarea de HEAs con incertidumbre (Deep Gaussian Processes)",
    20: "DJINN: inicialización de redes neuronales con árboles de decisión",
    24: "Cascadas de irradiación en CuNi mediante dinámica molecular",
    25: "MD + kMC: efecto de la tasa de dosis en tungsteno",
    28: "OE-BERT: pre-entrenamiento de dominio (DAPT) para optoelectrónica",
    29: "OMC25: dataset de cristales moleculares orgánicos (Meta)",
    33: "Review: Deep Learning para la ciencia de materiales",
    35: "TGS in situ para el seguimiento de vacancias (MIT, 2026)",
    38: "U-Net para la nucleación de voids en tantalio",
}

# ── Asignación de cada paper (índice) a un tópico ───────────────────────────
TOPIC_OF = {
    # 1 · Daño por radiación y evolución de defectos
    2: "rad", 1: "rad", 24: "rad", 25: "rad", 3: "rad", 27: "rad", 40: "rad",
    # 2 · ML para detección y caracterización de defectos
    11: "defect", 21: "defect", 15: "defect", 38: "defect", 35: "defect", 9: "defect",
    # 3 · GNN y predicción de propiedades de materiales
    13: "gnn", 0: "gnn", 16: "gnn", 19: "gnn", 14: "gnn", 23: "gnn", 33: "gnn", 28: "gnn",
    # 4 · Deep learning sobre nubes de puntos y datos 3D
    32: "pc", 31: "pc", 18: "pc", 39: "pc", 30: "pc", 37: "pc",
    # 5 · Potenciales interatómicos ML y dinámica molecular
    26: "mlip", 41: "mlip", 36: "mlip", 8: "mlip", 29: "mlip", 10: "mlip", 34: "mlip",
    # 6 · Fundamentos de IA / aprendizaje profundo
    12: "ai", 20: "ai", 5: "ai",
    # 7 · Visualización y software científico
    7: "soft", 17: "soft",
    # 8 · Fundamentos y temas transversales
    6: "misc", 22: "misc", 4: "misc",
}

# ── Definición de tópicos: orden, nº, nombre, color, síntesis ───────────────
TOPICS = [
    ("rad", "01", "Daño por radiación y evolución de defectos", "#b5462e",
     """Núcleo de <strong>materiales nucleares y de fusión</strong>. El trabajo de
     <em>Nordlund et al. (2018)</em> sobre el daño primario funciona como base conceptual
     —la cascada de colisión, la función de daño y la zona de alta entropía— y es la
     referencia que articula al resto: la irradiación de la HEA FeCoNiCrCu (Zhanguang),
     las cascadas en CuNi (Wei 2025), el acople MD+kMC dependiente de la tasa de dosis
     en tungsteno (Boleininger 2025) y la teoría de materiales de fusión (Reali 2026).
     La nucleación de <em>voids</em> (Hemani 2014) y la difusión de vacancias en HEAs
     (Reimer 2025) cierran el ciclo defecto→migración→propiedad. Estos papers comparten
     el método de dinámica molecular de cascadas y alimentan directamente al Tema 02,
     donde el ML aprende a detectar los defectos que aquí se generan."""),

    ("defect", "02", "ML para detección y caracterización de defectos", "#c77d2e",
     """Aquí el aprendizaje automático se aplica sobre las estructuras dañadas del
     Tema 01 para <strong>encontrar, clasificar y cuantificar defectos</strong>.
     Pipelines no supervisados con <em>autoencoders sobre descriptores SOAP</em>
     (Del Fré 2025) y <em>fingerprints</em> de defectos (FaVAD, von Toussaint),
     un <em>CVAE</em> sobre imágenes STEM (Ayyubi 2026), <em>U-Net</em> para nuclear
     voids en tantalio (Anantharanga 2025) y TGS in situ (Botica MIT 2026). El
     3D-CNN de Peivaste (2023) predice propiedades de material perfecto y defectuoso.
     Toman descriptores estructurales del Tema 05 (SOAP, parámetros de orden) y
     arquitecturas convolucionales/voxel del Tema 04."""),

    ("gnn", "03", "Redes de grafos y predicción de propiedades", "#1a4a6e",
     """La familia de <strong>GNN para materiales</strong> nace con
     <em>CGCNN (Xie &amp; Grossman 2018)</em>, que representa el cristal como grafo y
     se cita en casi todo lo posterior: el framework de Linton (2026) que combina
     CHGNet + CGCNN para evitar la DFT en vacancias de HEAs, CarNet para tensores
     cartesianos (Chen 2025), los procesos gaussianos profundos multitarea (Alvi 2025),
     los 3D-CNN para constantes elásticas (Zorkaltsev 2025) y la teoría de grafos en MD
     de sílice (Bougueroua/Gaigeot 2025). OE-BERT extiende el paradigma a transformers
     en optoelectrónica, y el review de Choudhary (2022) mapea todo el campo. Apoya
     directamente al Tema 01 (predice E<sub>vf</sub> y difusión) sustituyendo cálculos DFT."""),

    ("pc", "04", "Deep learning sobre nubes de puntos y datos 3D", "#2e7d9e",
     """Linaje canónico de la <strong>visión geométrica 3D</strong>, con una cadena de
     citación nítida: <em>PointNet (Qi 2017)</em> → <em>PointNet++ (Qi 2017)</em> →
     <em>DGCNN/EdgeConv (Wang 2020)</em>, junto a la vía basada en vóxeles de
     <em>VoxelNet (Zhou 2017)</em>, el dataset de anotación de regiones de Yi (PartNet)
     y el framework reproducible <em>Torch-Points3D</em> (Chaton 2020) que los integra.
     Son las arquitecturas fundacionales que el Tema 02 reutiliza para procesar
     estructuras atómicas como nubes de puntos o rejillas de vóxeles."""),

    ("mlip", "05", "Potenciales interatómicos ML y dinámica molecular", "#3f7d5a",
     """Donde se construyen y explotan los <strong>potenciales interatómicos
     aprendidos (MLIP)</strong> y los descriptores estructurales que alimentan al resto.
     Desarrollo de MLIP para HfO₂ ferroeléctrico (Kankanamalage 2026), el potencial
     de neuroevolución (NEP) para conductividad térmica de 16 metales (Cao), el puente
     atomístico↔continuo del transporte térmico (Ugwumadu 2026, ligado a sptc-ai),
     el dataset OMC25 de cristales moleculares (Meta 2025) y la descomposición de fase
     por ablación láser (Sun 2025). El clásico de <em>Steinhardt (1983)</em> aporta los
     parámetros de orden orientacional que el Tema 02 usa como descriptores de defectos."""),

    ("ai", "06", "Fundamentos de IA y aprendizaje profundo", "#5b4b8a",
     """Las piezas <strong>fundacionales y transversales de IA</strong>: el artículo
     seminal de <em>retropropagación (Rumelhart, Hinton &amp; Williams 1986)</em> que
     habilita todo lo demás, DJINN (Humbird 2018) que inicializa redes a partir de
     árboles de decisión, y un survey actual sobre LLMs para generación de código
     (Jiang 2026). Es la base metodológica que sostiene los Temas 02, 03 y 04."""),

    ("soft", "07", "Visualización y software científico", "#7a6a3a",
     """Herramientas para <strong>explorar y diseminar datos atomísticos</strong>.
     Dos artículos sobre <em>Chemiscope</em> (el de JOSS y el de Ceriotti/Chorna 2026)
     cubren la visualización interactiva de estructuras y descriptores. Se conectan con
     Torch-Points3D (Tema 04) y FaVAD (Tema 02) como capa de infraestructura/visualización
     común a todo el ecosistema."""),

    ("misc", "08", "Fundamentos de materiales y temas transversales", "#6b6b6b",
     """Material de contexto y casos interdisciplinarios: el texto de divulgación
     <em>«Átomos en movimiento»</em> (introducción a la ciencia de materiales), el estudio
     de fotocatalizadores alternativos al TiO₂ (Hernández 2009) y un trabajo de
     entomología sobre bioinsecticidas en colza (Tonks 2026). No comparten método con
     los clusters anteriores pero completan la biblioteca."""),
]

def esc(s): return _html.escape(s or "", quote=True)

def fig_gallery(p):
    if not p["figs"]:
        return '<div class="nofig">— sin figuras extraídas —</div>'
    items = []
    for f in p["figs"]:
        items.append(
            f'<figure class="rg-fig">'
            f'<img src="{esc(f["src"])}" loading="lazy" alt="">'
            f'<figcaption>{esc(f["caption"])}</figcaption>'
            f'</figure>'
        )
    return '<div class="rg-gallery">' + "".join(items) + "</div>"

def paper_block(i):
    p = cards[i]
    title = TITLE_OVERRIDE.get(i, p["title"])
    year = p["year"] if p["year"] else "—"
    tags = " ".join(f'<span class="rg-tag">{esc(t)}</span>' for t in p["tags"].split())
    actions = []
    if p["resumen"]:
        actions.append(f'<a href="{esc(p["resumen"])}" class="rg-btn primary">Resumen</a>')
    if p["pdf"]:
        actions.append(f'<a href="{esc(p["pdf"])}" class="rg-btn">PDF</a>')
    return f"""
    <article class="rg-paper">
      <div class="rg-paper-head">
        <span class="rg-year">{esc(year)}</span>
        <h3>{esc(title)}</h3>
      </div>
      <div class="rg-authors">{esc(p["authors"])}</div>
      <div class="rg-tags">{tags}</div>
      {fig_gallery(p)}
      <div class="rg-actions">{"".join(actions)}</div>
    </article>"""

# ── Construcción de secciones ───────────────────────────────────────────────
sections = []
toc = []
for key, num, name, color, synth in TOPICS:
    idxs = [i for i, k in TOPIC_OF.items() if k == key]
    idxs.sort(key=lambda i: (cards[i]["year"] if cards[i]["year"].isdigit() else "9999"))
    papers_html = "".join(paper_block(i) for i in idxs)
    toc.append(
        f'<a class="toc-item" href="#t-{key}" style="--c:{color}">'
        f'<span class="toc-num">{num}</span>'
        f'<span class="toc-name">{esc(name)}</span>'
        f'<span class="toc-count">{len(idxs)}</span></a>'
    )
    sections.append(f"""
  <section class="rg-section" id="t-{key}" style="--c:{color}">
    <div class="rg-sec-head">
      <span class="rg-sec-num">{num}</span>
      <h2>{esc(name)}</h2>
      <span class="rg-sec-count">{len(idxs)} papers</span>
    </div>
    <p class="rg-synth">{synth}</p>
    <div class="rg-papers">{papers_html}</div>
  </section>""")

total = sum(1 for _ in TOPIC_OF)

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ilovepappers — Resumen general por tópicos</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{--bg:#f4f3ef;--surface:#fff;--border:#e2dfd8;--accent:#1a4a6e;--text:#1c1c1e;--muted:#6b6b6b;--shadow:0 2px 8px rgba(0,0,0,.08)}}
  body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.55}}
  header{{position:sticky;top:0;z-index:100;background:var(--accent);display:flex;align-items:center;gap:16px;padding:0 24px;height:54px;box-shadow:0 1px 6px rgba(0,0,0,.25)}}
  header h1{{font-family:'Playfair Display',serif;font-size:19px;color:#fff}}
  header .meta{{color:rgba(255,255,255,.72);font-size:12px}}
  header a.home{{margin-left:auto;color:#fff;text-decoration:none;font-size:12px;border:1px solid rgba(255,255,255,.35);padding:5px 12px;border-radius:20px}}
  header a.home:hover{{background:rgba(255,255,255,.15)}}
  .wrap{{max-width:1180px;margin:0 auto;padding:28px 24px 80px}}
  .intro{{font-family:'Playfair Display',serif;font-size:26px;margin-bottom:6px}}
  .intro-sub{{color:var(--muted);margin-bottom:26px;max-width:760px}}
  /* TOC */
  .toc{{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px;margin-bottom:42px}}
  .toc-item{{display:flex;align-items:center;gap:10px;background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--c);border-radius:8px;padding:11px 14px;text-decoration:none;color:var(--text);box-shadow:var(--shadow);transition:transform .12s}}
  .toc-item:hover{{transform:translateY(-2px)}}
  .toc-num{{font-family:'Playfair Display',serif;font-weight:700;color:var(--c);font-size:17px}}
  .toc-name{{flex:1;font-weight:500;font-size:13px}}
  .toc-count{{background:var(--c);color:#fff;border-radius:20px;font-size:11px;padding:2px 9px}}
  /* Section */
  .rg-section{{margin-bottom:54px;scroll-margin-top:70px}}
  .rg-sec-head{{display:flex;align-items:baseline;gap:14px;border-bottom:3px solid var(--c);padding-bottom:8px;margin-bottom:14px}}
  .rg-sec-num{{font-family:'Playfair Display',serif;font-weight:700;font-size:30px;color:var(--c)}}
  .rg-sec-head h2{{font-family:'Playfair Display',serif;font-size:23px;flex:1}}
  .rg-sec-count{{color:var(--muted);font-size:12px;white-space:nowrap}}
  .rg-synth{{background:var(--surface);border:1px solid var(--border);border-left:4px solid var(--c);border-radius:8px;padding:14px 18px;margin-bottom:22px;box-shadow:var(--shadow)}}
  .rg-synth em{{color:var(--c);font-style:italic}}
  /* Papers */
  .rg-papers{{display:grid;grid-template-columns:1fr;gap:18px}}
  .rg-paper{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px 18px;box-shadow:var(--shadow)}}
  .rg-paper-head{{display:flex;align-items:baseline;gap:10px}}
  .rg-year{{font-size:11px;font-weight:600;color:#fff;background:var(--c);border-radius:5px;padding:2px 8px;white-space:nowrap}}
  .rg-paper-head h3{{font-size:15.5px;font-weight:600}}
  .rg-authors{{color:var(--muted);font-size:12.5px;margin:3px 0 8px}}
  .rg-tags{{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:12px}}
  .rg-tag{{font-size:10.5px;background:#eef3f6;color:var(--accent);border-radius:5px;padding:2px 8px}}
  .rg-gallery{{display:flex;gap:12px;overflow-x:auto;padding-bottom:8px}}
  .rg-fig{{flex:0 0 230px;display:flex;flex-direction:column;background:#faf9f6;border:1px solid var(--border);border-radius:8px;overflow:hidden}}
  .rg-fig img{{width:100%;height:150px;object-fit:contain;background:#fff;border-bottom:1px solid var(--border)}}
  .rg-fig figcaption{{font-size:11px;color:#4a4a4a;padding:8px 10px;line-height:1.4}}
  .nofig{{color:var(--muted);font-size:12px;font-style:italic;padding:8px 0}}
  .rg-actions{{display:flex;gap:8px;margin-top:12px}}
  .rg-btn{{font-size:12px;text-decoration:none;border:1px solid var(--border);border-radius:6px;padding:5px 14px;color:var(--text);background:#fff}}
  .rg-btn.primary{{background:var(--c);color:#fff;border-color:var(--c)}}
  .rg-btn:hover{{opacity:.88}}
  footer{{text-align:center;color:var(--muted);font-size:12px;padding:30px 0}}
  @media(min-width:860px){{.rg-papers{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h1>ilovepappers · Resumen general por tópicos</h1>
  <span class="meta">{total} papers · 8 áreas temáticas</span>
  <a class="home" href="index.html">← Biblioteca</a>
</header>
<div class="wrap">
  <div class="intro">Mapa temático de la biblioteca</div>
  <p class="intro-sub">Todos los resúmenes agrupados por áreas relacionadas y por líneas de
  citación. Cada tópico abre con una síntesis general y reúne las figuras estrella de cada
  paper con su caption. Las flechas entre temas indican qué cluster alimenta a cuál.</p>
  <nav class="toc">{"".join(toc)}</nav>
  {"".join(sections)}
  <footer>Generado automáticamente desde index.html · ilovepappers</footer>
</div>
</body>
</html>"""

Path("resumen_general.html").write_text(HTML, encoding="utf-8")
print("OK -> resumen_general.html")
print("Papers agrupados:", total, "de", len(cards))
# sanity: ¿alguno sin asignar?
missing = [i for i in range(len(cards)) if i not in TOPIC_OF]
print("Sin asignar:", missing)
