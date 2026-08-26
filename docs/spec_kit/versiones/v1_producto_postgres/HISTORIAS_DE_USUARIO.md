# Historias de usuario — API Facturas (Versión 1: producto)

> Proyecto Diseño de Software · USB-MED. Las MISMAS exigencias de la
> [especificación](2_spec.md), expresadas en el formato de **historias de
> usuario** del curso (tarjeta + descripción + criterios de aceptación).
> La trazabilidad es de ida y vuelta: cada historia apunta a su RF de
> `2_spec.md` y a su contrato de `6_contracts.md`; si una historia y la
> spec se contradicen, se corrige UNA de las dos en el mismo commit —
> nunca conviven en desacuerdo.

## Historial de revisiones

| Fecha | Versión | Descripción | Autor | Revisor |
|---|---|---|---|---|
| 21/08/2026 | 1.0 | Historias de la v1 (producto) en el formato del curso | Carlos Arturo Castro Castro | — |

## Introducción

El dominio: una comercializadora factura productos a sus clientes. La
**versión 1** construye únicamente el catálogo de productos como API
(sin pantallas: el front llega en la v7 — por eso estas historias no
traen figuras; la "pantalla" de la v1 es Swagger en
`http://localhost:8055/swagger`, y quien la consume es una persona
usando esa interfaz o el front futuro). Los personajes: **Marcela Ríos**
(auxiliar de inventario) y **Álvaro Mejía** (administrador).

---

## Historia de Usuario 1

