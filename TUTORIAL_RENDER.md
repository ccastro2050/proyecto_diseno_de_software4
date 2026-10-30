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
| **3** | La cadena de conexión — y comprobarla **antes** de publicar | Neon · su máquina |
| **4** | La imagen de producción de la API, leída | su editor |
| **5** | El servicio de la API | Render |
| **6** | Las variables de entorno de la API | Render |
| **7** | El front en Flask | Render |
| **8** | La prueba del sistema completo | el navegador |

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
| **`Region`** | **`AWS Europe Central 1 (Frankfurt)`** | **Donde quede la base de datos van a quedar los demás servicios.** Ver el recuadro de abajo |
| **`Services`** | **Solo `Postgres database`** | Los otros cinco —`Object storage`, `Functions`, `AI gateway`, `Realtime`, `Better Auth`— **se quedan apagados.** Este proyecto no los usa |

> **El recuadro negro sobre el globo dice lo que da el plan gratuito:**
> *1 GB storage · **Scales to zero when inactive** · Autoscaling up to 2 CU ·
> 10 branches per project*.
>
> **«Scales to zero» es la parte que hay que entender**: cuando nadie la usa,
> la base de datos **se apaga** y deja de consumir. La primera consulta después
> de un rato tarda unos segundos **porque está despertando**, no porque algo
> esté mal.

#### ¿Y por qué Frankfurt, estando en Colombia?

**La regla que de verdad importa es otra: la API y la base de datos tienen que
quedar en la MISMA región.** Cuál sea esa región pesa mucho menos — y conviene
verlo con números en vez de creerlo.

**Medido el 29 de octubre de 2026, desde Medellín**, ida y vuelta completa:

| Hasta dónde | Cuánto tardó |
|---|---|
| **Frankfurt** —la API de este tutorial— | **0,28 – 0,30 s** |
| **Virginia** —un servicio de AWS, de referencia— | **0,26 s** |

**Casi lo mismo.** La diferencia entre «al otro lado del Atlántico» y «en el
mismo continente» son **centésimas**, porque de todas formas el tráfico sale
del país por unos pocos cables.

> **Lo que NO es casi lo mismo es separar la API de la base de datos.** Ese
> salto no ocurre una vez: **ocurre varias veces por pantalla.** Una página
> que haga diez consultas, con la base de datos en otro continente, paga el
> viaje diez veces — y ahí sí se nota.

**Entonces, ¿por qué Frankfurt aquí?** Por una razón honesta y poco técnica:
**la cuenta de Render ya tenía un servicio en Frankfurt** —el front de otro
curso— y los servicios de una misma región **se hablan por red privada**. Si
usted empieza de cero, **escoja la región más cercana a sus usuarios** y ponga
todo lo demás ahí.

> **Y ojo con esto, que no tiene vuelta atrás:** la región de un proyecto de
> Neon **se escoge al crearlo y no se cambia después**. Para mudarla hay que
> crear otro proyecto y volver a cargar el esquema.

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

## Paso 3 — La cadena de conexión

**Botón verde `Connect`**, arriba a la izquierda.

![El diálogo Connect, con la contraseña tapada](docs/tutorial_render/img/09_neon_conectar.png)

### 3.1 · Lo que hay que mirar en el diálogo

| Campo | Valor | Qué es |
|---|---|---|
| **Las cuatro pestañas** | `Postgres database` · `Storage` · `Data API` · `Auth` | Formas distintas de llegar a los datos. **La nuestra es la primera**: conexión SQL de toda la vida |
| **`Compute`** | `Primary` · `Idle` | **Está dormida.** No es un problema: la primera consulta la despierta |
| **`Database`** | **`neondb`** | El nombre que Neon le pone. No vale la pena cambiarlo |
| **`Role`** | **`neondb_owner`** | El usuario. En PostgreSQL los usuarios se llaman *roles* |
| **`Reset password`** | | Cambia la contraseña. **Es lo que se usa cuando una clave se filtra** — y al terminar el curso conviene oprimirlo |

### 3.2 · `Connection pooling`: déjelo encendido

Mire lo que le hace al nombre del servidor:

```
ep-weathered-dream-b91narw8-pooler.c-7.eu-central-1.aws.neon.tech
                            ^^^^^^^
                            esto lo agrega el pooling
```

