# CONTEXTO.md — Pipeline de Análisis de Papers Científicos
> Orquestador para Claude Code · Versión 1.0

---

## Objetivo del proyecto

Dado un directorio de papers en PDF, este pipeline:
1. Extrae todas las figuras y captions.
2. Analiza visualmente cada figura con un modelo de visión.
3. Genera un resumen profundo del paper con las figuras integradas.
4. Revisa la calidad del resultado final.

El output es un **HTML autocontenido** por paper (imágenes inline en base64), listo para leer en cualquier browser sin dependencias externas.

---

## Estructura del repositorio esperada

```
project/
├── CONTEXTO.md                  ← este archivo
├── figure_extractor.py          ← extractor de figuras (ya funciona)
├── agents/
│   ├── agent_figure_analyst.py  ← Agente 2: analiza cada figura
│   ├── agent_summarizer.py      ← Agente 3: genera el resumen HTML
│   └── agent_reviewer.py        ← Agente 4: revisión de calidad
├── pipeline.py                  ← orquestador principal (punto de entrada)
├── config.py                    ← configuración global (modelo, rutas, etc.)
├── papers/                      ← directorio de entrada: colocar PDFs aquí
└── output/                      ← directorio de salida: HTMLs generados
```

---

## Configuración global — `config.py`

```python
# config.py
from pathlib import Path

# ── Modelo de visión ───────────────────────────────────────────────────────────
# Opciones: "claude-sonnet-4-6" | "gpt-4.5"  (ver nota abajo)
VISION_MODEL = "claude-sonnet-4-6"

# ── Modelo de texto (resumen y revisión) ──────────────────────────────────────
TEXT_MODEL = "claude-sonnet-4-6"

# ── Rutas ─────────────────────────────────────────────────────────────────────
PAPERS_DIR  = Path("papers")
OUTPUT_DIR  = Path("output")
TEMP_DIR    = Path(".pipeline_tmp")   # figuras extraídas temporalmente

# ── Calidad de imagen ─────────────────────────────────────────────────────────
IMAGE_SCALE = 2.0   # resolución Docling (1.0 = 72dpi, 2.0 = 144dpi)

# ── Idioma del resumen final ──────────────────────────────────────────────────
OUTPUT_LANGUAGE = "español"   # o "english"
```

> **Nota sobre el modelo de visión:**
> - `claude-sonnet-4-6` → usa la API de Anthropic (variable de entorno: `ANTHROPIC_API_KEY`)
> - `gpt-4.5` → usa la API de OpenAI (variable de entorno: `OPENAI_API_KEY`)
> El código de cada agente detecta automáticamente el modelo y usa el cliente correcto.

---

## Etapa 0 — `pipeline.py` (orquestador)

**Responsabilidad:** punto de entrada. Itera sobre los PDFs en `papers/`, llama a cada agente en orden, maneja errores y genera logs.

```python
# pipeline.py  — esqueleto funcional
import sys
from pathlib import Path
from config import PAPERS_DIR, OUTPUT_DIR, TEMP_DIR

from figure_extractor import extract_figures, save_images, save_json
from agents.agent_figure_analyst import analyze_figures
from agents.agent_summarizer import generate_summary_html
from agents.agent_reviewer import review_and_fix

def process_paper(pdf_path: Path):
    paper_id = pdf_path.stem
    tmp = TEMP_DIR / paper_id
    tmp.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Procesando: {pdf_path.name}")
    print(f"{'='*60}")

    # ── Etapa 1: Extracción ───────────────────────────────────────────
    result = extract_figures(pdf_path)
    if result.total_figures == 0:
        print("  [!] Sin figuras. Se genera resumen solo-texto.")
    save_images(result, pdf_path, tmp)
    save_json(result, tmp)

    # ── Etapa 2: Análisis de figuras ──────────────────────────────────
    analyzed = analyze_figures(result, tmp)  # devuelve ExtractionResult enriquecido

    # ── Etapa 3: Resumen HTML ─────────────────────────────────────────
    html_draft = generate_summary_html(pdf_path, analyzed)

    # ── Etapa 4: Revisión de calidad ──────────────────────────────────
    html_final = review_and_fix(html_draft, analyzed)

    # ── Guardar ───────────────────────────────────────────────────────
    out_path = OUTPUT_DIR / f"{paper_id}.html"
    out_path.write_text(html_final, encoding="utf-8")
    print(f"\n  ✓ HTML final: {out_path}")

def main():
    pdfs = list(PAPERS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"[!] No hay PDFs en {PAPERS_DIR}/")
        sys.exit(1)
    for pdf in sorted(pdfs):
        try:
            process_paper(pdf)
        except Exception as e:
            print(f"  [ERROR] {pdf.name}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
```

