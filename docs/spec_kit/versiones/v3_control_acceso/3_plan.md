# Plan técnico — Versión 3: el control de acceso

> | | |
> |---|---|
> | **Qué hay que construir** | [2_spec.md](2_spec.md) |
> | **Los formatos exactos** | [6_contracts.md](6_contracts.md) |
> | **El orden** | [8_tasks.md](8_tasks.md) |
> | **Los conceptos** | [CONCEPTOS_CONTROL_DE_ACCESO.md](../../../CONCEPTOS_CONTROL_DE_ACCESO.md) |

---

## 1. Lo único que se agrega a la pila

| | |
|---|---|
| **`Microsoft.AspNetCore.Authentication.JwtBearer`** | Valida el token en cada petición |

**Y la versión no se adivinó:** es la **9.0.10**, que es la que ya corre sobre
`net10.0` en `proyecto_construccion1/api_generica_csharp`. Elegir un número
por intuición es lo que hace perder una tarde: se copia de un proyecto que
compila.

> **`BCrypt.Net-Next` ya estaba** desde antes, y el hash de la contraseña **ya
> funcionaba**. Lo que faltaba no era el hash: era la **puerta**.

## 2. Las tres piezas, y por qué son tres

```
   credenciales          token            permiso
        │                  │                 │
   AUTENTICA ────────►  SESIÓN  ────────► AUTORIZA
   ¿quién es?         (lo recuerda)       ¿puede esto?
        │                  │                 │
  ServicioSesion      JwtBearer        ExigePermiso
   + BCrypt           (middleware)   + verificar_acceso_ruta
```

| | Archivo | Qué resuelve |
|---|---|---|
| **1** | `Servicios/ServicioSesion.cs` | Compara el hash y **arma** el token |
| **2** | `Program.cs` → `AddJwtBearer` | **Valida** el token en cada petición. **401** si no sirve |
| **3** | `Autorizacion/ExigePermisoAttribute.cs` | Pregunta el permiso. **403** si el rol no puede |

> **Sin la 1 las otras dos no tienen a quién validar. Sin la 2, la 3 no sabe
> quién pregunta. Y sin la 3, el sistema sabe quién entra y le deja hacer todo.**
> El orden no es un gusto: cada una necesita la anterior.

## 3. Los archivos nuevos

### 3.1 La sesión

```
Modelos/ConfiguracionJwt.cs       los 4 valores con los que se firma y se valida
Modelos/Sesion.cs                 lo que recibe quien se identifica
Peticiones/SesionCrear.cs         { email, contrasena }  ← EN EL CUERPO
Servicios/IServicioSesion.cs
Servicios/ServicioSesion.cs       compara el hash y arma el token
Controllers/SesionController.cs   POST /api/sesion — el único [AllowAnonymous]
```

**Dos decisiones de diseño que vale la pena leer dos veces:**

| | |
|---|---|
| **Las credenciales van en el CUERPO** | El endpoint de la versión anterior las recibía por la URL: `?valor_usuario=…&valor_contrasena=…`. **Una contraseña en la URL queda en el historial del navegador y en los logs de cualquier proxy del camino.** Ese endpoint se queda —no se toca lo cerrado— y el inicio de sesión de verdad usa el cuerpo |
| **El mismo error para los dos casos** | Correo inexistente y contraseña equivocada responden **lo mismo**. Decir «ese correo no existe» le confirma a un desconocido **cuáles sí existen** — y con una lista de correos válidos, probar contraseñas vale la pena |

### 3.2 El permiso

```
Repositorios/IRepositorioAcceso.cs
Repositorios/RepositorioAccesoPostgres.cs   llama verificar_acceso_ruta
Autorizacion/ExigePermisoAttribute.cs       el filtro que responde 403
Controllers/PermisosController.cs           GET /api/permisos/mios, para el menú
```

**El atributo, que es la pieza central:**

```csharp
[Route("api/usuario")]
[Authorize]                        // exige TOKEN      -> 401
[ExigePermiso("interfaz.usuarios")] // exige PERMISO    -> 403
public class UsuarioController : ControllerBase
```

| | Por qué así |
|---|---|
| **Es un FILTRO, no una línea al principio de cada método** | Si fuera una línea, el día que alguien escriba un endpoint nuevo y se le olvide, **ese endpoint queda abierto** — y nadie lo nota, porque funciona |
| **Se consulta EN CADA PETICIÓN** | Es más trabajo —una consulta por operación— y es lo que hace que **quitarle un permiso surta efecto sin volver a identificarse** |
| **El nombre de la ruta sale de la tabla `ruta`** | `interfaz.usuarios`, `interfaz.facturas`… son los valores que la base ya trae sembrados. No se inventan |

### 3.3 La interfaz gráfica

```
app.py  (session de Flask)                quién está identificado, FIRMADO en la cookie
cliente_api.iniciar_sesion()              la única llamada que funciona sin token
cliente_api.mis_permisos()                los permisos que arman el menú
templates/login.html                      la interfaz de identificación
templates/base.html                       quién está dentro, y cómo salir
app.py  (el context_processor menu())     el menú ARMADO CON LOS PERMISOS
```

**Y doce archivos que crecen:** cada servicio del front suma un método
`Autorizar()` que pone el token en la cabecera antes de cada petición.

## 4. Las cuatro decisiones del front, con su razón