| Sin *pooling* | **Con *pooling*** |
|---|---|
| Cada conexión abre un proceso en la base de datos | **Un intermediario reparte un puñado de conexiones** entre todos |
| Se agota rápido | Aguanta muchos más clientes |

> **Y para esta API es justo lo que hace falta:** abre y cierra conexión **en
> cada petición**. Sin el *pooler*, veinte estudiantes probando a la vez la
> tumban.

### 3.3 · La cadena, y lo que dice el final

```
postgresql://neondb_owner:LA_CLAVE@ep-weathered-dream-b91narw8-pooler.c-7.eu-central-1.aws.neon.tech/neondb
             ?sslmode=require&channel_binding=require
```

| Parte | Qué dice |
|---|---|
| `postgresql://` | El formato estándar de PostgreSQL — **no es el de .NET** |
| `...eu-central-1...` | **Frankfurt.** Ahí queda confirmada la región |
| **`sslmode=require`** | **Cifrado obligatorio.** Esta conexión **sale a internet**: va de Render a Neon, por fuera de cualquier red privada |
| **`channel_binding=require`** | Amarra la autenticación al canal cifrado, para que nadie se interponga |

> **`Hide password` antes de tomar la captura.** El diálogo trae la contraseña
> a la vista, y una captura con la clave adentro **es la clave publicada**: las
> imágenes de este tutorial viven en GitHub igual que el código.
>
> **Copie la cadena con `Copy snippet`, nunca a mano.** Esa contraseña mezcla
> caracteres que se confunden entre sí —`l` con `1`, `O` con `0`— y uno mal
> leído se manifiesta como un error de autenticación **que no dice que el
> problema sea un carácter.**

**Guárdela en un `.txt` fuera del repositorio.** No va a ningún archivo del
proyecto: en el paso 6 se escribe **directamente en el panel de Render**.

### 3.4 · Traducirla al formato de .NET

**Npgsql no entiende `postgresql://`.** Hay que pasarla a pares `Clave=Valor`:

```
Host=ep-weathered-dream-b91narw8-pooler.c-7.eu-central-1.aws.neon.tech;Database=neondb;Username=neondb_owner;Password=SU_CLAVE;SSL Mode=Require
```

| El formato de Neon | **El de .NET** |
|---|---|
| `postgresql://usuario:clave@servidor/base` | Pares `Clave=Valor` separados por `;` |
| `?sslmode=require` | **`SSL Mode=Require`** — con espacio y mayúsculas |
| `&channel_binding=require` | **Se omite.** Npgsql no tiene esa opción: **ya usa amarre de canal por su cuenta** cuando la conexión va cifrada |

### 3.5 · Comprobarla aquí, antes de publicar nada

**Esto es opcional y vale la pena**, porque separa dos preguntas que después se
mezclan: *«¿está mal la cadena?»* y *«¿está mal el hospedaje?»*.

Se construye la imagen de producción y se corre **en su máquina**, apuntando a
Neon:

```powershell
docker build -f api_facturas/Dockerfile.produccion -t apifacturas-prod api_facturas

docker run -d --name prueba-neon -p 18056:18056 `
  -e PORT=18056 `
  -e Motor=postgres `
  -e ConnectionStrings__Postgres="Host=...;Database=neondb;Username=neondb_owner;Password=SU_CLAVE;SSL Mode=Require" `
  -e Jwt__Key="UnaClaveDePruebaDeTreintaYDosCaracteresOMas" `
  -e Jwt__Issuer=ApiFacturas -e Jwt__Audience=FrontFacturas `
  apifacturas-prod
```

| La parte | Qué hace |
|---|---|
| `-e PORT=18056` | **imita lo que hace Render**: imponerle el puerto desde afuera |
| `-e Motor=postgres` | el interruptor de la v4 |
| `-e ConnectionStrings__Postgres=...` | **el doble guion bajo es el `:` de .NET**: equivale a `ConnectionStrings:Postgres` |
| `-e Jwt__Key=...` | `Program.cs` **aborta el arranque** si falta o tiene menos de 32 caracteres |

**Y la prueba que vale**, iniciar sesión —porque eso sí va a la base de datos:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:18056/api/sesion `
  -ContentType "application/json" `
  -Body '{"email":"admin@correo.com","contrasena":"admin123"}'