| | | |
|---|---|---|
| **Número:** 1 | **Usuario:** Marcela Ríos — auxiliar de inventario | **Iteración asignada:** v1 |
| **Nombre historia:** Consultar el catálogo de productos | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Alta | **Riesgo en desarrollo:** Bajo | |
| **Puntos estimados:** 1 | **Horas estimadas:** 6 | |
| **Programador responsable:** el estudiante (reconstrucción guiada — ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Marcela Ríos, como auxiliar de inventario de la comercializadora,
quiero consultar el catálogo completo de productos —y poder limitar
cuántos me trae la consulta— para revisar qué hay registrado y con qué
existencias, sin abrir la base de datos.

**Observaciones:**
Trazabilidad: RF1 de [2_spec.md](2_spec.md) · contrato §2 de
[6_contracts.md](6_contracts.md) · smoke test §2.2 de
[7_quickstart.md](7_quickstart.md).

**Criterios de aceptación:**
1. `GET /api/producto` responde 200 con el sobre
   `{tabla, limite, total, datos}` y los **8 productos semilla**.
2. `GET /api/producto?limite=3` responde exactamente 3 (total: 3).
3. Si la tabla está vacía, responde **204** sin cuerpo (vacío no es error).
4. Con `limite=0` o negativo responde **400** con
   `{estado, mensaje, detalle}` (regla de negocio, no de forma).

---

## Historia de Usuario 2

| | | |
|---|---|---|
| **Número:** 2 | **Usuario:** Marcela Ríos — auxiliar de inventario | **Iteración asignada:** v1 |
| **Nombre historia:** Consultar un producto por su código | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Alta | **Riesgo en desarrollo:** Bajo | |
| **Puntos estimados:** 1 | **Horas estimadas:** 4 | |
| **Programador responsable:** el estudiante (ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Marcela Ríos, como auxiliar de inventario, quiero buscar un producto
por su código exacto para verificar su nombre, su stock y su valor
unitario antes de facturarlo o de corregirlo.

**Observaciones:**
Trazabilidad: RF2 de [2_spec.md](2_spec.md) · contrato §3 de
[6_contracts.md](6_contracts.md).

**Criterios de aceptación:**
1. `GET /api/producto/PR001` responde 200 con los 4 campos del producto
   (código, nombre, stock, valor unitario).
2. Con un código inexistente (`PR999`) responde **404** con el sobre
   `{estado, mensaje: "Producto no encontrado.", detalle}` — nunca un
   error a secas ni un 200 vacío.

---

## Historia de Usuario 3

| | | |
|---|---|---|
| **Número:** 3 | **Usuario:** Marcela Ríos — auxiliar de inventario | **Iteración asignada:** v1 |
| **Nombre historia:** Registrar un producto nuevo | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Alta | **Riesgo en desarrollo:** Medio | |
| **Puntos estimados:** 2 | **Horas estimadas:** 8 | |
| **Programador responsable:** el estudiante (ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Marcela Ríos, como auxiliar de inventario, quiero registrar un
producto nuevo con su código, nombre, stock inicial y valor unitario,
para que quede disponible en el catálogo — y quiero que el sistema me
rechace datos incompletos o absurdos ANTES de guardarlos.

**Observaciones:**
Trazabilidad: RF3 de [2_spec.md](2_spec.md) · contrato §4 de
[6_contracts.md](6_contracts.md). El rechazo temprano es la petición
`ProductoCrear` (la frontera de entrada — [3_plan.md](3_plan.md) §4.2).

**Criterios de aceptación:**
1. `POST /api/producto` con los 4 campos válidos responde 200 con
   `{estado, mensaje: "Producto creado exitosamente."}` y el producto
   queda consultable (historia 2).
2. Si falta cualquier campo, o el stock o el valor son negativos,
   responde **422** con la lista `errores[]` — y la petición **nunca
   llega a la base de datos**.
3. Un stock con decimales (7.5) responde **422**: el tipo también es regla.
4. Un código ya existente responde **500** con el error de llave primaria
   del motor en `detalle` (la BD es la última defensa).

---

## Historia de Usuario 4

| | | |
|---|---|---|
| **Número:** 4 | **Usuario:** Marcela Ríos — auxiliar de inventario | **Iteración asignada:** v1 |
| **Nombre historia:** Reemplazar la ficha completa de un producto | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Media | **Riesgo en desarrollo:** Medio | |
| **Puntos estimados:** 2 | **Horas estimadas:** 6 | |
| **Programador responsable:** el estudiante (ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Marcela Ríos, como auxiliar de inventario, quiero reemplazar la
ficha COMPLETA de un producto (nombre, stock y valor, todos a la vez)
cuando llega información nueva del proveedor, entendiendo que reemplazar
significa entregar todos los datos — no "dejar lo que estaba".

**Observaciones:**
Trazabilidad: RF4 de [2_spec.md](2_spec.md) · contrato §5 de
[6_contracts.md](6_contracts.md). Esta historia y la 5 forman la
**pareja didáctica** PUT/PATCH del curso.

**Criterios de aceptación:**
1. `PUT /api/producto/{codigo}` con los 3 campos responde 200 con
   `{estado, mensaje, filasAfectadas: 1}`.
2. Si falta CUALQUIER campo responde **422** — un reemplazo a medias no
   existe.
3. Con un código inexistente responde **404**.

---

## Historia de Usuario 5

| | | |
|---|---|---|
| **Número:** 5 | **Usuario:** Marcela Ríos — auxiliar de inventario | **Iteración asignada:** v1 |
| **Nombre historia:** Corregir un solo dato de un producto | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Media | **Riesgo en desarrollo:** Bajo | |
| **Puntos estimados:** 1 | **Horas estimadas:** 4 | |
| **Programador responsable:** el estudiante (ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Marcela Ríos, como auxiliar de inventario, quiero corregir UN dato
puntual (por ejemplo, solo el stock después del conteo físico) sin tener
que reescribir la ficha entera del producto.

**Observaciones:**
Trazabilidad: RF5 de [2_spec.md](2_spec.md) · contrato §6 de
[6_contracts.md](6_contracts.md). El contraste con la historia 4 es
verificable: el MISMO body `{"stock": 17}` falla en PUT (422) y funciona
en PATCH (200).

**Criterios de aceptación:**
1. `PATCH /api/producto/{codigo}` con un subconjunto de campos responde
   200 con `filasAfectadas: 1`, y SOLO cambian los campos enviados.
2. Con el body vacío `{}` responde **400** ("no se envió ningún campo") —
   es decisión de negocio, no de forma.
3. Con un código inexistente responde **404**.
4. El body `{"stock": 17}` responde 422 en PUT y 200 en PATCH (la pareja).

---

## Historia de Usuario 6

| | | |
|---|---|---|
| **Número:** 6 | **Usuario:** Marcela Ríos — auxiliar de inventario | **Iteración asignada:** v1 |
| **Nombre historia:** Retirar un producto del catálogo | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Media | **Riesgo en desarrollo:** Bajo | |
| **Puntos estimados:** 1 | **Horas estimadas:** 4 | |
| **Programador responsable:** el estudiante (ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Marcela Ríos, como auxiliar de inventario, quiero retirar del
catálogo un producto que ya no se comercializa, y que el sistema me diga
claramente si intento retirar algo que no existe.

**Observaciones:**
Trazabilidad: RF6 de [2_spec.md](2_spec.md) · contrato §7 de
[6_contracts.md](6_contracts.md). Cuando existan facturas (v2), un
producto facturado no podrá borrarse: la llave foránea del motor lo
rechazará con 500 — esa consecuencia se documentará en su versión.

**Criterios de aceptación:**
1. `DELETE /api/producto/{codigo}` responde 200 con
   `{estado, mensaje, filasEliminadas: 1}` y el producto deja de existir
   (la historia 2 responde 404 para ese código).
2. Repetir el DELETE responde **404** — borrar dos veces no es idempotente
   en el mensaje: la segunda vez ya no había nada que borrar.

---

## Historia de Usuario 7

| | | |
|---|---|---|
| **Número:** 7 | **Usuario:** Álvaro Mejía — administrador | **Iteración asignada:** v1 |
| **Nombre historia:** Verificar que el servicio está disponible | | |
| **Diseñada por:** Carlos Arturo Castro Castro | | |
| **Prioridad:** Baja | **Riesgo en desarrollo:** Bajo | |
| **Puntos estimados:** 1 | **Horas estimadas:** 2 | |
| **Programador responsable:** el estudiante (ver [GUIA_IA1](GUIA_IA1.md)) | | |

**Descripción:**
Yo, Álvaro Mejía, como administrador de la comercializadora, quiero
levantar todo el sistema con UN solo comando y tener una dirección de
diagnóstico que me diga si el servicio está vivo y qué versión corre,
para no depender de nadie técnico cada vez que algo parezca caído.

**Observaciones:**
Trazabilidad: RF7 de [2_spec.md](2_spec.md) · contrato §1 de
[6_contracts.md](6_contracts.md) · Artículo 4 de la
[constitución](../../1_constitution.md) ("un solo comando").

**Criterios de aceptación:**
1. `docker compose up -d --build` deja base de datos y API funcionando
   sin ningún paso adicional.
2. `GET /` responde 200 con `{mensaje, version: "v1", contratos}`.
3. La documentación interactiva vive en `/swagger` y permite probar
   todos los endpoints de estas historias sin herramientas externas.

---

## Referencias

1. Formato de tarjeta: *Historias de usuario — micro proyecto gestión
   del desempeño v2.5* (USB-MED), adaptado: en un proyecto SIN front,
   las "figuras" se sustituyen por los contratos HTTP exactos.
2. En este kit: [2_spec.md](2_spec.md) (los RF y criterios en formato
   spec) · [6_contracts.md](6_contracts.md) (los formatos exactos) ·
   [7_quickstart.md](7_quickstart.md) (los criterios ejecutados como
   smoke test).