---

## Etapa 1 — Extracción de figuras (`figure_extractor.py`)

**Herramienta:** Docling  
**Input:** `paper.pdf`  
**Output:**
- `<tmp>/images/fig_001.png`, `fig_002.png`, …
- `<tmp>/figures.json` con `figure_id`, `label`, `caption`, `page`, `bbox`

**Ya implementado y funcional.** No modificar salvo para ajustar `IMAGE_SCALE`.

**Contrato de datos de salida (figures.json):**
```json
{
  "source_file": "papers/attention.pdf",
  "total_figures": 5,
  "figures": [
    {
      "figure_id": "fig_001",
      "label": "picture",
      "caption": "Figure 1: The Transformer model architecture.",
      "page": 3,
      "bbox": {"l": 72.0, "t": 680.0, "r": 540.0, "b": 420.0}
    }
  ]
}
```

---

## Etapa 2 — Análisis de figuras (`agents/agent_figure_analyst.py`)

**Responsabilidad:** Para cada figura, enviar la imagen + caption al modelo de visión y obtener un análisis detallado.

**Input:** `ExtractionResult` + directorio `tmp/images/`  
**Output:** `ExtractionResult` enriquecido con campo `analysis` en cada `FigureRecord`

### Prompt del agente (visión)

```
SYSTEM:
Sos un investigador científico experto en análisis de papers. 
Tu tarea es analizar figuras de artículos científicos con precisión técnica.
Respondé ÚNICAMENTE en JSON con esta estructura exacta, sin texto adicional ni backticks:
{
  "type": "diagram|chart|photo|equation|table|other",
  "what_shows": "descripción técnica de qué muestra la figura (2-3 oraciones)",
  "key_insight": "insight principal o resultado que comunica (1-2 oraciones)",
  "relation_to_paper": "cómo se relaciona con el argumento central del paper (1 oración)",
  "importance": "high|medium|low"
}

USER:
Caption: {caption}

[imagen adjunta]
```

### Esqueleto del agente

```python
# agents/agent_figure_analyst.py
import base64, json
from pathlib import Path
from config import VISION_MODEL
from figure_extractor import ExtractionResult, FigureRecord

def _encode_image(img_path: Path) -> str:
    return base64.b64encode(img_path.read_bytes()).decode()

def _analyze_one_figure(rec: FigureRecord, img_path: Path) -> dict:
    """Llama al modelo de visión y retorna el dict de análisis."""
    img_b64 = _encode_image(img_path)
    
    if VISION_MODEL.startswith("claude"):
        return _call_anthropic(rec, img_b64)
    else:
        return _call_openai(rec, img_b64)

def _call_anthropic(rec: FigureRecord, img_b64: str) -> dict:
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=VISION_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_b64}},
                {"type": "text", "text": f"Caption: {rec.caption or 'Sin caption'}"}
            ]
        }]
    )
    raw = response.content[0].text.strip()
    return json.loads(raw)

def _call_openai(rec: FigureRecord, img_b64: str) -> dict:
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": f"Caption: {rec.caption or 'Sin caption'}"}
            ]
        }],
        max_tokens=1024
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

SYSTEM_PROMPT = """
Sos un investigador científico experto en análisis de papers. 
Analiza la figura con precisión técnica. 
Respondé ÚNICAMENTE en JSON válido con esta estructura, sin texto ni backticks:
{
  "type": "diagram|chart|photo|equation|table|other",
  "what_shows": "...",
  "key_insight": "...",
  "relation_to_paper": "...",
  "importance": "high|medium|low"
}
""".strip()

def analyze_figures(result: ExtractionResult, tmp_dir: Path) -> ExtractionResult:
    images_dir = tmp_dir / "images"
    for rec in result.figures:
        img_path = images_dir / f"{rec.figure_id}.png"
        if not img_path.exists():
            print(f"  [!] {rec.figure_id}: imagen no encontrada, se omite análisis.")
            continue
        try:
            analysis = _analyze_one_figure(rec, img_path)
            rec.__dict__["analysis"] = analysis   # enriquecemos el record dinámicamente
            importance = analysis.get("importance", "?")
            print(f"  [+] {rec.figure_id} analizado — importancia: {importance}")
        except Exception as e:
            print(f"  [!] {rec.figure_id}: error en análisis — {e}")
            rec.__dict__["analysis"] = None
    return result
```

