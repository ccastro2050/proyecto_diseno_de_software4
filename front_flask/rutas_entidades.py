"""
rutas_entidades.py — Las rutas GENERICAS del front.

Un solo juego de vistas atiende a TODAS las entidades: la entidad llega en la
URL (`/e/<clave>`) y sus metadatos salen de `entidades.py`.

Y conviene decir por que aqui si vale lo generico y en la API no, que es la
pregunta obvia: la API expone un CONTRATO que otros leen, y un `/api/{tabla}`
lo deja en blanco. Esto no expone nada — es la configuracion de UNA
aplicacion, y el contrato que consume sigue siendo especifico.

LAS REGLAS DE NEGOCIO SIGUEN TODAS EN LA API. Aqui solo se dibuja.
"""

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)

import cliente_api
from entidades import ENTIDADES

bp = Blueprint("entidades", __name__)


def _config(clave):
    """Los metadatos de la entidad, y la cortesia de no abrir lo que no se puede.

    OJO CON LO QUE ESTO NO ES: no es el control de acceso. Si alguien quita
    esta comprobacion, la API sigue respondiendo 403 — porque la proteccion
    esta alla, en [ExigePermiso], y no aqui.

    Esto solo evita que la persona llegue a una pantalla que le va a responder
    403 en todas las operaciones. Y por eso usa EL MISMO permiso que la API:
    el valor de la tabla `ruta`. Si el front tuviera su propia idea de quien
    puede que, un dia no coincidirian.
    """
    cfg = ENTIDADES.get(clave)
    if cfg is None:
        abort(404)
    if "usuario" not in session:
        abort(redirect(url_for("login")))
    if cfg.get("permiso") and cfg["permiso"] not in session.get("permisos", []):
        flash("Su rol no tiene permiso para esa seccion.", "error")
        abort(redirect(url_for("inicio")))
    return cfg


def _opciones_fk(cfg):
    """Para cada campo que es clave foranea, trae sus opciones DESDE LA API.

    Es la leccion de la v2: la clave foranea se ELIGE de un desplegable, no se
    escribe. Un campo de texto obliga a la persona a adivinar que codigos
    existen; escribe uno que no esta, la API responde 409, y no hay forma de
    saber cual era el bueno.

    El desplegable muestra el NOMBRE y manda el CODIGO: la persona reconoce
    nombres, la base necesita claves.
    """
    opciones = {}
    for nombre, _, fk in cfg["campos"]:
        if not fk:
            continue
        fuente = ENTIDADES[fk]
        ok, datos, _ = cliente_api.listar(fuente["endpoint"])
        pk = fuente["pk"]
        etiqueta = fuente["campos"][1][0] if len(fuente["campos"]) > 1 else pk
        opciones[nombre] = ([(str(d[pk]), "%s — %s" % (d[pk], d.get(etiqueta, "")))
                             for d in datos] if ok else [])
    return opciones


@bp.route("/e/<clave>")
def lista(clave):
    cfg = _config(clave)
    ok, datos, errores = cliente_api.listar(cfg["endpoint"])
    for e in errores:
        flash(e, "error")
    return render_template("entidades/lista.html", clave=clave, cfg=cfg, datos=datos)


@bp.route("/e/<clave>/nuevo", methods=["GET", "POST"])
def crear(clave):
    cfg = _config(clave)
    if request.method == "POST":
        datos = {n: request.form.get(n, "").strip() for n, _, _ in cfg["campos"]}
        # LO VACIO NO VIAJA. Asi el 422 de la API dice «es obligatorio» en
        # castellano, en vez del error tecnico de conversion de JSON. Y un
        # opcional vacio queda sin enviar, que es lo que la API espera para
        # ponerle su valor por defecto.
        datos = {k: v for k, v in datos.items() if v != ""}
        ok, errores = cliente_api.crear(cfg["endpoint"], datos)
        if ok:
            flash("Registro creado.", "exito")
            return redirect(url_for("entidades.lista", clave=clave))
        for e in errores:
            flash(e, "error")
        # El error NO borra lo que la persona escribio: vuelve al formulario
        # con sus datos, para que pueda corregir.
        return render_template("entidades/formulario.html", clave=clave, cfg=cfg,
                               registro=datos, editando=False,
                               opciones=_opciones_fk(cfg))
    return render_template("entidades/formulario.html", clave=clave, cfg=cfg,
                           registro={}, editando=False, opciones=_opciones_fk(cfg))


@bp.route("/e/<clave>/<pk>/editar", methods=["GET", "POST"])
def editar(clave, pk):
    cfg = _config(clave)
    if not cfg["editable"]:
        # Las tablas puente no se editan: una pareja existe o no existe.
        # Cambiarla es quitarla y poner otra.
        abort(404)
    if request.method == "POST":
        # PATCH: viaja SOLO lo diligenciado. Dejar un campo vacio significa «no
        # lo toque» — y por eso editar no obliga a volver a escribirlo todo.
        # El PUT, con el mismo cuerpo, responderia 422.
        datos = {n: request.form.get(n, "").strip() for n, _, _ in cfg["campos"]
                 if n != cfg["pk"] and request.form.get(n, "").strip() != ""}
        ok, errores = cliente_api.actualizar(cfg["endpoint"], pk, datos)
        if ok:
            flash("Registro actualizado.", "exito")
            return redirect(url_for("entidades.lista", clave=clave))
        for e in errores:
            flash(e, "error")
    ok, registro, errores = cliente_api.obtener(cfg["endpoint"], pk)
    if not ok:
        for e in errores:
            flash(e, "error")
        return redirect(url_for("entidades.lista", clave=clave))
    return render_template("entidades/formulario.html", clave=clave, cfg=cfg,
                           registro=registro, editando=True,
                           opciones=_opciones_fk(cfg))


@bp.route("/e/<clave>/<pk>/eliminar", methods=["POST"])
def eliminar(clave, pk):
    cfg = _config(clave)
    ok, errores = cliente_api.eliminar(cfg["endpoint"], pk)
    flash("Registro eliminado." if ok else " ".join(errores),
          "exito" if ok else "error")
    return redirect(url_for("entidades.lista", clave=clave))


@bp.route("/e/<clave>/<a>/<b>/eliminar", methods=["POST"])
def eliminar_puente(clave, a, b):
    """El borrado de una tabla PUENTE necesita LAS DOS claves.

    Su clave primaria son las dos columnas juntas, asi que con una sola no se
    sabe cual pareja quitar. De ahi que esta ruta exista aparte.
    """
    cfg = _config(clave)
    if not cfg.get("puente"):
        abort(404)
    ok, errores = cliente_api.eliminar(cfg["endpoint"], "%s/%s" % (a, b))
    flash("Asignacion retirada." if ok else " ".join(errores),
          "exito" if ok else "error")
    return redirect(url_for("entidades.lista", clave=clave))
