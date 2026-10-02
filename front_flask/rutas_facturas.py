"""
rutas_facturas.py — La facturación en el navegador (v8).

La operación de negocio más rica del sistema, con la misma regla de
siempre: el front NO calcula nada — subtotales, total y stock los pone
la BD (los triggers) a través de la API. El front arma la petición y
muestra lo que la API responda.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

import cliente_api
from entidades import ENTIDADES

bp = Blueprint("facturas", __name__)

RENGLONES = 5  # filas de detalle que ofrece el formulario (mínimo 1 diligenciada)


def _opciones():
    """Los selects del encabezado y de los renglones, cargados de la API."""
    ok_c, clientes, _ = cliente_api.listar("/api/cliente")
    ok_v, vendedores, _ = cliente_api.listar("/api/vendedor")
    ok_p, productos, _ = cliente_api.listar("/api/producto")
    # El cliente/vendedor se muestran con el nombre de su persona si viene:
    return (
        [(c["id"], f"{c['id']} — persona {c.get('fkcodpersona', '')}") for c in clientes] if ok_c else [],
        [(v["id"], f"{v['id']} — persona {v.get('fkcodpersona', '')}") for v in vendedores] if ok_v else [],
        [(p["codigo"], f"{p['codigo']} — {p['nombre']} (stock {p['stock']})") for p in productos] if ok_p else [],
    )


@bp.route("/facturas")
def lista():
    ok, facturas, errores = cliente_api.listar_facturas()
    for e in errores:
        flash(e, "error")
    return render_template("facturas/lista.html", facturas=facturas)


@bp.route("/facturas/<int:numero>")
def detalle(numero):
    ok, factura, errores = cliente_api.obtener_factura(numero)
    if not ok:
        for e in errores:
            flash(e, "error")
        return redirect(url_for("facturas.lista"))
    return render_template("facturas/detalle.html", f=factura)


@bp.route("/facturas/nueva", methods=["GET", "POST"])
def crear():
    clientes, vendedores, productos = _opciones()
    if request.method == "POST":
        # Los renglones diligenciados (producto Y cantidad) viajan; el resto no:
        renglones = []
        for i in range(RENGLONES):
            codigo = request.form.get(f"producto_{i}", "").strip()
            cantidad = request.form.get(f"cantidad_{i}", "").strip()
            if codigo and cantidad:
                renglones.append({"codigo": codigo, "cantidad": cantidad})
        datos = {
            "fkidcliente": request.form.get("fkidcliente", ""),
            "fkidvendedor": request.form.get("fkidvendedor", ""),
            "productos": renglones,
        }
        ok, factura, errores = cliente_api.crear_factura(datos)
        if ok:
            flash(f"Factura {factura.get('numero', '')} creada — subtotales y "
                  "total los calculó la base de datos.", "exito")
            return redirect(url_for("facturas.lista"))
        for e in errores:
            flash(e, "error")
    return render_template("facturas/formulario.html", clientes=clientes,
                           vendedores=vendedores, productos=productos,
                           renglones=range(RENGLONES))


@bp.route("/facturas/<int:numero>/anular", methods=["POST"])
def anular(numero):
    ok, errores = cliente_api.anular_factura(numero)
    if ok:
        flash(f"Factura {numero} anulada: el stock quedó RESTAURADO.", "exito")
    for e in errores:
        flash(e, "error")
    return redirect(url_for("facturas.lista"))