---

## Etapa 3 — Generación del resumen HTML (`agents/agent_summarizer.py`)

**Responsabilidad:** Leer el texto completo del PDF + todos los análisis de figuras → generar el HTML final.

**Input:** `pdf_path`, `ExtractionResult` enriquecido  
**Output:** `str` con el HTML completo (imágenes inline como base64)

### Prompt del agente (texto largo)

```
SYSTEM:
Sos un divulgador científico de élite. Tu tarea es generar un resumen profundo y detallado
de un paper científico en {OUTPUT_LANGUAGE}. El resultado debe ser un HTML autocontenido,
visualmente sofisticado, con las figuras del paper integradas y explicadas en contexto.

REQUISITOS DEL HTML:
- Una sola página, sin dependencias externas (fuentes vía @import de Google Fonts está OK)
- Imágenes como <img src="data:image/png;base64,..."> (inline)
- Secciones: Resumen ejecutivo · Contexto y motivación · Metodología · 
              Resultados clave · Figuras y su interpretación · Conclusiones · Limitaciones
- Cada figura aparece en la sección "Figuras" con: la imagen, el caption original,
  y un párrafo explicando qué muestra, por qué importa, y cómo se relaciona con el paper
- Tono: técnico pero accesible; evitar jerga sin explicación
- Diseño: elegante, editorial, dark theme con tipografía serif para títulos
  y sans-serif para cuerpo; máximo ancho 900px centrado; figuras con sombra sutil

USER:
=== TEXTO COMPLETO DEL PAPER ===
{paper_text}

=== ANÁLISIS DE FIGURAS ===
{figures_json_with_analysis}

=== IMÁGENES (base64) ===
{figures_base64_map}

Generá el HTML completo autocontenido.
```

### Esqueleto del agente

