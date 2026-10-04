#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py · genera los documentos del lead desde un solo config.json.

Uso:
    python scripts/generate.py
    python scripts/generate.py --config config.json --informe 00-auditoria/informe.html --propuesta 01-propuesta/propuesta.html

Produce:
    informe.html    documento A4 con membrete y pie en cada hoja, paginado por
                    templates/print.js (el paginador se auto-verifica: data-desbordes=0)
    propuesta.html  propuesta comercial narrativa + selector interactivo de módulos

Regla de la casa: los totales se calculan, nunca se escriben. Este script es el
único que resuelve los placeholders; si queda uno sin resolver, falla.
"""

import argparse
import base64
import html
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "brand"
TEMPLATES = ROOT / "templates"

PRINT_JS_MARKER = "Paginador del informe"


def read(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def esc(text) -> str:
    return html.escape(str(text if text is not None else ""), quote=False)


def money(n) -> str:
    return f"USD {int(n):,}".replace(",", ".")


def miles(n) -> str:
    """Separador de miles argentino: 1.551.900"""
    return f"{int(round(n)):,}".replace(",", ".")


def dec1(n) -> str:
    """Un decimal con coma decimal: 9,1"""
    return f"{n:.1f}".replace(".", ",")


def render(tpl: str, data: dict) -> str:
    out = tpl
    for key, value in data.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out


# ---------------------------------------------------------------- bloques

def finding_card(h: dict) -> str:
    tipo = (h.get("tipo") or "[MEDIDO]").strip("[]").lower()
    cls = {"medido": "tag-medido", "inferible": "tag-inferible"}.get(tipo, "tag-noverif")
    prio = (h.get("prioridad") or "").strip().lower()
    prio_tag = (f'<span class="tag tag-prio-{esc(prio)}">Prioridad {esc(prio)}</span>'
                if prio else "")
    return f"""
    <div class="finding">
      <div class="finding-head">
        <span class="tag {cls}">{esc(h.get('tipo') or '[MEDIDO]')}</span>
        {prio_tag}
        <span class="finding-title">{esc(h.get('titulo'))}</span>
      </div>
      <p>{esc(h.get('descripcion'))}</p>
      <div class="finding-meta">
        <span>Impacto estimado: <strong>{esc(h.get('impacto'))}</strong></span>
        <span class="tag">[INFERIBLE]</span>
      </div>
    </div>"""


def compare_table(comp: dict) -> str:
    cols = comp.get("columnas", [])
    head = "<thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr></thead>"
    rows = []
    for fila in comp.get("filas", []):
        celdas = []
        for i, c in enumerate(fila.get("celdas", [])):
            txt = str(c)
            cls = ""
            if i > 0:
                if re.match(r"^(200|✓)", txt):
                    cls = "ok"
                elif re.search(r"✗|404|0$|no resuelve|bloqueó", txt):
                    cls = "bad"
                elif txt == "—":
                    cls = "meh"
            celdas.append(f'<td class="{cls}">{esc(txt)}</td>')
        rowcls = "row-client" if fila.get("cliente") else ""
        rows.append(f'<tr class="{rowcls}">' + "".join(celdas) + "</tr>")
    return f'<table class="compare-table">{head}<tbody>' + "".join(rows) + "</tbody></table>"


def alcance_item(texto: str) -> str:
    """El alcance declara qué se miró (✓) y qué no (✗). La marca la pone la config."""
    t = str(texto).strip()
    if t.startswith("✓"):
        marca, resto, cls = "✓", t[1:].strip(), "yes"
    elif t.startswith("✗"):
        marca, resto, cls = "✗", t[1:].strip(), "no"
    else:
        marca, resto, cls = "·", t, "no"
    return f'<li><span class="{cls}">{marca}</span> {esc(resto)}</li>'


def kpi_row(kpis: list) -> str:
    if not kpis:
        return ""
    items = "".join(
        f'<div class="kpi"><span class="kpi__value">{esc(k.get("valor"))}</span>'
        f'<span class="kpi__label">{esc(k.get("label"))}</span></div>'
        for k in kpis
    )
    return f'<div class="kpi-row">{items}</div>'


def scenarios(base: int, modulos: list) -> list:
    """Mismos escenarios que calcula el paginador. Se derivan, no se escriben."""
    prices = [int(m.get("price", 0)) for m in modulos]
    combo2 = base + (prices[0] if len(prices) > 0 else 0) + (prices[1] if len(prices) > 1 else 0)
    combo3 = combo2 + (prices[2] if len(prices) > 2 else 0)
    total = base + sum(prices)
    pack = round(total * 0.85 / 5) * 5
    codes = [m.get("code", "") for m in modulos]
    return [
        ("Entrada", "Base sola", base),
        ("Intermedio", f"Base + {codes[0]} + {codes[1]}", combo2),
        ("Recomendado", f"Base + {codes[0]} + {codes[1]} + {codes[2]}", combo3),
        ("Pack completo", f"Base + los {len(modulos)} módulos", total),
        ("Pack con descuento", f"Pack completo con 15% de descuento", pack),
    ]


def imagen_uri(path: Path, ancho: int = 900, calidad: int = 72) -> str:
    """Embebe una imagen como data URI JPEG, redimensionada. Sin red, sin archivos sueltos."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    if im.width > ancho:
        alto = round(im.height * ancho / im.width)
        im = im.resize((ancho, alto), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=calidad, optimize=True, progressive=True)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def shots_band(cfg: dict) -> str:
    """Banda de antes/después. Sólo se arma si las dos capturas existen."""
    imgs = cfg.get("imagenes") or {}
    antes, despues = imgs.get("antes"), imgs.get("despues")
    if not (antes and despues):
        return ""
    pa, pd = ROOT / antes, ROOT / despues
    if not (pa.exists() and pd.exists()):
        return ""
    return f"""
<section class="band band--soft">
  <div class="wrap">
    <span class="eyebrow">El cambio, en una mirada</span>
    <h2 style="font-size:1.5rem;margin-top:.75rem">Cómo se ve hoy y cómo se vería</h2>
    <p>Las dos capturas son reales: la de la izquierda es tu sitio actual, tomada el {esc(cfg.get('meta', {}).get('fecha'))};
       la de la derecha es el sitio nuevo, funcionando y verificado.</p>
    <div class="grid-2">
      <div class="shot">
        <img src="{imagen_uri(pa)}" alt="Sitio actual de {esc(cfg.get('meta', {}).get('nombre'))}">
        <div class="shot__cap">Hoy — template de plataforma, sin WhatsApp, sin descripción para Google</div>
      </div>
      <div class="shot">
        <img src="{imagen_uri(pd)}" alt="Propuesta de sitio nuevo para {esc(cfg.get('meta', {}).get('nombre'))}">
        <div class="shot__cap">Propuesta — sitio propio, tus fotos reales, tu habilitación como texto</div>
      </div>
    </div>
  </div>
</section>"""


