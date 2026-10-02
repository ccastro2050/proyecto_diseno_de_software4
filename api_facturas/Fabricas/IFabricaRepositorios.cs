// ============================================================
// IFabricaRepositorios — el contrato de la FÁBRICA (v4).
//
// El patrón fábrica abstracta: quien implementa esta interfaz
// decide el motor de las ONCE rebanadas a la vez. El ensamblador
// (Program.cs) elige UNA fábrica al arrancar y le pide todo; nadie
// más en el sistema vuelve a pensar en motores.
//
// Los 11 métodos "aburridos" SON la lección: la fábrica promete la
// familia COMPLETA de repositorios, no repositorios sueltos — por
// eso agregar un motor (MariaDB, v5) costará UNA clase, y agregar
// una entidad obligará a los DOS motores a soportarla (el compilador
// no deja fábricas incompletas).
// ============================================================

using ApiFacturas.Repositorios;

namespace ApiFacturas.Fabricas;

public interface IFabricaRepositorios
{
    IRepositorioProducto CrearRepositorioProducto();
    IRepositorioPersona CrearRepositorioPersona();
    IRepositorioFactura CrearRepositorioFactura();
    IRepositorioEmpresa CrearRepositorioEmpresa();
    IRepositorioCliente CrearRepositorioCliente();
    IRepositorioVendedor CrearRepositorioVendedor();
    IRepositorioUsuario CrearRepositorioUsuario();
    IRepositorioRol CrearRepositorioRol();
    IRepositorioRuta CrearRepositorioRuta();
    IRepositorioRolUsuario CrearRepositorioRolUsuario();
    IRepositorioRutaRol CrearRepositorioRutaRol();

    /// <summary>El recurso maestro-detalle sobre la tabla puente (v2).</summary>
    IRepositorioUsuarioConRoles CrearRepositorioUsuarioConRoles();

    /// <summary>El control de acceso (v3). Tambien por aqui: con el motor
    /// en sqlserver, un repositorio de acceso que siguiera hablando con
    /// PostgreSQL no se notaria hasta que los dos dejaran de tener los
    /// mismos datos.</summary>
    IRepositorioAcceso CrearRepositorioAcceso();
}
