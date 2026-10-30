# Tutorial — Publicar el sistema en Render

**Hasta aquí el proyecto corrió en su máquina**, con un solo `docker compose up`:
cuatro contenedores que nacen juntos y mueren juntos. **Aquí sale a internet**, y
lo primero que cambia es que las piezas dejan de vivir en la misma casa.

| La pieza | Dónde va a quedar | Quién la ejecuta |
|---|---|---|
| **La base de datos** — PostgreSQL | **Neon**, Frankfurt | un servicio administrado: nadie instala nada |
| **La API** — C# / ASP.NET Core | **Render** | una imagen Docker que **construye Render** |
| **El front** — Python / Flask | **Render** | otra imagen, **otro servicio** |

> **Tres proveedores para un solo sistema, y eso no es un capricho del
> tutorial:** es lo que ocurre cuando las piezas se hablan por contratos. El
> front no sabe que la API es de C#; la API no sabe que la base de datos está
> en otra empresa. **Si estuvieran enredadas por dentro, esto sería imposible.**

### Lo que cuesta: nada, y conviene saber por qué

| | Lo que da gratis | La letra menuda |
|---|---|---|
| **Neon** | 1 GB de almacenamiento, hasta 2 CU | **Se apaga sola** cuando nadie la usa, y despierta con la primera consulta |
| **Render** | 750 horas de instancia al mes, `0.1 CPU` · `512 MB` | **Se duerme a los 15 minutos** sin visitas. **Las 750 horas son de la cuenta**, repartidas entre todos sus servicios |

> **Y por qué la base de datos NO va en Render**, que también regala una:
> **el PostgreSQL gratuito de Render se borra a los 30 días.** Para un curso
> que dura un semestre, eso es perder la base de datos a mitad de camino.
> **Neon no caduca.**

### Lo que este tutorial NO publica, y hay que decirlo

**SQL Server se queda en su máquina.** El proyecto habla con dos motores —ése
es el interruptor `MOTOR_BD` de la v4— pero **no hay SQL Server administrado
gratis en ninguna parte**. El interruptor sigue existiendo y sigue
funcionando; lo que no hay es dónde publicarlo sin pagar.

> **Eso tampoco es un contratiempo: es información del oficio.** Lo que se
> puede publicar gratis no lo decide el diseño de la aplicación, **lo decide el
> mercado de hospedajes del año en que uno esté.**

### Antes de empezar

| | |
|---|---|
| **El repositorio en GitHub** | Público. Render lo clona; **no lee su disco** |
| **El `Dockerfile` de producción** | **Ya está en el repositorio** (`api_facturas/Dockerfile.produccion`). El paso 3 lo lee renglón por renglón |
| **Tarjeta de crédito** | **Ninguna.** Ni Neon ni Render la piden para el plan gratuito |
| **Docker en su máquina** | No hace falta **para publicar**. Hace falta para probar antes de publicar, que es lo sensato |

### Los pasos

| | Qué se hace | Dónde |
|---|---|---|
| **1** | La base de datos | Neon |
| **2** | El esquema y los datos | Neon |
| **3** | La imagen de producción de la API, leída | su editor |
| **4** | El servicio de la API | Render |
| **5** | Las variables de entorno de la API | Render |
| **6** | El front en Flask | Render |
| **7** | La prueba del sistema completo | el navegador |

---

## Paso 1 — La base de datos en Neon

### 1.1 · La cuenta

```
https://neon.com
```

**`Sign up`**, y ofrece GitHub, Google o correo.

> **Hágalo en una ventana de incógnito.** No es paranoia: si el navegador tiene
> sesión abierta con varias cuentas de GitHub, el registro se engancha con la
> que no era — y uno se entera tres pasos después, cuando ya hay cosas creadas
> en el sitio equivocado. **En incógnito no hay sesión previa que lo meta donde
> no quiere.**

### 1.2 · El proyecto

![El formulario de proyecto nuevo en Neon](docs/tutorial_render/img/01_neon_crear_proyecto.png)

**Dos campos y una lista de interruptores:**