```python
# agents/agent_summarizer.py
import base64, json
from pathlib import Path
import anthropic
from config import TEXT_MODEL, OUTPUT_LANGUAGE
from figure_extractor import ExtractionResult

def _extract_text_from_pdf(pdf_path: Path) -> str:
    """Extrae texto plano del PDF usando Docling."""
    from docling.document_converter import DocumentConverter
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    return result.document.export_to_markdown()

def _build_figures_payload(result: ExtractionResult, tmp_dir: Path) -> tuple[str, dict]:
    """Construye el JSON de análisis y el mapa base64 de imágenes."""
    images_dir = tmp_dir / "images"
    figures_data = []
    b64_map = {}

    for rec in result.figures:
        entry = {
            "figure_id": rec.figure_id,
            "label": rec.label,
            "caption": rec.caption,
            "page": rec.page,
            "analysis": rec.__dict__.get("analysis"),
        }
        figures_data.append(entry)

        img_path = images_dir / f"{rec.figure_id}.png"
        if img_path.exists():
            b64_map[rec.figure_id] = base64.b64encode(img_path.read_bytes()).decode()

    return json.dumps(figures_data, indent=2, ensure_ascii=False), b64_map

def generate_summary_html(pdf_path: Path, result: ExtractionResult) -> str:
    tmp_dir = Path(".pipeline_tmp") / pdf_path.stem
    paper_text = _extract_text_from_pdf(pdf_path)
    figures_json, b64_map = _build_figures_payload(result, tmp_dir)

    # Construir lista base64 legible para el prompt
    b64_section = "\n".join(
        f"{fig_id}: data:image/png;base64,{b64[:40]}..."  # solo preview en el prompt
        for fig_id, b64 in b64_map.items()
    )

    # Para el HTML final el agente recibirá los b64 completos vía herramienta/contexto
    # Aquí los inyectamos directamente en el prompt (paper corto) o en bloques (paper largo)
    client = anthropic.Anthropic()
    
    # Construir content con imágenes reales para que el modelo las pueda referir
    content_blocks = []
    content_blocks.append({"type": "text", "text": SUMMARIZER_PROMPT.format(
        OUTPUT_LANGUAGE=OUTPUT_LANGUAGE,
        paper_text=paper_text[:40000],  # truncar si muy largo
        figures_json=figures_json,
    )})

    response = client.messages.create(
        model=TEXT_MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": content_blocks}]
    )

    html_draft = response.content[0].text.strip()

    # Reemplazar placeholders {{fig_001}} → src base64 real
    for fig_id, b64 in b64_map.items():
        placeholder = f"{{{{IMAGE:{fig_id}}}}}"
        html_draft = html_draft.replace(placeholder, f"data:image/png;base64,{b64}")

    return html_draft

SUMMARIZER_PROMPT = """
Sos un divulgador científico de élite. Generá un resumen profundo en {OUTPUT_LANGUAGE} del siguiente paper.

OUTPUT: HTML autocontenido (sin dependencias externas salvo Google Fonts @import).
- Dark theme editorial, tipografía serif para títulos, sans para cuerpo, máx 900px centrado
- Secciones obligatorias: Resumen ejecutivo · Contexto · Metodología · Resultados clave · 
  Figuras · Conclusiones · Limitaciones
- Para cada figura en la sección Figuras, usar exactamente este placeholder como src de la imagen:
  {{IMAGE:fig_001}}  (reemplazá "fig_001" con el figure_id real)
  Ejemplo: <img src="{{IMAGE:fig_001}}" alt="fig_001">
- Debajo de cada imagen: caption original + párrafo de interpretación basado en el análisis

=== TEXTO DEL PAPER ===
{paper_text}

=== ANÁLISIS DE FIGURAS ===
{figures_json}

Generá el HTML completo.
""".strip()
```

---

## Etapa 4 — Revisión de calidad (`agents/agent_reviewer.py`)

**Responsabilidad:** Revisar el HTML generado, detectar problemas y corregirlos automáticamente.

**Input:** `html_draft: str`, `ExtractionResult`  
**Output:** `html_final: str` corregido

### Checklist de revisión (el agente lo ejecuta internamente)

```
1. ¿Están todas las figuras incluidas? (comparar figure_ids con los <img> en el HTML)
2. ¿Los placeholders {{IMAGE:fig_xxx}} fueron reemplazados? (no debe quedar ninguno)
3. ¿El HTML es válido y autocontenido? (no referencias externas a archivos locales)
4. ¿El resumen ejecutivo cubre: problema, método, resultado principal, conclusión?
5. ¿Las interpretaciones de figuras son técnicamente consistentes con el análisis?
6. ¿Hay secciones vacías o incompletas?
7. ¿El tono es consistente (técnico pero accesible)?
```

### Esqueleto del agente

```python
# agents/agent_reviewer.py
import anthropic
from config import TEXT_MODEL
from figure_extractor import ExtractionResult

def review_and_fix(html_draft: str, result: ExtractionResult) -> str:
    """Revisa y corrige el HTML. Retorna el HTML final."""
    client = anthropic.Anthropic()

    expected_ids = [rec.figure_id for rec in result.figures]
    present_ids  = [fid for fid in expected_ids if fid in html_draft]
    missing_ids  = [fid for fid in expected_ids if fid not in html_draft]
    placeholders_left = "{{IMAGE:" in html_draft

    issues = []
    if missing_ids:
        issues.append(f"Figuras faltantes en el HTML: {missing_ids}")
    if placeholders_left:
        issues.append("Quedan placeholders {{IMAGE:...}} sin reemplazar.")

    if not issues:
        print("  [✓] Revisión OK — sin problemas detectados.")
        return html_draft

    print(f"  [!] Revisión detectó {len(issues)} problema(s): {issues}")

    response = client.messages.create(
        model=TEXT_MODEL,
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": REVIEWER_PROMPT.format(
                issues="\n".join(f"- {i}" for i in issues),
                html=html_draft,
            )
        }]
    )
    
    fixed = response.content[0].text.strip()
    # Limpiar si el modelo envuelve en backticks
    if fixed.startswith("```"):
        fixed = fixed.split("\n", 1)[1].rsplit("```", 1)[0]
    
    print("  [✓] HTML corregido por el agente revisor.")
    return fixed

