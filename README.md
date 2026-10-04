# Lead Lagos Lisandro

Auditoría, propuesta comercial y sitio nuevo para el **Lic. Lisandro Lagos**,
psicólogo clínico y psicoanalista en Rosario (Matrícula Provincial N° 5677).

Un solo repositorio, tres entregables, una sola fuente de datos: `config.json`.
**Ningún número de este repositorio está escrito a mano**: todos salen de una medición
que se puede volver a correr con los scripts que están acá.

Fecha de la medición: **4 de octubre de 2026**.

---

## Los entregables

| Entregable | Archivo | Qué es |
|---|---|---|
| **Informe de auditoría** | `00-auditoria/informe.html` | Documento A4 con membrete y pie en cada hoja, listo para imprimir a PDF. 12 páginas. |
| **Informe en PDF** | `00-auditoria/informe-lagos.pdf` | El mismo informe ya exportado. |
| **Propuesta comercial** | `01-propuesta/propuesta.html` | Una sola página, con selector de módulos: el total se recalcula al tildar. Incluye la banda de antes/después. |
| **Sitio nuevo** | `02-sitio/index.html` | El sitio propuesto, funcionando: datos reales, fotos reales del consultorio, SEO completo. |
| **Evidencia** | `00-auditoria/evidencia.json` | Todo lo medido, legible por máquina. |
| **Fuentes** | `00-auditoria/fuentes.md` | Ledger: qué se miró, qué se midió y qué **no** se pudo verificar. |
| **Capturas** | `00-auditoria/capturas/`, `02-sitio/capturas/` | Sitio actual y sitio nuevo, en escritorio y celular. |

## Cómo se lee el repositorio

```
lead-lagos-lisandro/
├── config.json                  EL CONTRATO. Hallazgos, módulos, precios, alcance.
├── 00-auditoria/                la auditoría
│   ├── informe.html             generado
│   ├── informe-lagos.pdf        exportado del anterior
│   ├── evidencia.json           consolidado, legible por máquina
│   ├── evidencia-web.json       medición cruda del cliente y de los 6 pares
│   ├── evidencia-doctoralia.json  35 perfiles de Rosario
│   ├── evidencia-antes-despues.json  señales antes/después
│   ├── fuentes.md               ledger de fuentes y descartes
│   ├── pares.txt                los colegas comparados
│   ├── fuentes/                 fotos y certificado, copiados sin retoque
│   └── capturas/                evidencia visual
├── 01-propuesta/                la propuesta comercial
│   └── propuesta.html           generado
├── 02-sitio/                    el sitio nuevo
│   ├── index.html
│   ├── robots.txt · sitemap.xml
│   ├── assets/img/              imágenes optimizadas
│   └── capturas/
├── brand/                       la marca (fuente única de lo visual)
├── templates/                   informe.html · print.js · print.css · propuesta.html
└── scripts/                     el motor
```

## Cómo se regenera todo

```bash
python scripts/preparar-assets.py        # fotos y certificado -> 02-sitio/assets/img
python scripts/generar.sh                # informe.html + propuesta.html desde config.json
python scripts/verify.py                 # render real: paginación y selector (Chrome headless)
python scripts/verificar-sitio.py        # sitio nuevo: señales, DOM, capturas
python scripts/consolidar-evidencia.py   # 00-auditoria/evidencia.json
```

Y para volver a medir las fuentes externas:

```bash
python scripts/medir.py --pares 00-auditoria/pares.txt --out 00-auditoria/evidencia-web.json
python scripts/pesar.py https://www.liclisandrolagos.com/
python scripts/diagnostico-desborde.py 02-sitio/index.html 390
python scripts/movil.py 02-sitio/index.html 390
python scripts/capturar.py
```

`generar.sh` genera los dos documentos y después corre `verify.py`. Si algo no cierra,
devuelve error y no hay entregable.

## Qué quedó verificado (y cómo)

`verify.py` — sobre el **DOM renderizado**, no sobre el HTML fuente:
- el informe paginó en 12 hojas con `data-desbordes=0` (ninguna hoja con contenido cortado);
- los 6 hallazgos y las 6 filas de módulos están en el documento;
- el selector de la propuesta ejecutó su JavaScript: 6 tarjetas y total inicial USD 350;
- las dos piezas comparten marca, membrete y pie.

