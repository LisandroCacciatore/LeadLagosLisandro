#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify-pdf.py · verifica el PDF REAL del informe.

No alcanza con que el HTML se vea bien: se exporta el PDF con Chrome headless y se
lee el texto de cada página con pypdf (sin depender de binarios externos).

Criterios de aceptación:
    Hojas      : dentro del rango declarado
    Secciones  : todas presentes, en orden de aparición
    Membrete   : repetido, al menos una aparición por hoja
    Pie        : sin encimado sobre el contenido (el bug original del paginador)
    Totales    : el total de la config aparece en el PDF
    Módulos    : cada título de módulo de la config aparece en el PDF

Uso:
    python scripts/verify-pdf.py
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INFORME = ROOT / "00-auditoria" / "informe.html"
PDF = ROOT / "00-auditoria" / "informe-lagos.pdf"
CONFIG = ROOT / "config.json"

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

SECCIONES = [
    "Resumen Ejecutivo",
    "Diagnóstico",
    "Comparativo verificado",
    "Propuesta de Valor",
    "Inversión y Próximos Pasos",
    "Alcance de esta revisión",
    "Aceptación de la propuesta",
]
RANGO_HOJAS = (10, 14)


def miles(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def exportar(chrome: str) -> bool:
    PDF.parent.mkdir(parents=True, exist_ok=True)
    PDF.unlink(missing_ok=True)
    perfil = ROOT / ".chrome-tmp"
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--no-first-run",
        f"--user-data-dir={perfil}", "--virtual-time-budget=14000",
        "--no-pdf-header-footer", f"--print-to-pdf={PDF}", INFORME.resolve().as_uri(),
    ], capture_output=True, text=True, errors="replace")
    shutil.rmtree(perfil, ignore_errors=True)
    return PDF.exists()


def main() -> int:
    if not INFORME.exists():
        print("  ✗ falta 00-auditoria/informe.html — corré: python scripts/generate.py")
        return 1

    chrome = next((c for c in CHROME if Path(c).exists()), None)
    if not chrome:
        print("No encontré Chrome ni Edge.")
        return 1

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    mod_titles = [m.get("title", "") for m in cfg.get("modulos", [])]
    hall_titles = [h.get("titulo", "") for h in cfg.get("hallazgos", [])]
    total = int(cfg["base"]["precio"]) + sum(int(m.get("price", 0)) for m in cfg.get("modulos", []))

    print("=" * 68)
    print("  VERIFICANDO EL PDF DEL INFORME")
    print("=" * 68)
    if not exportar(chrome):
        print("  ✗ Chrome no produjo el PDF")
        return 2

    try:
        from pypdf import PdfReader
    except ImportError:
        print("  ✗ falta pypdf (pip install pypdf) — no puedo leer el texto del PDF")
        return 2

    lector = PdfReader(str(PDF))
    paginas = len(lector.pages)
    textos = [(p.extract_text() or "") for p in lector.pages]
    todo = "\n".join(textos)

    print(f"  archivo   : {PDF.relative_to(ROOT)}  ({PDF.stat().st_size // 1024} KB)")
    print(f"  hojas     : {paginas}  (esperado {RANGO_HOJAS[0]}-{RANGO_HOJAS[1]})")

    errores = []
    if not (RANGO_HOJAS[0] <= paginas <= RANGO_HOJAS[1]):
        errores.append(f"hojas fuera de rango: {paginas}")

    # ---- Secciones, y que aparezcan en orden
    faltan = [s for s in SECCIONES if s.upper() not in todo.upper()]
    print(f"  secciones : {len(SECCIONES) - len(faltan)}/{len(SECCIONES)}")
    if faltan:
        errores.append(f"faltan secciones: {faltan}")
    else:
        posiciones = [todo.upper().index(s.upper()) for s in SECCIONES]
        if posiciones != sorted(posiciones):
            errores.append("las secciones no aparecen en orden")

    # ---- Membrete repetido: al menos una vez por hoja (menos la portada)
    hits = todo.upper().count("LISANDRO CACCIATORE")
    print(f"  membrete  : x{hits} para {paginas} hojas")
    if hits < paginas - 1:
        errores.append(f"membrete poco repetido: {hits} apariciones para {paginas} hojas")

    # ---- Pie encimado: si un renglón del pie contiene un título de contenido, se superpone
    contenido = [s for s in SECCIONES + mod_titles + hall_titles if s]
    choques = []
    for ln in todo.splitlines():
        if "lisandrocacciatore@gmail.com" not in ln:
            continue
        for token in contenido:
            if len(token) > 12 and token.lower()[:40] in ln.lower():
                choques.append(f"{token[:40]!r} en: {ln.strip()[:80]}")
                break
    print(f"  pie       : {'sin encimado' if not choques else 'ENCIMADO x' + str(len(choques))}")
    if choques:
        errores.append(f"el pie se superpone al contenido en {len(choques)} renglón(es)")
        for c in choques[:3]:
            print(f"      · {c}")

    # ---- Totales y módulos: config -> PDF
    total_str = miles(total)
    print(f"  total     : USD {total_str} {'presente' if total_str in todo else 'AUSENTE'}")
    if total_str not in todo:
        errores.append(f"el total de la config (USD {total_str}) no aparece en el PDF")

    sin_mod = [t for t in mod_titles if t.upper() not in todo.upper()]
    print(f"  módulos   : {len(mod_titles) - len(sin_mod)}/{len(mod_titles)} en el PDF")
    if sin_mod:
        errores.append(f"módulos ausentes en el PDF: {sin_mod}")

    if "Pack completo" not in todo:
        errores.append("falta el escenario «Pack completo»")

    # ---- Los datos verificados del cliente tienen que estar sostenidos en el documento
    for dato in ("Matrícula Provincial N° 5677", "Buenos Aires 1110", "AR$ 240.000"):
        if dato not in todo:
            errores.append(f"falta el dato «{dato}» en el PDF")

    print("-" * 68)
    if errores:
        print("  ✗ PDF CON PROBLEMAS")
        for e in errores:
            print(f"      - {e}")
        return 2
    print(f"  ✓ {paginas} hojas, {len(SECCIONES)}/{len(SECCIONES)} secciones en orden")
    print("  ✓ Membrete repetido y pie sin encimado")
    print("  ✓ Total, módulos y datos verificados presentes en el PDF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