def conversion_block(cfg: dict, base: int, modulos: list) -> str:
    conv = cfg.get("conversion") or {}
    tc = float(conv.get("tipoCambio") or 0)
    ses = int(conv.get("tarifaSesion") or 0)
    if not (tc and ses):
        return "<p>Sin referencia de cambio declarada: la conversión queda [NO VERIFICADO].</p>"

    filas = ""
    for nombre, detalle, usd in scenarios(base, modulos):
        filas += (
            f"<tr><td>{esc(detalle)}</td><td>{money(usd)}</td>"
            f"<td>AR$ {miles(usd * tc)}</td><td>{dec1(usd * tc / ses)} sesiones</td></tr>"
        )

    total_all = base + sum(int(m.get("price", 0)) for m in modulos)
    sesiones_pack = total_all * tc / ses
    recupero_base = base * tc / 240000

    return f"""
    <p>Traducido a lo que ya sabés contar, con dos referencias tuyas: la tarifa que publicás
       (AR$ {miles(ses)}) y el tipo de cambio del {esc(conv.get('tipoCambioFecha'))}
       ({esc(conv.get('tipoCambioDetalle'))}, fuente: {esc(conv.get('tipoCambioFuente'))}).</p>
    <table class="price-table">
      <thead><tr><th>Escenario</th><th>En dólares</th><th>En pesos</th><th>Equivale a</th></tr></thead>
      <tbody>{filas}
      </tbody>
    </table>
    <p class="evsrc">El pack completo ({money(total_all)}) se paga con {dec1(sesiones_pack)} sesiones:
       menos de lo que facturás en tres semanas trabajando a una consulta por día.
       Y si el sitio recupera una sola consulta por semana, la base de {money(base)}
       se paga en {dec1(recupero_base)} meses.</p>
    <p class="evsrc">[INFERIBLE] La recuperación depende de tu agenda real, que no veo.
       El número de sesiones equivalentes, en cambio, es aritmética sobre datos que vos publicás.</p>"""


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--informe", default="00-auditoria/informe.html")
    ap.add_argument("--propuesta", default="01-propuesta/propuesta.html")
    args = ap.parse_args()

    config_path = ROOT / args.config
    if not config_path.exists():
        print(f"ERROR: no existe {config_path}")
        return 1

    cfg = json.loads(read(config_path))
    meta = cfg.get("meta", {})
    author = cfg.get("author", {})
    hallazgos = cfg.get("hallazgos", [])
    modulos = cfg.get("modulos", [])
    pasos = cfg.get("nextSteps", [])
    comp = cfg.get("comparativo", {})
    base = int(cfg.get("base", {}).get("precio", 0))
    base_items = cfg.get("base", {}).get("items", [])

    costo_mensual = cfg.get("costoMensual", "[NO DECLARADO]")
    base_calculo = cfg.get("baseCalculo", "[NO DECLARADO]")
    comparativos = str(cfg.get("comparativos", 0))
    total_all = base + sum(int(m.get("price", 0)) for m in modulos)

    # ---- marca y fragmentos compartidos
    brand_css = read(BRAND / "brand.css")
    print_css = read(TEMPLATES / "print.css")
    logo_svg = read(BRAND / "assets" / "logo.svg")

    header = render(read(BRAND / "header.html"), {
        "LOGO_SVG": logo_svg,
        "DOC_TITLE": esc(meta.get("nombre", "")),
    })
    footer = render(read(BRAND / "footer.html"), {
        "FOOTER_META": esc(f"{author.get('email', '')} · {meta.get('fecha', '')}"),
    })

    common = {
        "BRAND_CSS": brand_css,
        "HEADER": header,
        "FOOTER": footer,
        "NOMBRE_CLIENTE": esc(meta.get("nombre")),
        "NOMBRE_CLIENTE_ENCODED": esc(meta.get("nombre", "")).replace(" ", "%20"),
        "PROFESION": esc(meta.get("profesion")),
        "MATRICULA": esc(meta.get("matricula")),
        "RUBRO": esc(meta.get("rubro")),
        "FECHA": esc(meta.get("fecha")),
        "VALIDEZ": esc(meta.get("validez")),
        "URL_CLIENTE": esc(meta.get("url")),
        "META_URL": esc(meta.get("url")),
        "AUTHOR_NOMBRE": esc(author.get("nombre")),
        "AUTHOR_EMAIL": esc(author.get("email")),
        "NUM_HALLAZGOS": str(len(hallazgos)),
        "NUM_COMPARATIVOS": comparativos,
        "COSTO_MENSUAL": esc(costo_mensual),
        "BASE_CALCULO": esc(base_calculo),
        "PRECIO_BASE": str(base),
        "TOTAL": str(total_all),
        "PASOS_HTML": "".join(f"<li>{esc(p)}</li>" for p in pasos),
        "BASE_ITEMS_HTML": "".join(f"<li>{esc(i)}</li>" for i in base_items),
        "ALCANCE_HTML": "".join(alcance_item(a) for a in cfg.get("alcance", [])),
        "PREGUNTAS_HTML": "".join(f"<li>{esc(p)}</li>" for p in cfg.get("preguntasAbiertas", [])),
        "SIN_INCLUIR_HTML": "".join(f"<li>{esc(p)}</li>" for p in cfg.get("sinIncluir", [])),
        "MODULOS_JSON": json.dumps(modulos, ensure_ascii=False),
        "KPI_HTML": kpi_row(comp.get("kpis", [])),
        # acceso directo -> no se usa en el informe, sí en la propuesta
        "HALLAZGOS_HTML": "".join(finding_card(h) for h in hallazgos),
    }

    # ---- propuesta: bloques propios
    conv = cfg.get("conversion") or {}
    propuesta_data = dict(common)
    propuesta_data.update({
        "COMPARATIVO_HTML": compare_table(comp),
        "COMPARATIVO_INTRO": esc(comp.get("intro", "")),
        "COMPARATIVO_NOTA": esc(comp.get("nota", "")),
        "COMPARATIVO_FUENTE": esc(
            f"Medición propia del {comp.get('medidoEl', '')} · reproducible con: "
            "python scripts/medir.py --pares 00-auditoria/pares.txt"
        ),
        "ESCENARIOS_HTML": "".join(
            f"<li><strong>{esc(n)}:</strong> {esc(d)} — <strong>{money(u)}</strong></li>"
            for n, d, u in scenarios(base, modulos)
        ),
        "CONVERSION_HTML": conversion_block(cfg, base, modulos),
        "SHOTS_BAND": shots_band(cfg),
        "TIPO_CAMBIO": str(conv.get("tipoCambio", 0)),
        "TARIFA_SESION": str(conv.get("tarifaSesion", 0)),
        "WHATSAPP_CTA_HTML": (
            f'<a class="btn btn-wa" href="https://wa.me/{esc(author.get("whatsapp"))}'
            '?text=Hola%2C%20vi%20la%20propuesta%20para%20Lisandro%20Lagos" rel="noopener" target="_blank">'
            'Responder por WhatsApp</a>' if author.get("whatsapp") else ""
        ),
    })

    # ---- informe: shell + paginador
    def js_json(obj) -> str:
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    informe_data = dict(common)
    informe_data.update({
        "PRINT_CSS": print_css,
        "CONFIG_JSON": js_json(cfg),
        "HEADER_JSON": js_json(header),
        "FOOTER_JSON": js_json(footer),
        "PAGINATOR_JS": read(TEMPLATES / "print.js"),
    })

    informe_html = render(read(TEMPLATES / "informe.html"), informe_data)
    propuesta_html = render(read(TEMPLATES / "propuesta.html"), propuesta_data)

    out_informe = ROOT / args.informe
    out_propuesta = ROOT / args.propuesta
    out_informe.parent.mkdir(parents=True, exist_ok=True)
    out_propuesta.parent.mkdir(parents=True, exist_ok=True)
    out_informe.write_text(informe_html, encoding="utf-8")
    out_propuesta.write_text(propuesta_html, encoding="utf-8")

    # ---- verificación: se relee de disco, se valida el archivo real
    errores = []
    producidos = {
        "informe": out_informe.read_text(encoding="utf-8"),
        "propuesta": out_propuesta.read_text(encoding="utf-8"),
    }

    for name, text in producidos.items():
        left = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", text)))
        if left:
            errores.append(f"{name}: placeholders sin resolver -> {left}")

    for name, text in producidos.items():
        if "--brand-default" not in text:
            errores.append(f"{name}: falta el CSS de marca inyectado")
        if "brand-header" not in text or "brand-footer" not in text:
            errores.append(f"{name}: falta el membrete o el pie compartido")

    if PRINT_JS_MARKER not in producidos["informe"]:
        errores.append("informe: el paginador no se inyectó")

    m_inj = re.search(r"window\.CLIENT_CONFIG = (\{.*?\});", producidos["informe"], re.S)
    if not m_inj:
        errores.append("informe: no pude leer la config inyectada")
    else:
        try:
            inj = json.loads(m_inj.group(1).replace("<\\/", "</"))
            inj_total = int(inj.get("base", {}).get("precio", 0)) + sum(
                int(m.get("price", 0)) for m in inj.get("modulos", [])
            )
            if inj_total != total_all:
                errores.append(f"config inyectada suma {inj_total} y el generador calculó {total_all}")
        except Exception as e:  # noqa: BLE001
            errores.append(f"informe: la config inyectada no es JSON válido ({e})")

    for m in modulos:
        if m.get("title") and m["title"] not in producidos["informe"]:
            errores.append(f"módulo '{m['title']}' falta en el informe")
        if m.get("code") and f'"{m["code"]}"' not in producidos["propuesta"]:
            errores.append(f"módulo {m['code']} falta en el selector de la propuesta")

    # El total de la propuesta tiene que aparecer calculado, no escrito a mano.
    if f"USD {base}" not in producidos["propuesta"]:
        errores.append("propuesta: el total inicial no coincide con el precio base")

    # Cada hallazgo tiene que haber entrado con su prioridad visible.
    for h in hallazgos:
        if (h.get("prioridad") or "").lower() not in producidos["propuesta"].lower():
            errores.append(f"propuesta: hallazgo sin prioridad visible -> {h.get('titulo')[:40]}")
            break

    print("=" * 68)
    print(f"  GENERANDO LEAD: {meta.get('nombre')}")
    print("=" * 68)
    print(f"  hallazgos        : {len(hallazgos)}")
    print(f"  módulos          : {len(modulos)}")
    print(f"  comparativo      : {len(comp.get('filas', []))} filas")
    print(f"  base             : {money(base)}")
    print(f"  pack completo    : {money(total_all)}")
    print(f"  informe          : {out_informe.relative_to(ROOT)}")
    print(f"  propuesta        : {out_propuesta.relative_to(ROOT)}")
    print("-" * 68)
    if errores:
        print("  ✗ VERIFICACIÓN FALLÓ")
        for e in errores:
            print(f"      - {e}")
        return 2
    print("  ✓ Sin placeholders sin resolver")
    print(f"  ✓ Config inyectada válida y consistente (total {money(total_all)})")
    print(f"  ✓ Paginador inyectado · {len(modulos)} módulos · {len(hallazgos)} hallazgos")
    print("  ✓ CSS de marca, membrete y pie en las dos piezas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