| | Qué poner | Por qué |
|---|---|---|
| **Nombre** | `bdfacturas-diseno4` | Es el nombre del proyecto, no el de la base de datos. La base de datos se va a llamar `neondb` |
| **`Region`** | **`AWS Europe Central 1 (Frankfurt)`** | **Donde quede la base de datos van a quedar los demás servicios.** Cada salto entre continentes se le suma a cada consulta |
| **`Services`** | **Solo `Postgres database`** | Los otros cinco —`Object storage`, `Functions`, `AI gateway`, `Realtime`, `Better Auth`— **se quedan apagados.** Este proyecto no los usa |

> **El recuadro negro sobre el globo dice lo que da el plan gratuito:**
> *1 GB storage · **Scales to zero when inactive** · Autoscaling up to 2 CU ·
> 10 branches per project*.
>
> **«Scales to zero» es la parte que hay que entender**: cuando nadie la usa,
> la base de datos **se apaga** y deja de consumir. La primera consulta después
> de un rato tarda unos segundos **porque está despertando**, no porque algo
> esté mal.

**`Create project`.**

### 1.3 · Creado — y una oferta que aquí NO se acepta

![El proyecto creado en 762 milisegundos](docs/tutorial_render/img/02_neon_proyecto_creado.png)

```
Your new project was created in 762 ms
```

**Neon ofrece en seguida un bloque de texto** bajo el título *«Set up Neon with
your coding agent»*, para pegárselo a una herramienta de IA.

> **No lo use.** Ese texto le dice a un agente que instale `neon`, que corra
> `neon init` y `neon deploy`, y que **conecte la aplicación por su cuenta** —
> pensando en un proyecto de Node que todavía no existe.
>
> **Aquí la aplicación ya está escrita**, y lo que se va a conectar es una API
> de C# con una cadena de conexión que usted va a leer y entender. **Dejar que
> una herramienta lo haga sola es saltarse justo lo que este tutorial enseña.**

**`Go to project`.**

### 1.4 · El tablero, leído

![El tablero del proyecto en Neon](docs/tutorial_render/img/03_neon_tablero.png)

**La columna de la derecha es la ficha técnica de lo que acaba de crear**, y
vale leerla entera una vez:

| Lo que dice | Qué significa |
|---|---|
| **`Branch: production`** · `Expires: Never` | Neon tiene **ramas**, como git: se puede sacar una copia de la base de datos para probar algo. La principal se llama `production` y **no caduca** |
| **`Region: AWS Europe Central 1`** | Frankfurt, como se pidió |
| **`Plan: Free plan`** | El gratuito |
| **`IP restrictions: None set`** | **Cualquiera con la contraseña entra, desde donde sea.** Es lo normal en Neon —está hecha para que le hablen desde afuera—, y por eso **la contraseña es toda la puerta** |
| **`Default compute: 0.25 ↔ 2 CU`** | Arranca con un cuarto de unidad de cómputo y crece hasta 2 si hace falta. Un cuarto es ~0,25 de CPU y 1 GB de RAM: **sobra** |
| **`History retention: 6 hours`** | Puede devolver la base de datos a **cualquier instante de las últimas seis horas** |
| **`Version: 18`** | **PostgreSQL 18** |
| **`Storage: 0 kB`** | **Todavía no hay nada adentro.** Eso lo arregla el paso 2 |

> **`Version 18` contra el `postgres:16-alpine` del `docker-compose.yml`:** el
> esquema del proyecto no usa nada exclusivo de una versión, **así que debería
> cargar sin problema** — pero eso es un supuesto, no un hecho. **Se comprueba
> al importar**, y si algo falla, el mensaje lo dirá.

---

## Paso 2 — El esquema y los datos

**En el menú de la izquierda, bajo `Postgres database`: `SQL Editor`.**

### 2.1 · El editor NO llega vacío

![El editor de SQL con el ejemplo que trae Neon](docs/tutorial_render/img/04_neon_sql_editor.png)

**Trae un ejemplo de Neon** que crea una tabla llamada `playing_with_neon`. No
estorba, pero no es lo nuestro: hay que **reemplazarlo**, no escribir debajo.

Arriba, compruebe dos cosas antes de seguir:

| | |
|---|---|
| **`neondb`** | la base de datos donde van a caer las tablas |
| **`Primary`** | la única rama que existe |