### 4.1 El token vive en la COOKIE DE SESIÓN, y Flask la FIRMA

`session` de Flask es una cookie firmada con `CLAVE_SESION`: el navegador la
guarda, y **no la puede alterar sin romper la firma**.

| | |
|---|---|
| **Qué se gana** | Sobrevive al F5. Y el front no guarda estado propio: dos copias del contenedor atienden la misma sesión sin ponerse de acuerdo |
| **Qué se pierde, y hay que decirlo** | El token **sí baja al navegador**, dentro de la cookie. La firma impide **alterarla**, no leerla |

> **Firmada no es cifrada**, y es la misma propiedad del JWT que lleva adentro:
> cualquiera que tenga la cookie puede ver su contenido. Por eso ahí no va nada
> privado — ni la contraseña, ni los permisos.
>
> Lo que sí hace Flask es marcarla **`HttpOnly`** por defecto: un script de la
> página **no** la puede leer. Guardar el token en `localStorage` —que es la
> otra opción— pierde justamente eso.

> **EL ERROR FÁCIL, y no da ningún mensaje:** guardar el token en una variable
> de módulo de `cliente_api.py` —«total, es una sola aplicación»—. Entonces hay
> **UN token para todos los que entren**, y el último que se identifique le
> cambia la sesión a los demás. Es el mismo error que en un front de Blazor
> Server es declarar el estado de sesión como `singleton` en vez de `scoped`:
> otro lenguaje, otra palabra, **idéntica consecuencia**.

### 4.2 La cabecera se pone en UN solo sitio, y no en un cliente compartido

`_cabecera()` en `cliente_api.py` lee el token de la sesión y lo pone en cada
llamada. Lo elegante sería un `requests.Session` de módulo con la cabecera ya
puesta. **Y no se hace**, por una razón concreta: ese objeto es **uno para todo
el proceso**, compartido por todas las personas conectadas, y la cabecera de
una sesión se le quedaría puesta a la siguiente.

> Es un problema **silencioso**: no falla, responde — con el token de otro. Es
> la misma trampa que en Blazor Server tiene el `DelegatingHandler`, cuya
> cadena se arma una vez por nombre de cliente y se reutiliza.

### 4.3 Y donde los hilos entran, el token viaja como argumento

El tablero de la v4 pide **diez consultas a la vez**. `session` pertenece al
contexto de la petición, y **un hilo nuevo no lo tiene**: las diez saldrían sin
cabecera y la API responderia **401**, diez veces.

> El camino que no sirve, porque es el primero que se intenta: envolver la
> función con `copy_current_request_context`. Eso revienta con
> `ValueError: <Token ...> was created in a different Context`, porque el
> envoltorio copia **un** contexto y los diez hilos entran y salen del mismo.
> Pasar el token como argumento es más corto y no tiene magia.

### 4.4 El menú no es la protección, y la interfaz lo dice

El menú se arma con `GET /api/permisos/mios`. **Y eso no protege nada:** es
HTML que ya está en el navegador de quien pregunta, y la dirección se puede
escribir a mano.

> **Se comprueba así, y es el criterio 9:** identifíquese con un rol sin
> permiso y **escriba la dirección a mano**. La interfaz se abre, le pide los
> datos a la API, y la API responde **403**. Eso es lo que tiene que pasar.

## 5. Los cinco tropiezos que esta versión tiene preparados

| | Qué pasa | Cómo se ve |
|---|---|---|
| **1** | **El `ClockSkew` por defecto** | ASP.NET perdona **5 minutos** de reloj desadaptado. Un token vencido responde **200** durante cinco minutos, y parece que el código está mal. Se pone en cero |
| **2** | **El 401 sin cuerpo** | ASP.NET responde el 401 con el cuerpo **vacío**, y la interfaz no tiene nada que mostrarle a la persona. Se arregla con `OnChallenge` |
| **3** | **`UseAuthentication` después de `UseAuthorization`** | Compila, arranca, y **deja pasar todo**: el segundo no tiene a quién consultar |
| **4** | **Una ruta que no está en la tabla** | `verificar_acceso_ruta` no la encuentra. Tiene que **fallar cerrado** —nadie entra— y no abierto |
| **5** | **la cookie de sesión como `singleton`** | Un token para todos. No da ningún error: da la sesión de otro |

> **Los cinco pasan la compilación.** Tres de ellos —el 1, el 3 y el 5— dejan
> el sistema **menos seguro de lo que parece**, que es la peor clase de error:
> funciona, y por eso nadie lo mira.

## 6. Lo que este plan deja FUERA, a propósito

| | Por qué |
|---|---|
| **Refrescar el token** | Con una hora de duración, volver a identificarse alcanza. Un *refresh token* trae su propio problema —cómo se revoca— y el curso no lo pide |
| **Recuperar la contraseña por correo** | Hace falta un servidor de correo. No lo pide el curso |
| **Segundo factor** | Ídem |
| **Revocar un token** | **No se puede**, y es una propiedad del diseño, no un olvido: un JWT está firmado y ya salió. Lo único que lo apaga es que venza — de ahí que la duración sea corta |
| **Permisos por operación** (leer sí, borrar no) | La tabla `ruta` tiene `permiso.crear` y `permiso.eliminar` sembrados, así que la base lo soportaría. **La v3 protege por interfaz**, que es lo que los diez criterios piden |
