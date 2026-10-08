# Mundo Linterna

Tienda en línea desarrollada con **Django**, **HTML**, **CSS** y **JavaScript**, con carrito
de compras y pago con **Webpay Plus (Transbank)**.

Este proyecto es una versión limpia y corregida de uno anterior. Se mantuvieron las mismas
tecnologías y la misma estructura (`EYV` como proyecto, `appEYV` como app), pero se
corrigieron fallas de seguridad y de funcionamiento. Al final de este archivo hay un
resumen de qué cambió y por qué.

## Requisitos

- Python 3.10 o superior

## Instalación

```bash
# 1) Entorno virtual
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 2) Dependencias
pip install -r requirements.txt

# 3) Variables de entorno
cp .env.example .env
# Genera una SECRET_KEY y pégala en .env:
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"

# 4) Base de datos
python manage.py migrate

# 5) Datos de ejemplo (crea un superusuario y carga los productos de ejemplo)
python manage.py seed_demo
# o indicando usuario/clave propios:
python manage.py seed_demo --admin-user admin --admin-password "UnaClaveSegura123"

# 6) Ejecutar
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. El panel de administración está en
`http://127.0.0.1:8000/SeguridadAdministrativa/`.

## Pruebas

```bash
python manage.py test
```

## Pagos (Webpay Plus)

Por defecto el proyecto usa las credenciales **públicas de integración** de Transbank
(`TRANSBANK_ENVIRONMENT=TEST` en `.env`), así que puedes probar una compra completa sin
contratar nada. Transbank publica tarjetas de prueba en su documentación oficial
(developers.transbank.cl) para simular pagos aprobados y rechazados.

Para producción, solicita tus credenciales reales a Transbank y en `.env` define:

```
TRANSBANK_ENVIRONMENT=LIVE
TRANSBANM_COMMERCE_CODE=tu_codigo_de_comercio
TRANSBANK_API_KEY=tu_api_key
```

y además `DJANGO_DEBUG=False`, `DJANGO_HTTPS=True` y un `DJANGO_ALLOWED_HOSTS` con tu dominio real.

## Estructura

```
EYV/            Configuración del proyecto (settings, urls)
appEYV/         La aplicación: modelos, vistas, formularios, carrito, Webpay
  static/app/   CSS y JS propios
  templates/    Plantillas HTML
  management/commands/seed_demo.py   Comando para cargar datos de ejemplo
media/img/      Imágenes de productos
```

## Qué cambió respecto a la versión original

**Seguridad**
- Las páginas para agregar, modificar, eliminar y listar productos ahora exigen sesión
  iniciada y permiso de personal (`is_staff`); antes eran públicas.
- El carrito y el total de la compra se calculan siempre en el servidor a partir del
  precio guardado en la base de datos. El navegador ya no puede alterar el precio.
- Se quitaron los `@csrf_exempt` que no correspondían.
- `SECRET_KEY`, credenciales de Webpay y `DEBUG` ahora se leen desde variables de entorno
  (`.env`), no quedan escritas en el código. `db.sqlite3` y `.env` están en `.gitignore`.

**Pago**
- Se dejó un solo medio de pago, **Webpay Plus**, en pesos chilenos (se había detectado que
  el medio alternativo cobraba los precios en CLP pero como si fueran USD).
- Se agregó la vista de retorno (`/resultado-transbank/`) que faltaba: confirma la
  transacción con Transbank, valida el monto y el estado, y recién ahí marca el pedido
  como pagado.
- Cada intento de pago usa una orden de compra única; antes era un valor fijo que
  Transbank habría rechazado al repetirse.
- Se agregó una página de resultado (éxito, rechazo o cancelación) y el carrito se vacía
  automáticamente solo cuando el pago fue autorizado.

**Modelos**
- Se quitaron los modelos que no se usaban en ninguna parte (`Venta`, `Factura`, `Compra`,
  `MedioPago`, `DetalleVenta`, `Administrador`, `Usuario`).
- Se agregaron `Pedido`, `ItemPedido` y se reescribió `Pago` para que un pago quede
  siempre ligado a un pedido y a sus productos.

**Limpieza**
- Se eliminaron las plantillas y vistas que no funcionaban o estaban duplicadas
  (`crearcuenta.html`, el formulario de tarjeta en `pedido.html`, las vistas y
  funciones de JavaScript repetidas).
- Se quitaron imágenes de prueba sin relación con la tienda y los duplicados idénticos
  en `media/img`.
- El buscador y los filtros por tipo ahora funcionan de verdad (antes comparaban con una
  variable inexistente y una función de JavaScript que no estaba definida).
- La página principal ya no falla cuando un producto no tiene imagen: se muestra un
  ícono de reemplazo.