```

**Lo que contestó:**

```
estado   : 200
mensaje  : Sesion iniciada.
token    : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> **Ese `200` prueba tres cosas de una vez:** la imagen de producción arranca,
> **la cadena llega hasta Frankfurt con TLS**, y los datos semilla están ahí
> —porque el usuario `admin@correo.com` salió de la tabla `usuario` que se
> cargó en el paso 2.
>
> **Si esto funciona y después Render falla, el problema no es el suyo: es la
> configuración del hospedaje.** Eso es lo que compra esta comprobación.

**Al terminar, el contenedor de prueba sobra:**

```powershell
docker rm -f prueba-neon
```

---

## Paso 4 — La imagen de producción, y por qué hubo que escribir otra

**El repositorio tiene dos `Dockerfile` para la misma API**, y conviene saber
por qué antes de decirle a Render cuál usar:

```
api_facturas/
   Dockerfile               <- desarrollo: el que usa docker compose
   Dockerfile.produccion    <- publicado: el que usa Render
```

| | `Dockerfile` (desarrollo) | **`Dockerfile.produccion`** |
|---|---|---|
| **De qué imagen parte** | **SDK**, ~1,3 GB: trae el compilador adentro | **runtime**, la imagen final pesa **367 MB** |
| **Cómo arranca** | `dotnet watch`: **recompila** cuando usted guarda un `.cs` | `dotnet ApiFacturas.dll`: arranca y punto |
| **Dónde está el código** | **montado** por el compose: el contenedor lee su carpeta | **adentro de la imagen**, ya compilado |
| **En qué puerto escucha** | 8055, fijo | **el que imponga el hospedaje** |

> **Y ese último renglón es el que hunde a medio mundo.** Render —como casi
> toda plataforma de contenedores— **impone el puerto** con la variable `PORT`
> y espera que el programa escuche ahí. **ASP.NET Core no lee `PORT`**: lee
> `ASPNETCORE_URLS`. Si nadie traduce, la aplicación arranca viva en otro
> puerto y **la plataforma reporta el servicio como caído.**

**La traducción es el último renglón del archivo:**

```dockerfile
CMD ["sh", "-c", "export ASPNETCORE_URLS=http://0.0.0.0:${PORT:-8055}; exec dotnet ApiFacturas.dll"]
```

| La parte | Qué hace |
|---|---|
| `["sh", "-c", ...]` | **pasa por un shell.** La forma corta —`["dotnet", "ApiFacturas.dll"]`— no lo hace, y entonces `$PORT` llegaría **literal**, con el signo de dólar |
| `${PORT:-8055}` | usa `PORT` **si existe**; si no, el 8055 del proyecto. **La misma imagen sirve en Render y en su máquina** |
| `exec` | hace que `dotnet` sea el proceso 1 del contenedor: así recibe la señal de apagado y **termina ordenado** |

**El estudiante no tiene que escribir nada de esto:** el archivo ya está en el
repositorio. Lo que sí tiene que hacer es **decirle a Render que use ése** —y
eso es el campo `Dockerfile Path` del paso siguiente.

---

## Paso 5 — El servicio de la API en Render

### 5.1 · La cuenta

```
https://render.com
```

**`Get started`**, en una ventana de incógnito. Ofrece GitHub, GitLab,
Bitbucket, Google o correo.

![La pantalla de registro de Render](docs/tutorial_render/img/10_render_registro.png)

> **Si entra con Google** —como se hizo aquí—, **GitHub no queda conectado**, y
> eso cambia una cosa en el paso siguiente: hay que pegar la dirección del
> repositorio a mano. A cambio, no se enreda con tener varias cuentas de GitHub
> abiertas en el navegador.

![El tablero de Render](docs/tutorial_render/img/11_render_tablero.png)

> **Y una advertencia sobre las 750 horas:** son **de la cuenta**, no de cada
> servicio. En este tablero ya había un servicio de otro curso, y al terminar
> este tutorial van a ser **tres**. Como los servicios gratuitos **se duermen a
> los 15 minutos**, solo gastan horas mientras alguien los usa — pero si usted
> deja tres despiertos todo el día, las 750 horas se acaban antes de fin de mes.

### 5.2 · De dónde saca el código

**`+ New`** → **`Web Service`**.