`verificar-sitio.py` — el sitio nuevo, medido con el mismo motor que mide al cliente y a los pares:

| Señal | Sitio actual | Sitio nuevo |
|---|---|---|
| Idioma declarado | `ar` | `es-AR` |
| Descripción para Google | 0 caracteres | 150 caracteres |
| Open Graph / Twitter | 0 / 0 | 10 / 4 |
| URL canónica | — | sí |
| Datos estructurados | 0 bloques | Psychologist + Person + FAQPage |
| Encabezados h1 / h2 | 1 / 1 | 1 / 7 |
| Imágenes sin texto alternativo | 5 de 13 | 0 de 4 |
| Carga diferida / srcset | 0 / 0 | 3 / 2 |
| Llamados a WhatsApp | 0 | 14 |
| Mapa del sitio | 404 | 200 |
| Peso por visita | 3.555,8 KB en 18 archivos | 724,6 KB en 5 archivos |

Además: render real sin desborde horizontal a 1440, 1024, 768, 390 y 360 px de ancho.

## Lo que hay que confirmar con el cliente antes de publicar

Estos cuatro datos **no figuran en ninguna fuente** y por eso el sitio no los inventa.
Están también en la propuesta, como «cuatro datos que no puedo inventar»:

1. **Correo de contacto.** El sitio actual no publica ninguno. El sitio nuevo no lo inventa:
   el contacto es WhatsApp, teléfono, dirección y la agenda de Doctoralia.
2. **Días y horarios de atención.** Hoy no figuran en ninguna parte.
3. **Documentación para reintegro.** El perfil de Doctoralia dice «no se aceptan coberturas
   médicas: sólo pacientes particulares». El sitio nuevo dice exactamente eso y ofrece
   consultar por WhatsApp. **Si emite factura para reintegro, hay que corregirlo.**
4. **Qué plataforma usar para reservar turnos.** El sitio nuevo convive con la agenda actual
   de Doctoralia; el módulo M3 la reemplaza o la sincroniza con Google Calendar.

Y una decisión de producto: **no hay ninguna foto del profesional**. Las 4 fotos del
consultorio son reales y se usan; el retrato no se puede inventar.

## Lo que se descartó, y por qué

Llegaron dos maquetas HTML de una herramienta externa como «sugerencias de mejora».
Se usaron como referencia de estructura, **no como fuente de datos**: contenían métricas
inventadas (seguidores, lecturas, recomendaciones de colegas con nombre y apellido), una
copia de la interfaz de LinkedIn como sitio del cliente y un error de transcripción en el
número de trámite del certificado (decían `08-0111-22`; el certificado dice `58-0111-22`).
El detalle completo está en `00-auditoria/fuentes.md`.

## Cómo se relaciona con el sistema de propuestas

Este repositorio es un **lead de un solo cliente**, derivado de `~/propuestas-clientes`.
Reusa su marca (`brand/`), su paginador calibrado (`templates/print.js`) y su verificación
en Chrome headless. Los cambios que se hicieron acá y conviene devolver al sistema general:

- `templates/print.js`: secciones dinámicas — la sección **Comparativo verificado** entra
  sólo si `config.comparativo` tiene filas, y los hallazgos aceptan `prioridad`.
- `brand/brand.css`: estilos de prioridad, tabla comparativa, indicadores y layout de la
  propuesta comercial.
- `scripts/generate.py`: acepta `--config`, `--informe` y `--propuesta`, y arma la propuesta
  narrativa completa (comparativo, conversión a pesos, banda de antes/después).

## Reproducibilidad y honestidad

- **Nada visual fuera de `brand/`.**
- **`config.json` es el contrato.** Los documentos son la salida: no se editan a mano.
- **Los totales se calculan, no se escriben.** El informe, los escenarios, la tabla de
  inversión y el selector derivan del mismo `config.json`.
- **Cada afirmación está marcada.** `[MEDIDO]` si sale de una medición, `[INFERIBLE]` si es
  una estimación, `[NO VERIFICADO]` si no se pudo comprobar. Lo no verificado no se afirma:
  LinkedIn responde con muro de registro (HTTP 999), así que no hay una sola cifra de esa red
  en este repositorio.
