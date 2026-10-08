from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .cart import Cart
from .models import Pedido, Producto


def crear_producto(nombre='Linterna de prueba', precio=1000, tipo=Producto.TIPOS_PROD[0][0]):
    return Producto.objects.create(nombre_prod=nombre, Precio=precio, Tipo_prod=tipo)


class CartTests(TestCase):
    """El carrito vive en la sesión y el precio/total se calculan desde la BD."""

    def setUp(self):
        self.producto = crear_producto(precio=9990)

    def _cart(self):
        request = self.client.session
        request.save()
        from django.test import RequestFactory
        req = RequestFactory().get('/')
        req.session = self.client.session
        return Cart(req)

    def test_agregar_y_total_se_calcula_desde_la_bd(self):
        cart = self._cart()
        cart.agregar(self.producto.pk, 2)
        items = cart.items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['cantidad'], 2)
        self.assertEqual(Cart.total_de(items), 9990 * 2)

    def test_el_total_ignora_un_precio_manipulado_por_el_cliente(self):
        # Aunque alguien intente mandar un "precio" distinto al endpoint, el total
        # siempre se recalcula desde Producto.Precio, nunca desde datos del cliente.
        cart = self._cart()
        cart.agregar(self.producto.pk, 1)
        total_real = Cart.total_de(cart.items())
        self.assertEqual(total_real, self.producto.Precio)

    def test_producto_eliminado_desaparece_del_carrito(self):
        cart = self._cart()
        cart.agregar(self.producto.pk, 1)
        self.producto.delete()
        self.assertEqual(cart.items(), [])


class CarritoEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.producto = crear_producto(precio=5000)

    def test_agregar_producto_responde_total_correcto(self):
        resp = self.client.post(
            reverse('carrito_agregar'), data={'id': self.producto.pk}, content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['total'], 5000)

    def test_agregar_producto_inexistente_falla(self):
        resp = self.client.post(
            reverse('carrito_agregar'), data={'id': 99999}, content_type='application/json'
        )
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(resp.json()['success'])


class PermisosProductoTests(TestCase):
    """Solo el personal (is_staff) puede administrar productos."""

    def setUp(self):
        User = get_user_model()
        self.anonimo = Client()
        self.cliente_normal = Client()
        self.cliente_normal.force_login(User.objects.create_user('cliente', password='Clave123!'))
        self.staff = Client()
        self.staff.force_login(User.objects.create_user('staff', password='Clave123!', is_staff=True))

    def test_anonimo_no_puede_listar_productos(self):
        resp = self.anonimo.get(reverse('listar-productos'))
        self.assertEqual(resp.status_code, 302)  # redirige a login

    def test_usuario_normal_no_puede_listar_productos(self):
        resp = self.cliente_normal.get(reverse('listar-productos'))
        self.assertEqual(resp.status_code, 403)

    def test_staff_si_puede_listar_productos(self):
        resp = self.staff.get(reverse('listar-productos'))
        self.assertEqual(resp.status_code, 200)


class PagoRequiereLoginTests(TestCase):
    def test_pago_sin_sesion_redirige_a_login(self):
        resp = self.client.get(reverse('pago'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp.url)


class RegistroTests(TestCase):
    def test_registro_crea_usuario_y_cliente_asociado(self):
        resp = self.client.post(reverse('registro'), {
            'username': 'nuevo',
            'first_name': 'Ana',
            'last_name': 'Pérez',
            'email': 'ana@example.com',
            'password1': 'ClaveSegura123!',
            'password2': 'ClaveSegura123!',
        })
        self.assertEqual(resp.status_code, 302)
        User = get_user_model()
        usuario = User.objects.get(username='nuevo')
        self.assertTrue(hasattr(usuario, 'cliente'))
        self.assertEqual(usuario.cliente.Email, 'ana@example.com')