![El menu New de Render](docs/tutorial_render/img/12_render_new_web_service.png)

**Tres pestañas, y aquí se usa la del medio:**

| Pestaña | Qué hace | |
|---|---|---|
| `Git Provider` | Render se conecta a su cuenta y **republica con cada `git push`** | Lo ideal |
| **`Public Git Repository`** | Se le pega la dirección y ya. **Sin conectar cuentas** | **La que usamos** |
| `Existing Image` | Para una imagen ya construida en un registro | No |

![La direccion del repositorio pegada](docs/tutorial_render/img/13_render_repo_publico.png)

```
https://github.com/ccastro2050/proyecto_diseno_de_software4
```

**`Connect`.**

> **Render clona el repositorio y detecta `Docker` solo**, porque encuentra un
> `Dockerfile`. Eso no hay que escogerlo. **Y fíjese en lo que implica: Render
> no lee su disco.** Lo que no esté subido a GitHub, para Render no existe.

### 5.3 · El formulario: cinco campos, y uno se esconde

![Los campos del formulario](docs/tutorial_render/img/15_render_campos.png)

| Campo | Qué poner | Qué es |
|---|---|---|
| **`Name`** | `apifacturas-diseno4` | **Queda en la dirección pública**: `apifacturas-diseno4.onrender.com`. El que trae por defecto es el nombre del repositorio entero |
| `Project` | **vacío** | Solo sirve para agrupar servicios en el tablero |
| `Language` | `Docker` | **Lo detectó solo.** No se toca |
| `Branch` | `main` | La rama que se publica |
| **`Region`** | **`Frankfurt (EU Central)`** | **Donde quedó Neon.** Si lo deja en Oregón, cada consulta cruza Estados Unidos **y** el Atlántico |
| **`Root Directory`** | `api_facturas` | **El que más se olvida.** Sin él, Render trabaja desde la raíz del repositorio, donde no hay ninguna API |
| **`Compute`** | **`$0 / month · Free`** | Viene marcado el de **7 dólares** |

> **Al escribir en `Root Directory`, le va a ofrecer las carpetas de adentro**
> —`api_facturas/Controllers/`, `api_facturas/Modelos/`—. **No escoja ninguna:**
> la que sirve es `api_facturas/`, que ya quedó escrita. Cierre la lista
> haciendo clic afuera.

#### El campo que se esconde

**Apenas se llena `Root Directory`, el campo `Dockerfile Path` desaparece del
formulario.** No se borró: se fue a la sección **`Advanced`**, abajo del todo,
justo encima de `Deploy web service`.

**Ábrala**, porque sin ese campo Render construye el `Dockerfile` **de
desarrollo** —el de `dotnet watch`, que no copia el código adentro— y el
servicio no arranca.

| Campo de `Advanced` | Qué poner | Qué es |
|---|---|---|
| `Docker Build Context Directory` | déjelo en `.` | Desde dónde mira Docker al construir. Ya apunta a `api_facturas/` |
| **`Dockerfile Path`** | **`Dockerfile.produccion`** | Render ya pone el `api_facturas/` adelante. **Es el archivo del paso 4** |
| **`Health Check Path`** | **vacío** | Si le pone una ruta, Render la golpea cada rato y **el servicio no se duerme nunca**: las 750 horas se le van solas |
| `Auto-Deploy` | `On Commit` | Déjelo. Con repositorio público no republica solo, pero no estorba |

### 5.4 · Las variables de entorno — **la tabla para copiar**

**En la sección `Environment Variables`, `Add Environment Variable` cinco
veces.** Esto es lo que lleva cada una:

| KEY | VALUE | Qué es |
|---|---|---|
| `Motor` | `postgres` | **El interruptor de la v4.** Decide el dialecto: `postgres` o `sqlserver` |
| `ConnectionStrings__Postgres` | la cadena del paso 3.4 | **Dónde está la base de datos.** El **doble guion bajo es el `:` de .NET**: equivale a `ConnectionStrings:Postgres` |
| `Jwt__Key` | oprima **`Generate`** | **La clave que FIRMA el token.** `Program.cs` **aborta el arranque** si falta o tiene menos de 32 caracteres |
| `Jwt__Issuer` | `ApiFacturas` | Quién emite el token. Si no coincide con lo que valida la API, todo responde `401` |
| `Jwt__Audience` | `FrontFacturas` | Para quién es el token. Lo mismo |