REVIEWER_PROMPT = """
El siguiente HTML tiene estos problemas:
{issues}

Corregí el HTML completo y devolvé SOLO el HTML corregido (sin explicaciones, sin backticks).
Si un placeholder {{IMAGE:fig_xxx}} no fue reemplazado, reemplazalo con un mensaje visible:
<div class="missing-fig">⚠ Imagen fig_xxx no disponible</div>

=== HTML A CORREGIR ===
{html}
""".strip()
```

---

## Flujo de ejecución completo

```
papers/paper.pdf
       │
       ▼
[Etapa 1] figure_extractor.py
       │  → .pipeline_tmp/paper/images/fig_001.png … fig_N.png
       │  → .pipeline_tmp/paper/figures.json
       │
       ▼
[Etapa 2] agent_figure_analyst.py
       │  → figures.json enriquecido con campo "analysis" por figura
       │    (type, what_shows, key_insight, relation_to_paper, importance)
       │
       ▼
[Etapa 3] agent_summarizer.py
       │  → HTML draft con resumen profundo + figuras inline
       │    (placeholders {{IMAGE:fig_xxx}} → base64 real)
       │
       ▼
[Etapa 4] agent_reviewer.py
       │  → HTML final corregido
       │
       ▼
output/paper.html   ← resultado final, autocontenido
```

---

## Instalación y uso

```bash
# 1. Instalar dependencias
pip install docling pillow anthropic openai

# 2. Variables de entorno
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."   # solo si usás gpt-4.5

# 3. Colocar PDFs en papers/
cp mis_papers/*.pdf papers/

# 4. Ejecutar el pipeline
python pipeline.py

# 5. Ver resultados
ls output/          # → paper1.html, paper2.html, ...
```

### Ejecutar con Claude Code (VS Code)

Abrir la terminal integrada de VS Code en la raíz del proyecto y ejecutar:
```bash
claude "Ejecutá pipeline.py sobre todos los PDFs en papers/ y reportame el resultado de cada etapa"
```
O interactivamente:
```bash
claude
> procesá solo el paper attention.pdf
> el resumen de fig_003 no es correcto, regeneralo
> mostrá un resumen del resultado de revisión de calidad
```

---

## Extensiones futuras (no implementadas)

| Feature | Descripción |
|---|---|
| `--lang` flag | Generar el HTML en inglés o español desde CLI |
| Cache de análisis | No re-analizar figuras ya procesadas (hash de imagen) |
| Batch paralelo | `asyncio` + semáforo para procesar múltiples papers en paralelo |
| Índice global | `index.html` con links a todos los papers procesados |
| Watchdog | Monitorear `papers/` y procesar automáticamente nuevos PDFs |
| RAG | Indexar todos los resúmenes en una base vectorial para búsqueda semántica |

---

## Notas de diseño para Claude Code

- **Cada agente es independiente y testeable por separado.** Claude Code puede ejecutar `python agents/agent_figure_analyst.py` en modo standalone para probar con un paper específico.
- **Los errores no detienen el pipeline.** Si un agente falla para una figura, la omite con un warning y continúa. El revisor compensa al final.
- **El modelo de visión es intercambiable** con solo cambiar `VISION_MODEL` en `config.py`. No hay que tocar el código de los agentes.
- **El HTML es el artefacto final, no un intermedio.** Está diseñado para ser enviado por email, subido a un servidor, o abierto directamente. Cero dependencias externas.
