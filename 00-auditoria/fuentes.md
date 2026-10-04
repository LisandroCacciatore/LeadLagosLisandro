# Fuentes y verificación

Auditoría del **Lic. Lisandro Lagos** — medición del **4 de octubre de 2026**.
Ledger de lo que se miró, lo que se midió y lo que **no** se pudo verificar.

Regla: cada número que aparece en el informe o en la propuesta sale de acá.
Lo que no se pudo comprobar queda declarado como **[NO VERIFICADO]**, no estimado.

## 1. Fuente principal — el sitio del cliente

[1] https://www.liclisandrolagos.com/ — HTML servido, medido con `scripts/medir.py`.
También se capturó su render: `00-auditoria/capturas/actual-desktop.png` y `actual-mobile.png`.
Resultado crudo: `00-auditoria/evidencia-web.json` (clave `cliente`).

Datos transcriptos del propio sitio:
- Nombre y profesión: «Lic. Lisandro Lagos», «Psicoanalista, Psicólogo».
- Núm. Colegiado 5677. Dirección: Buenos Aires 1110, 2000 Rosario, Santa Fe.
- Teléfonos publicados: +54 341 301-2482 y +54 9 341 301-2482.
- Precios publicados: Consulta online de Psicoanálisis (desde $60.000), Primera sesión de
  Psicología ($60.000), Psicoanálisis ($60.000).
- Cinco opiniones de pacientes, todas atribuidas a «Paciente».
- Trayectoria y formación: 13 entradas, transcriptas al sitio nuevo sin agregados.
- Plataforma: el HTML carga `/websites/14/assets/css/themes/theme-brown_beige.css` y el pie
  dice «DocPlanner.com © 2026».

## 2. Imágenes — del propio profesional

Las fotos y el certificado salen del sitio del cliente y de su perfil público de Doctoralia.
Se copiaron **sin retoque** a `00-auditoria/fuentes/` y se versionan como evidencia.
Las variantes optimizadas que usa el sitio nuevo las produce `scripts/preparar-assets.py`.

- `foto-a.jpg`, `a4-1.jpg`, `a4-2.jpg`, `perfil.jpg` — fotos del consultorio. **No hay ningún
  retrato del profesional**: la imagen que la plataforma usa como foto de perfil (en el círculo
  del encabezado) es una foto de la sala.
- `a4-3.jpg` y `consultorio.jpg` — el certificado de habilitación. Datos transcriptos al sitio
  nuevo y contrastados a ojo sobre la imagen: Habilitación Provincial de Consultorio
  **N° 084-60296**, Ley 9.847 (modificatoria Ley 10.169), Resolución de Directorio **ACTA N° 958**,
  **trámite 58-0111-22**, domicilio habilitado Buenos Aires 1110 Piso 4 Dto 8, **vigencia hasta el
  16 de agosto de 2027**, firmado por el presidente del Colegio, Ps. Nahuel Castillo.

## 3. Perfil profesional — Doctoralia

[2] https://www.doctoraliar.com/perfil/lisandro-lagos
- 5 opiniones, puntaje 5,0. «Tiempo de respuesta aproximado»: **vacío**.
- «No se aceptan coberturas médicas. Este especialista sólo acepta pacientes particulares.»
- Precios: tres ítems a $60.000 (mismos que el sitio propio).
- 5 fotos en la galería, 13 entradas de formación, 37 enfermedades tratadas declaradas.

## 4. Comparativo — colegas de la misma categoría en Rosario

[3] https://www.doctoraliar.com/psicoanalista/rosario
[4] https://www.doctoraliar.com/psicologo/rosario
[5] https://www.doctoraliar.com/perfil/&lt;slug&gt; — un perfil por colega.

35 perfiles relevados, 23 con al menos una opinión, 12 sin ninguna.
Mediana de opiniones de los que tienen: **14**. Máximo: **142**. 7 con dominio propio.
Volcado completo en `00-auditoria/evidencia-doctoralia.json`.

