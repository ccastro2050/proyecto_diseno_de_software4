"""
cliente_api.py — La capa de datos del FRONT.

Es al front lo que el repositorio es al back: la UNICA pieza que sabe donde
viven los datos. Traduce respuestas HTTP a tuplas `(ok, datos, errores)` — y
NUNCA decide negocio.

Si manana la API cambia de direccion, se cambia aqui y en ningun otro sitio.
"""

import os

import requests
from flask import session

# El NOMBRE del servicio del compose, jamas localhost: dentro del contenedor
# del front, localhost seria el front mismo.
URL_API = os.environ.get("API_FACTURAS_URL", "http://localhost:8055")

# Si la API no contesta en diez segundos, el front lo DICE. No se queda
# esperando: una interfaz colgada es peor que una que avisa.
TIEMPO_MAXIMO = 10

def _cabecera(token=None):
    """La cabecera con el token. Si no hay, se manda sin ella — y la API
    responde 401, que es lo correcto: no se simula una sesion que no existe."""
    if token is None:
        token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _llamar(metodo: str, ruta: str, **kwargs):
    """Ejecuta la peticion y unifica el manejo de «la API no responde»."""
    try:
        return requests.request(metodo, f"{URL_API}{ruta}",
                                timeout=TIEMPO_MAXIMO, **kwargs)
    except requests.RequestException:
        return None


def _mensaje(r):
    """El mensaje del DOMINIO que trae la API, no el codigo HTTP.

    El 422 trae `errores[]` con una entrada por campo; los demas traen
    `mensaje`. Y el 401 y el 403 se dicen con palabras, porque son los dos
    codigos que una persona tiene que poder distinguir:
    401 = «no se quien es usted»; 403 = «se quien es, y no puede».
    """
    try:
        cuerpo = r.json()
    except Exception:
        cuerpo = {}
    if r.status_code == 422:
        errores = cuerpo.get("errores") or []
        if isinstance(errores, list) and errores:
            return [str(e) for e in errores]
        if isinstance(errores, dict):
            return [f"{c}: {'; '.join(m)}" for c, m in errores.items()]
    if r.status_code == 401:
        return ["Su sesion no es valida o ya vencio. Vuelva a iniciar sesion."]
    if r.status_code == 403:
        return ["Su rol no tiene permiso para esta operacion."]
    return [cuerpo.get("mensaje", "El servicio respondio con un problema.")]


def listar(endpoint: str):
    r = _llamar("GET", endpoint, headers=_cabecera())
    if r is None:
        return False, [], ["El servicio no esta disponible."]
    if r.status_code == 204:
        # 204: la tabla esta vacia. NO es un error.
        return True, [], []
    if r.status_code == 200:
        # EL SOBRE DEL CONTRATO: { tabla, limite, total, datos[] }. La API no
        # devuelve un arreglo pelado, y deserializarlo como tal deja la
        # interfaz vacia SIN ningun error.
        return True, r.json().get("datos", []), []
    return False, [], _mensaje(r)


def obtener(endpoint: str, clave):
    r = _llamar("GET", f"{endpoint}/{clave}", headers=_cabecera())
    if r is None:
        return False, None, ["El servicio no esta disponible."]
    if r.status_code == 200:
        return True, r.json(), []
    return False, None, _mensaje(r)


def crear(endpoint: str, datos: dict):
    r = _llamar("POST", endpoint, json=datos, headers=_cabecera())
    if r is None:
        return False, ["El servicio no esta disponible."]
    if r.status_code in (200, 201):
        return True, []
    return False, _mensaje(r)


def actualizar(endpoint: str, clave, datos: dict):
    """PATCH: viaja SOLO lo diligenciado. Dejar un campo vacio significa «no lo
    toque», y por eso el formulario de editar no exige volver a escribirlo
    todo. El PUT, con el mismo cuerpo, responderia 422."""
    r = _llamar("PATCH", f"{endpoint}/{clave}", json=datos, headers=_cabecera())
    if r is None:
        return False, ["El servicio no esta disponible."]
    if r.status_code == 200:
        return True, []
    return False, _mensaje(r)


def eliminar(endpoint: str, clave):
    r = _llamar("DELETE", f"{endpoint}/{clave}", headers=_cabecera())
    if r is None:
        return False, ["El servicio no esta disponible."]
    if r.status_code == 200:
        return True, []
    return False, _mensaje(r)

# ── v3: LA SESION ────────────────────────────────────────────────────

def iniciar_sesion(email: str, contrasena: str):
    """POST /api/sesion — devuelve (ok, sesion, errores).

    Las credenciales van EN EL CUERPO, no en la URL. El endpoint viejo
    `verificar-contrasena` las recibia por la URL, y una contrasena en la URL
    queda en el historial del navegador y en los logs de cualquier proxy del
    camino.
    """
    r = _llamar("POST", "/api/sesion", json={"email": email, "contrasena": contrasena})
    if r is None:
        return False, None, ["El servicio no está disponible."]
    if r.status_code == 200:
        return True, r.json(), []
    # El MISMO mensaje para el correo inexistente y la contrasena equivocada:
    # lo decide la API, y el front no lo "mejora" averiguando cual fue.
    return False, None, [r.json().get("mensaje", "El correo o la contrasena no son correctos.")]


def mis_permisos(token: str):
    """GET /api/permisos/mios — las rutas a las que ESTE usuario puede entrar.

    El correo sale DEL TOKEN, no de la URL: si viniera por parametro,
    cualquiera podria preguntar por los permisos de otro.

    Y OJO: esto NO es el control de acceso. Es una lista para dibujar el menu.
    La proteccion es el 403 que responde la API en cada operacion.
    """
    r = _llamar("GET", "/api/permisos/mios", headers=_cabecera(token))
    if r is None or r.status_code != 200:
        return []
    return r.json().get("datos", [])