> **Y una que NO hay que poner, aunque `Program.cs` la exija:**
> `ConnectionStrings__SqlServer`. La API pide que **existan las dos cadenas**
> —aunque solo use una— y la de SQL Server **ya viene en el
> `appsettings.json`** que viaja dentro de la imagen, apuntando a `localhost`.
> **Nunca se abre**, porque `Motor` dice `postgres`.

> **Fíjese dónde quedaron escritos estos valores: en el panel de Render, no en
> un archivo del repositorio.** Ésa es la diferencia entre una contraseña
> publicada y una que no. **El repositorio puede ser público justamente porque
> no lleva ninguno de estos cinco valores adentro.**

**Y ahora sí: `Deploy web service`.**

### 5.5 · La compilación, leída

![El registro de la compilacion](docs/tutorial_render/img/16_render_compilando.png)

**Son las instrucciones del `Dockerfile.produccion`, en orden:**

```
#10 [compilacion 3/6] COPY ApiFacturas.csproj .
#11 [compilacion 4/6] RUN dotnet restore ApiFacturas.csproj
#11 2.891   Restored /origen/ApiFacturas.csproj (in 1.74 sec)
#12 [compilacion 5/6] COPY . .
#13 [compilacion 6/6] RUN dotnet publish ApiFacturas.csproj -c Release -o /publicado --no-restore
```

| Lo que se ve | Qué significa |
|---|---|
| `[compilacion N/6]` | **la etapa que se llama `compilacion`**, la primera del archivo. La segunda aparece después como `[stage-1 ...]` |
| El `.csproj` **antes** que el código | **el orden importa:** mientras no cambien los paquetes, Docker reutiliza la capa de `restore` y reconstruir tarda segundos |
| `warning NU1902` / `NU1903` | avisos de **vulnerabilidades conocidas** en un paquete heredado. **No detienen la compilación**, pero son el tipo de renglón que uno no debería acostumbrarse a ignorar |

### 5.6 · Está viva — y tres renglones que valen el paso entero

![El servicio vivo](docs/tutorial_render/img/17_render_vivo.png)

```
Overriding HTTP_PORTS '8080' and HTTPS_PORTS ''.
   Binding to values defined by URLS instead 'http://0.0.0.0:10000'.
Now listening on: http://0.0.0.0:10000
Hosting environment: Production

==> Your service is live
==> Available at your primary URL https://apifacturas-diseno4.onrender.com
```

| El renglón | Qué prueba |
|---|---|
| **`Overriding HTTP_PORTS '8080'`** | **la imagen de .NET quería el 8080** y el `CMD` del paso 4 la mandó al **10000**, que es el que Render impuso con `PORT`. **Sin esa traducción, aquí decía «caído»** |
| **`Hosting environment: Production`** | lo fijó el `ENV ASPNETCORE_ENVIRONMENT=Production` del `Dockerfile` |
| **47 segundos** | lo que tardó todo: clonar, compilar .NET y arrancar |

### 5.7 · La prueba, desde afuera

```powershell
Invoke-RestMethod https://apifacturas-diseno4.onrender.com/
```

```
mensaje   : API Facturas funcionando
version   : v4
motor     : postgres
```

**Y la que de verdad toca la base de datos:**

```powershell
Invoke-RestMethod -Method Post -Uri https://apifacturas-diseno4.onrender.com/api/sesion `
  -ContentType "application/json" `
  -Body '{"email":"admin@correo.com","contrasena":"admin123"}'
```