Dominios propios medidos con la misma herramienta (`00-auditoria/pares.txt`, resultado en
`evidencia-web.json`):

| Colega | Sitio | Estado |
|---|---|---|
| Lucía Ramos | luciaramospsicologa.com | 200 OK |
| Maricel Gómez Scavuzzo | maricelgomezscavuzzo-psicologa.com | 200 OK |
| Mariela Reinaudi | mariela-reinaudi.com | 200 OK |
| Marcos M. Fleitas | licmarcosfleitas.com | **[NO VERIFICADO]** — 429 y error de TLS |
| Jesica Díaz Zenoff | jesicadiazzenoff.com.ar | el dominio no resuelve |
| Martín Podestá | martinpodesta.com | el dominio no resuelve |
| Federico Layacona | — | el perfil declara un sitio con formato inválido: no medible |

## 5. Peso real de la página

Medido con `scripts/pesar.py`, que resuelve los recursos que el HTML referencia.
- Sitio actual: **3.555,8 KB en 18 archivos** (incluye 703 KB y 602 KB de fotos sin optimizar,
  215 KB de CSS y 199 KB de Summernote, un editor de texto enriquecido).
- Sitio nuevo: **724,6 KB en 5 archivos**.

## 6. Tipo de cambio

[6] https://dolarapi.com/v1/dolares — consultado el 4 de octubre de 2026.
Referencia usada: dólar bolsa, venta **$1.551,90**. Es la única cifra externa al cliente que se
usa para traducir dólares a pesos, y está citada en la propuesta.

## Lo que NO se pudo verificar

- **LinkedIn** ([7] https://www.linkedin.com/in/lisandro-lagos-2935b8154/): responde con muro de
  registro (HTTP 999). Se declara **[NO VERIFICADO]**: no se afirma nada sobre seguidores,
  contactos ni publicaciones. Cualquier número de esa red que aparezca en un documento es
  inventado y no fue usado.
- **Estadísticas de visita del sitio**: sin acceso. Todos los impactos en consultas son
  **[INFERIBLE]** y están marcados como tales.
- **Agenda real, tasa de ausencias y facturación** del profesional.
- **Google Business Profile** y otras redes.
- **Email de contacto**: el sitio actual no publica ninguno. El sitio nuevo no lo inventa.

## Fuentes descartadas a propósito

Se recibieron dos maquetas HTML de una herramienta externa como «sugerencias de mejora». No se
usaron como fuente: contenían datos inventados que este repositorio no reproduce.

| Afirmación de la maqueta | Qué dice la fuente real |
|---|---|
| «5.0 en Doctoralia» con perfil propio | El perfil existe, pero no está enlazado desde el sitio actual (sí lo estaba el enlace, sin afirmar puntaje) |
| Facturas para reintegro en prepagas: OSDE, Swiss Medical, Galeno, Medifé, Sancor | Doctoralia: «No se aceptan coberturas médicas. Sólo pacientes particulares» |
| «Lunes a viernes de 09:00 a 20:00» | No figura en ninguna fuente |
| contacto@lisandrolagos.com.ar | No figura en ninguna fuente |
| «+15 años de trayectoria» | Consultorio privado desde 2010: **[INFERIBLE]**, con la base declarada |
| Certificado «ACTA Nº 958, trámite 08-0111-22» | El certificado real dice **trámite 58-0111-22** |
| «1.840 seguidores», «+500 contactos», «4 ensayos publicados», lecturas y recomendaciones | **[NO VERIFICADO]** — LinkedIn no permite la lectura |
| Recomendaciones de «Dr. Martín D. Fernández» y «Lic. Cecilia Valenzuela» | Personas no verificables: no se usaron |
| Copia de la interfaz de LinkedIn como sitio del cliente | Se descartó: la marca es de un tercero y las métricas eran falsas |

Lo que de esas maquetas **sí** resultó cierto y se aprovechó: la dirección, la matrícula, los
honorarios, la noción de «biblioteca y diván» (verificada en las fotos reales) y la estructura
editorial de las secciones.