> **Y si dice `Idle` en vez de `Active`, no pasa nada:** es la base de datos
> dormida. **La primera consulta la despierta.**

### 2.2 · Cómo se copia un archivo de 1.106 renglones

**El archivo es `db\bdfacturas_postgres.sql`** y no cabe en una pantalla. Se
puede abrir en VS Code y hacer `Ctrl+A`, `Ctrl+C` —pero hay una forma de un
solo renglón, **desde PowerShell**:

```powershell
Get-Content "C:\Users\fcl\OneDrive\Desktop\proyectos_usbmed\2026_2\proyecto_diseno_de_software4\db\bdfacturas_postgres.sql" -Raw | Set-Clipboard
```

| La parte | Qué hace |
|---|---|
| `Get-Content <ruta>` | **lee el archivo** |
| **`-Raw`** | lo entrega como **un solo texto**. Sin esta palabra lo entregaría renglón por renglón, y el pegado saldría desarmado |
| **`\| Set-Clipboard`** | mete ese texto **en el portapapeles**, listo para `Ctrl+V` |

**No responde nada, y así debe ser:** en PowerShell el silencio es éxito. Si la
ruta estuviera mal, habría un error en rojo.

> **El error que cae aquí, y que cayó escribiendo este tutorial:** copiar **la
> ruta** y pegarla en el editor de Neon. Queda un renglón con
> `C:\Users\...\bdfacturas_postgres.sql` adentro, que para PostgreSQL no
> significa nada.
>
> **La ruta es el papelito donde está anotada la dirección de la casa; el
> archivo es la casa.** Ese comando existe justamente para no confundirlos:
> `Get-Content` va a esa dirección y trae lo que hay adentro.

### 2.3 · Pegar — y un aviso que asusta sin motivo

**Clic en el editor** → `Ctrl+A` (para que lo pegado **sustituya** el ejemplo)
→ `Ctrl+V`.

![El script completo pegado en el editor](docs/tutorial_render/img/06_neon_script_pegado.png)

**Abajo aparece esto:**

```
This query will still run OK, but the last 32419 characters
will be truncated from query history
```

> **Se ejecuta completo.** Lo que Neon recorta es **la copia que guarda en su
> historial**, para no almacenar 60 KB de texto cada vez que usted oprime
> `Run`. **El script entero sí llega a la base de datos.**

**`Run`.**

### 2.4 · Lo que contesta

![El resultado: 46 sentencias ejecutadas](docs/tutorial_render/img/07_neon_script_ejecutado.png)

```
Connected (46 queries)        231ms
1: CREATE   2: CREATE   ...   12: CREATE   13: INSERT   ...
Statement executed successfully
```

| Lo que dice | Qué es |
|---|---|
| **46 sentencias** | las 12 tablas, el *trigger*, los procedimientos y los `INSERT` de los datos semilla |
| **12 `CREATE`** seguidos | las 12 tablas, en orden: primero las que no dependen de nadie |
| **231 ms** | **desde Colombia hasta Frankfurt**, creando una base de datos entera |

### 2.5 · Comprobar, que es más seguro que confiar

**Borre el editor y pegue esto:**

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

![Las doce tablas listadas](docs/tutorial_render/img/08_neon_doce_tablas.png)

**`12 rows`**, y ahí están: `cliente`, `empresa`, `factura`, `persona`,
`producto`, `productosporfactura`, `rol`, `rol_usuario`, `ruta`, `rutarol`, y
las dos que no caben en la pantalla.

> **Y aquí conviene aclarar algo que confunde**, porque el archivo que acaba de
> correr **se llama `bdfacturas_postgres.sql` y habla por dentro de
> `bdfacturas_postgres_local`** —que es el nombre que tiene la base de datos
> **en su máquina**, la que crea Docker.
>
> **Ese nombre aquí no se usa para nada.** El script **no crea ninguna base de
> datos**: solo crea tablas **adentro de la que ya existe**, que en Neon se
> llama `neondb`. Por eso el mismo archivo sirve en los dos sitios sin cambiar
> una letra.

---

> **En construcción.** Los pasos 3 a 7 se escriben a medida que se ejecutan:
> este documento no describe nada que no se haya hecho de verdad.