```
estado   : 200
mensaje  : Sesion iniciada.
token    : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> **Ese `200` recorrió esto:** su navegador → **Render, Frankfurt** (la API en
> Docker) → **Neon, Frankfurt** (la base de datos). **Dos empresas distintas**,
> y el usuario `admin@correo.com` salió de la tabla que usted cargó en el paso 2.
>
> **La primera llamada del día va a tardar** hasta un minuto: **hay dos cosas
> dormidas en fila**, el servicio de Render y la base de datos de Neon. El
> propio panel lo advierte: *«Your free instance will spin down with
> inactivity, which can delay requests by 50 seconds or more»*.

### 5.8 · La misma prueba sin terminal: Swagger

**Esta API viaja con Swagger encendido**, así que todo lo anterior se puede
hacer desde el navegador:

```
https://apifacturas-diseno4.onrender.com/swagger
```

![Swagger de la API publicada](docs/tutorial_render/img/18_swagger.png)

**Ahí está el contrato completo** —`/api/cliente`, `/api/factura`,
`/api/consultas/...`— con los cinco verbos de cada recurso. **El candado al
lado de cada ruta** significa que pide token.

#### 1. Pedir el token

**`Sesion` → `POST /api/sesion` → `Try it out`**, y en el cuerpo:

```json
{
  "email": "admin@correo.com",
  "contrasena": "admin123"
}
```

![La respuesta del login en Swagger](docs/tutorial_render/img/19_swagger_sesion.png)

```
200
{
  "estado": 200,
  "mensaje": "Sesion iniciada.",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email": "admin@correo.com",
  "roles": [ "Administrador" ],
  "expira": "2026-10-30T04:00:57Z"
}
```

> **Fíjese en `expira`: una hora.** Pasada esa hora el mismo token devuelve
> `401` y hay que volver a pedir uno. **Eso no es un estorbo, es el punto:** un
> token robado tiene fecha de vencimiento.

#### 2. Guardarlo

**Botón `Authorize`**, arriba a la derecha.

![El dialogo Authorize](docs/tutorial_render/img/20_swagger_authorize.png)

**Pegue el token solo, sin la palabra `Bearer`** — ésa la pone Swagger. Es el
error más común aquí, y el resultado es un `401` que parece decir que el token
está malo cuando lo que sobra es una palabra.

> **Y ojo al copiar:** el token es larguísimo y el navegador lo muestra
> partido. **Hay que llevarse la cadena completa**, de la primera `e` a la
> última letra.

#### 3. Usarlo

**Cualquier ruta con candado, `Try it out` → `Execute`.**

![Usuarios devueltos con el token](docs/tutorial_render/img/21_swagger_usuarios.png)

```
GET /api/usuario?limite=1000     ->  200

{ "tabla": "usuario", "limite": 1000, "total": 8, "datos": [ ... ] }
```

**Ocho usuarios**, los que sembró el script del paso 2 — leídos desde Neon.

> **Y la prueba que falta, que es la que de verdad vale:** oprima `Authorize` →
> `Logout` y ejecute la misma ruta otra vez. **Debe responder `401`.** Si
> devolviera los datos igual, el control de acceso no estaría funcionando — y
> eso **no se descubre probando lo que sí funciona.**

---

## Paso 6 — El front en Flask

**Es el mismo procedimiento del paso 5, con tres diferencias.** Y la primera
sorprende a todo el mundo:

> **Es el MISMO repositorio.** El front no vive en otro proyecto: está en la
> carpeta `front_flask/` del repositorio que ya conectamos. **Lo único que
> cambia es `Root Directory`.**
>
> **Y eso es el curso otra vez:** la API y la interfaz son **dos programas
> distintos** que se hablan por HTTP. Que compartan carpeta en su disco no los
> vuelve uno solo — **se publican por separado, arrancan por separado y se
> caen por separado.**

**`+ New`** → **`Web Service`** → **`Public Git Repository`** → la misma
dirección → **`Connect`**.

![El front, desde el mismo repositorio](docs/tutorial_render/img/22_render_front_repo.png)

### 6.1 · Los campos

| Campo | Qué poner | Qué es |
|---|---|---|
| **`Name`** | `facturas-flask-diseno4` | queda en la dirección: `facturas-flask-diseno4.onrender.com` |
| **`Region`** | **`Frankfurt (EU Central)`** | ahora dice **`2 existing services`**: la API y el front del otro curso |
| **`Root Directory`** | `front_flask` | **la única diferencia real** con el paso 5 |
| **`Compute`** | **`$0 / month · Free`** | otra vez viene marcado el de 7 dólares |
| **`Dockerfile Path`** | **no lo toque** | **el front sí usa el `Dockerfile` normal.** Aquí no hay dos: uno solo sirve para desarrollo y para publicado |

### 6.2 · Las dos variables

| KEY | VALUE | Qué es |
|---|---|---|
| **`API_FACTURAS_URL`** | `https://apifacturas-diseno4.onrender.com` | **a qué API le habla.** Sin esto el front busca en `localhost`, **que dentro del contenedor es él mismo** |
| **`CLAVE_SESION`** | oprima **`Generate`** | **firma la cookie de sesión**, que es donde el front guarda el token |

