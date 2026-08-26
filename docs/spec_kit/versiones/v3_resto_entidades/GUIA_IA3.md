# Cómo construir la VERSIÓN 3 con IA — sobre su proyecto de la v2

> Guía de la **v3** (acumulativa: se construye encima de su proyecto con
> v1 y v2 terminadas). El método general es el de la
> [guía de la v1](../v1_producto_postgres/GUIA_IA1.md) y los ajustes de
> trabajo acumulativo son los de la
> [guía de la v2](../v2_persona_factura/GUIA_IA2.md): aquí está SOLO lo
> propio de la v3.

---

## 0. Punto de partida

Su proyecto con la **v2 funcionando** (los smoke tests de v1 y v2 pasan
con sus puertos +100). La BD no cambia: las 8 tablas de la v3 están en su
`db/bdfacturas_postgres.sql` desde el principio, con datos semilla.

## A.1 Qué subirle al chat (los 9 de la v3)

`docs/spec_kit/1_constitution.md` + los 7 documentos de
`docs/spec_kit/versiones/v3_resto_entidades/` (2_spec a 8_tasks). No suba
los kits de v1/v2 (el código que la IA necesite ver, se lo pega usted).

## A.2 Prepare su proyecto (comandos PowerShell)

1. **Carpeta nueva** (la única): la de las specs de la v3.

   ```powershell
   mkdir docs\spec_kit\versiones\v3_resto_entidades
   ```

2. **Copie las specs** desde el clon del curso (ajuste la primera ruta):

   ```powershell
   Copy-Item ..\proyecto_diseno_de_software4\docs\spec_kit\versiones\v3_resto_entidades\* docs\spec_kit\versiones\v3_resto_entidades\
   ```

3. **Cree los ARCHIVOS VACÍOS nuevos** — los 68 que la IA irá llenando
   (8 modelos + 20 peticiones + 8 controllers + 16 servicios + 16
   repositorios):

   ```powershell
   New-Item api_facturas\Modelos\Empresa.cs, api_facturas\Modelos\Cliente.cs, api_facturas\Modelos\Vendedor.cs, api_facturas\Modelos\Usuario.cs, api_facturas\Modelos\Rol.cs, api_facturas\Modelos\Ruta.cs, api_facturas\Modelos\RolUsuario.cs, api_facturas\Modelos\RutaRol.cs, api_facturas\Peticiones\EmpresaCrear.cs, api_facturas\Peticiones\EmpresaReemplazo.cs, api_facturas\Peticiones\EmpresaActualizar.cs, api_facturas\Peticiones\ClienteCrear.cs, api_facturas\Peticiones\ClienteReemplazo.cs, api_facturas\Peticiones\ClienteActualizar.cs, api_facturas\Peticiones\VendedorCrear.cs, api_facturas\Peticiones\VendedorReemplazo.cs, api_facturas\Peticiones\VendedorActualizar.cs, api_facturas\Peticiones\UsuarioCrear.cs, api_facturas\Peticiones\UsuarioReemplazo.cs, api_facturas\Peticiones\UsuarioActualizar.cs, api_facturas\Peticiones\RolCrear.cs, api_facturas\Peticiones\RolReemplazo.cs, api_facturas\Peticiones\RolActualizar.cs, api_facturas\Peticiones\RutaCrear.cs, api_facturas\Peticiones\RutaReemplazo.cs, api_facturas\Peticiones\RutaActualizar.cs, api_facturas\Peticiones\RolUsuarioCrear.cs, api_facturas\Peticiones\RutaRolCrear.cs, api_facturas\Controllers\EmpresaController.cs, api_facturas\Controllers\ClienteController.cs, api_facturas\Controllers\VendedorController.cs, api_facturas\Controllers\UsuarioController.cs, api_facturas\Controllers\RolController.cs, api_facturas\Controllers\RutaController.cs, api_facturas\Controllers\RolUsuarioController.cs, api_facturas\Controllers\RutaRolController.cs, api_facturas\Servicios\IServicioEmpresa.cs, api_facturas\Servicios\ServicioEmpresa.cs, api_facturas\Servicios\IServicioCliente.cs, api_facturas\Servicios\ServicioCliente.cs, api_facturas\Servicios\IServicioVendedor.cs, api_facturas\Servicios\ServicioVendedor.cs, api_facturas\Servicios\IServicioUsuario.cs, api_facturas\Servicios\ServicioUsuario.cs, api_facturas\Servicios\IServicioRol.cs, api_facturas\Servicios\ServicioRol.cs, api_facturas\Servicios\IServicioRuta.cs, api_facturas\Servicios\ServicioRuta.cs, api_facturas\Servicios\IServicioRolUsuario.cs, api_facturas\Servicios\ServicioRolUsuario.cs, api_facturas\Servicios\IServicioRutaRol.cs, api_facturas\Servicios\ServicioRutaRol.cs, api_facturas\Repositorios\IRepositorioEmpresa.cs, api_facturas\Repositorios\RepositorioEmpresaPostgres.cs, api_facturas\Repositorios\IRepositorioCliente.cs, api_facturas\Repositorios\RepositorioClientePostgres.cs, api_facturas\Repositorios\IRepositorioVendedor.cs, api_facturas\Repositorios\RepositorioVendedorPostgres.cs, api_facturas\Repositorios\IRepositorioUsuario.cs, api_facturas\Repositorios\RepositorioUsuarioPostgres.cs, api_facturas\Repositorios\IRepositorioRol.cs, api_facturas\Repositorios\RepositorioRolPostgres.cs, api_facturas\Repositorios\IRepositorioRuta.cs, api_facturas\Repositorios\RepositorioRutaPostgres.cs, api_facturas\Repositorios\IRepositorioRolUsuario.cs, api_facturas\Repositorios\RepositorioRolUsuarioPostgres.cs, api_facturas\Repositorios\IRepositorioRutaRol.cs, api_facturas\Repositorios\RepositorioRutaRolPostgres.cs
   ```

4. Archivos de la v2 que **CRECEN** (la IA le entrega la versión completa
   actualizada): `Program.cs` (16 AddScoped + "v3"),
   `ApiFacturas.csproj` (paquete BCrypt.Net-Next) y
   `pruebas/Programa.cs` (repo falso de empresa).

## A.3 El prompt (los cambios sobre el de la v2)

Use el prompt de la [guía v2](../v2_persona_factura/GUIA_IA2.md) A.3
cambiando:

- "VERSIÓN 2" → "VERSIÓN 3", y el CONTEXTO CLAVE: *"Mi proyecto YA TIENE
  v1 y v2 construidas y funcionando (producto, persona y factura); NO las
  toques. Solo crecen Program.cs, ApiFacturas.csproj y pruebas/Programa.cs."*
- Regla de alcance: *"nada de JWT, tokens ni middleware (eso es de una
  versión futura); nada de CRUD para productosporfactura; el DELETE de
  las tablas puente filtra por AMBAS columnas de la clave compuesta; las
  lecturas de usuario JAMÁS devuelven la contraseña ni su hash."*
- El ancla de stack y los puertos +100 quedan igual.

## A.4 Método: igual que la v2, con una alarma extra

Si la IA le entrega un "refactor" del ensamblador (una fábrica, un
diccionario de motores, un archivo nuevo de configuración): recháselo —
[4_research.md](4_research.md) D6: Program.cs se deja crecer A PROPÓSITO;
la fábrica es el argumento de la v4.

## Cierre

El doble cierre de siempre: regresión (v1 y v2 completas) + smoke test v3
([7_quickstart.md](7_quickstart.md) §3, con sus puertos +100) → tag `v3`.
