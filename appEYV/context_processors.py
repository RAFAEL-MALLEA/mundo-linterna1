from .cart import Cart


def carrito(request):
    """Expone la cantidad de unidades del carrito a todas las plantillas."""
    return {'cart_count': len(Cart(request))}