> **Tres errores al escribir esa dirección, y ninguno dice lo que pasa:**
>
> | | |
> |---|---|
> | **Sin `https://` adelante** | `requests` no sabe qué hacer con eso |
> | **Con barra al final** | el front arma `...onrender.com//api/sesion` —dos barras— y la API responde `404` |
> | **Escrita a mano** | cópiela del panel de la API. Una letra de más y el front no encuentra nada |

> **Y si no pone `CLAVE_SESION`:** el front usa la clave de desarrollo **que
> está escrita en el código** — y cualquiera que lea el repositorio podría
> fabricarse una cookie de sesión válida.

**`Deploy web service`.**

### 6.3 · El registro, y los dos renglones que lo prueban todo

![El front vivo en Render](docs/tutorial_render/img/23_render_front_vivo.png)

```
==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs in the instance
[INFO] Starting gunicorn 23.0.0
[INFO] Listening at: http://0.0.0.0:10000 (1)
[INFO] Booting worker with pid: 7
[INFO] Booting worker with pid: 8
==> Your service is live
==> Available at your primary URL https://facturas-flask-diseno4.onrender.com
```

**Aquí se cobran dos decisiones que se tomaron antes de publicar nada:**

| Lo que dice el registro | Por qué |
|---|---|
| **`Starting gunicorn`**, y no el servidor de Flask | la imagen trae **`DEPURAR=0`** por defecto, y **nadie puso esa variable en Render**. El servidor de desarrollo de Flask atiende una petición a la vez y su depurador en internet es una puerta abierta |
| **`Listening at: http://0.0.0.0:10000`** | **Render impone el puerto con `PORT`**, y `app.py` la lee **antes** que `PUERTO`. Por eso el mismo código corre en Docker local (8081) y aquí (10000) |

> **Y fíjese en la discusión silenciosa:** Render anuncia `WEB_CONCURRENCY=1`,
> pero arrancaron **dos** trabajadores (`pid: 7` y `pid: 8`). Es porque el
> `Dockerfile` dice `--workers 2`, **y lo explícito gana sobre lo sugerido.**

---

## Paso 7 — La prueba del sistema completo

```
https://facturas-flask-diseno4.onrender.com
```

**Entre con `admin@correo.com` / `admin123`** y abra `Productos`.

**Comprobado desde la terminal, contra el sitio publicado:**

```
POST /login   admin@correo.com   ->  302, redirige a /
GET  /e/producto                 ->  <title>Productos · Comercial Los Andes S.A.</title>
```

### La prueba que de verdad cierra el círculo: emitir una factura

**Leer datos prueba la mitad del camino.** Para probar la otra mitad hay que
**escribir** — y la facturación es el mejor sitio, porque ahí trabajan el
procedimiento y el disparador que viven **dentro de la base de datos**.

**`Facturas` → `Nueva factura`.** Escoja cliente y vendedor, agregue dos
productos y mire el total:

![Emitir una factura desde el front publicado](docs/tutorial_render/img/24_front_factura_nueva.png)

> **El renglón bajo el total es el punto de la versión 4:**
>
> *«Este total es un cálculo para que usted sepa cuánto va. **No se envía**: el
> total que queda guardado lo calcula el disparador de la base de datos, y es
> el que manda.»*
>
> **La pantalla no decide la plata.** Si el front mandara el total, cualquiera
> podría mandar otro.

**`Emitir la factura`:**

![La factura 7, emitida](docs/tutorial_render/img/25_front_factura_emitida.png)

```
Factura 7 emitida — los subtotales y el total los calculó la base de datos.
```

**Y ahora la comprobación, en el `SQL Editor` de Neon:**

```sql
SELECT numero, fecha, total, estado
FROM factura
ORDER BY numero DESC
LIMIT 2;
```

```
 numero |           fecha            |  total  | estado
--------+----------------------------+---------+--------
      7 | 2026-10-30 03:17:32.227703 | 3600000 | activa
      6 | 2025-12-03 13:05:35.02846  | 4850000 | activa
```

