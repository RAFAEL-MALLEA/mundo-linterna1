"""
Carrito de compras guardado en la sesión del servidor.

En la sesión solo se guarda {id_producto: cantidad}. Los precios y el total se
calculan SIEMPRE desde la base de datos, así el navegador no puede alterarlos.
"""
from .models import Producto

MAX_CANTIDAD = 99


class Cart:
    SESSION_KEY = 'cart'

    def __init__(self, request):
        self.session = request.session
        self._cart = dict(self.session.get(self.SESSION_KEY, {}))

    def _guardar(self):
        self.session[self.SESSION_KEY] = self._cart
        self.session.modified = True

    def agregar(self, producto_id, cantidad=1):
        clave = str(producto_id)
        self._cart[clave] = min(self._cart.get(clave, 0) + cantidad, MAX_CANTIDAD)
        self._guardar()

    def establecer(self, producto_id, cantidad):
        if cantidad <= 0:
            self.quitar(producto_id)
            return
        self._cart[str(producto_id)] = min(cantidad, MAX_CANTIDAD)
        self._guardar()

    def quitar(self, producto_id):
        if self._cart.pop(str(producto_id), None) is not None:
            self._guardar()

    def vaciar(self):
        self._cart = {}
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True

    def items(self):
        """Lista de dicts con producto, cantidad, precio y subtotal (precios actuales de la BD)."""
        ids = [int(k) for k in self._cart]
        productos = Producto.objects.in_bulk(ids)
        resultado = []
        cambio = False
        for clave, cantidad in list(self._cart.items()):
            producto = productos.get(int(clave))
            if producto is None:  # el producto fue eliminado
                del self._cart[clave]
                cambio = True
                continue
            resultado.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio': producto.Precio,
                'subtotal': producto.Precio * cantidad,
            })
        if cambio:
            self._guardar()
        return resultado

    @staticmethod
    def total_de(items):
        return sum(i['subtotal'] for i in items)

    def __len__(self):
        """Cantidad total de unidades en el carrito (sin consultar la BD)."""
        return sum(self._cart.values())