**Las seis primeras son los datos semilla; la séptima la acaba de escribir
usted desde un navegador en Colombia.**

**Y el stock, que es la otra mitad de lo que hace el disparador:**

```sql
SELECT codigo, nombre, stock FROM producto
WHERE codigo IN ('PR001', 'PR005');
```

```
 codigo |          nombre          | stock
--------+--------------------------+-------
 PR001  | Laptop Lenovo IdeaPad    |    16
 PR005  | Impresora Epson EcoTank1 |    13
```

**Bajó solo.** Nadie escribió «descontar stock» en el front ni en la API: **lo
hizo el disparador, dentro de PostgreSQL**, en la misma transacción que
guardó la factura.

> **Eso es lo que acaba de quedar demostrado publicado, y no solo en su
> máquina:** la regla de negocio vive donde tiene que vivir, **el total que
> manda es el que calculó la base de datos**, y las tres piezas —front, API y
> base de datos, en tres servicios distintos— se coordinaron para una sola
> operación.

### Lo que acaba de recorrer esa petición

```
su navegador
   |  https
front en Flask      Render, Frankfurt     (Python, en Docker)
   |  https
API                 Render, Frankfurt     (C#, en Docker)
   |  tls
base de datos       Neon, Frankfurt       (PostgreSQL 18)
```

| | |
|---|---|
| **Tres proveedores** | Render, Neon y GitHub |
| **Dos lenguajes** | Python y C# |
| **Dos imágenes Docker** | construidas por Render, a partir de dos `Dockerfile` del mismo repositorio |
| **Un solo sistema** | y ninguna de las piezas sabe cómo está hecha la otra |

> **La primera carga del día va a tardar**, y esta vez hay **tres cosas
> dormidas en fila**: el front, la API y la base de datos. Cada una despierta
> con la primera petición. **Es el precio del plan gratuito**, y el panel lo
> advierte: *«can delay requests by 50 seconds or more»*.

---

## Si algo no funciona

| Lo que ve | Qué revisar |
|---|---|
| **El servicio dice `Deploy failed`** | Lea el registro **de abajo hacia arriba**: el error de verdad suele estar varios renglones antes del final |
| **La API arranca y se muere** | Falta `Jwt__Key`, o tiene menos de 32 caracteres. `Program.cs` **aborta a propósito** |
| **La API responde pero todo da `500`** | La cadena de conexión. Compruébela con el paso 3.5, **en su máquina**, donde el error se ve completo |
| **`GET /` dice `motor: sqlserver`** | Alguien escribió `sqlserver` en la variable `Motor` de Render. **Si la variable no existe no pasa nada** —el `appsettings.json` del proyecto ya dice `postgres`—, pero **puesta mal sí hace daño**: la API arranca bien, intenta hablar **T-SQL contra PostgreSQL**, y el error que sale no menciona PostgreSQL por ninguna parte |
| **El front abre pero el login falla** | `API_FACTURAS_URL`: sin `https://`, con barra al final, o mal escrita |
| **Todo responde `401`** | `Jwt__Issuer` o `Jwt__Audience` no coinciden con lo que valida la API |
| **El servicio tarda 50 segundos** | Está despertando. **No es un error**, es el plan gratuito |
| **Render construyó el `Dockerfile` equivocado** | `Settings` → `Dockerfile Path`. Debe decir `api_facturas/Dockerfile.produccion` |

---

## Lo que quedó demostrado

| | |
|---|---|
| **Un `Dockerfile` es la receta, y el hospedaje solo la sigue** | Render no sabe que esto es C# ni Python: lee el archivo y construye |
| **El puerto no lo decide la aplicación** | lo impone la plataforma, y el programa tiene que obedecer. Es el fallo más común al publicar en contenedores |
| **Los secretos viven en el panel, no en el repositorio** | por eso este repositorio puede ser público |
| **La misma aplicación corre en dos sitios sin cambiar una línea** | en su máquina con `docker compose`, aquí con tres servicios en tres proveedores |
| **Las capas se pagan solas el día que hay que publicar** | la API no sabe quién la llama, el front no sabe de qué está hecha la API, y la base de datos no sabe que existe internet |

---

**Versión 1.0** — escrito el 29 de octubre de 2026, ejecutando cada paso.
Las direcciones de ejemplo son las de esa corrida; **las suyas van a ser
otras.**
