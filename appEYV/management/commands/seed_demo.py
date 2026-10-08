"""
Crea datos iniciales: un superusuario y productos de ejemplo (usando las imágenes de media/img).

Uso:
    python manage.py seed_demo
    python manage.py seed_demo --admin-user admin --admin-email yo@correo.cl --admin-password MiClaveSegura123
    python manage.py seed_demo --sin-productos
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string

from appEYV.models import Producto

LINTERNA, HERRAMIENTA = 1, 2

# (archivo en media/img, nombre, tipo, precio en CLP). Precios de ejemplo.
PRODUCTOS = [
    ('1.png', 'Linterna LED recargable USB-C con estuche', LINTERNA, 12990),
    ('16.png', 'Linterna táctica LED con zoom y batería recargable', LINTERNA, 15990),
    ('20.png', 'Linterna recargable con mini linterna COB de regalo', LINTERNA, 11990),
    ('22.png', 'Mini linterna COB llavero recargable', LINTERNA, 5990),
    ('23.png', 'Linterna COB con mosquetón', LINTERNA, 6990),
    ('24.png', 'Linterna multifunción con mosquetón y abridor', LINTERNA, 8990),
    ('26.png', 'Mini linterna COB llavero multifunción', LINTERNA, 7990),
    ('28.png', 'Linterna COB llavero con gancho', LINTERNA, 6490),
    ('3.png', 'Linterna de trabajo plegable COB con imán', LINTERNA, 14990),
    ('31.png', 'Mini linterna recargable de colores', LINTERNA, 4990),
    ('34.png', 'Linterna llavero de 28 LED recargable', LINTERNA, 3990),
    ('38.png', 'Linterna LED recargable con zoom', LINTERNA, 9990),
    ('39.png', 'Linterna táctica de alta potencia con correa', LINTERNA, 17990),
    ('40.png', 'Linterna táctica LED con caja', LINTERNA, 13990),
    ('42.png', 'Foco LED de trabajo recargable con mango', LINTERNA, 24990),
    ('43.png', 'Linterna doble luz recargable', LINTERNA, 10990),
    ('44.png', 'Foco solar recargable de 500W', LINTERNA, 29990),
    ('45.png', 'Foco LED de trabajo con base y carga solar', LINTERNA, 27990),
    ('5.png', 'Linterna recargable con zoom y luz lateral', LINTERNA, 8490),
    ('53.png', 'Linterna de cabeza LED recargable', LINTERNA, 7490),
    ('56.png', 'Linterna de cabeza LED con imán', LINTERNA, 8990),
    ('6.png', 'Linterna LED recargable con indicador de batería', LINTERNA, 11490),
    ('63.png', 'Linterna multifuncional recargable X38', LINTERNA, 12490),
    ('9.png', 'Linterna LED con zoom y correa', LINTERNA, 9490),
    ('OIP.jpg', 'Linterna clásica naranja', LINTERNA, 5490),
    ('cintillo_w6126-1.png', 'Linterna de cabeza con sensor W6126 (modelo 1)', LINTERNA, 12990),
    ('cintillo_w6126-2.png', 'Linterna de cabeza con sensor W6126 (modelo 2)', LINTERNA, 12990),
    ('cintillo_w6126-3.png', 'Linterna de cabeza con sensor W6126 (modelo 3)', LINTERNA, 13490),
    ('cintillo_w6126-5.png', 'Linterna de cabeza con sensor W6126 (modelo 5)', LINTERNA, 13490),
    ('cob_w679.png', 'Linterna de cabeza COB W679', LINTERNA, 11990),
    ('multifuncional_5143.png', 'Linterna llavero multifuncional 5143', LINTERNA, 7490),
    ('66.png', 'Pistola de grapas térmicas para reparar plástico', HERRAMIENTA, 19990),
    ('67.png', 'Soldador de estaño con accesorios', HERRAMIENTA, 9990),
    ('68.png', 'Cinturón porta herramientas', HERRAMIENTA, 12990),
    ('70.png', 'Kit surtido de tubos termocontraíbles', HERRAMIENTA, 6990),
    ('71.png', 'Alicate de corte', HERRAMIENTA, 5990),
    ('72.png', 'Alicate de punta', HERRAMIENTA, 6490),
    ('73.png', 'Endoscopio USB para celular y PC', HERRAMIENTA, 14990),
    ('75.png', 'Cámara endoscopio con pantalla', HERRAMIENTA, 29990),
    ('76.png', 'Lentes de soldar con oscurecimiento automático', HERRAMIENTA, 15990),
    ('77.png', 'Set de brocas escalonadas', HERRAMIENTA, 8990),
    ('79.png', 'Pistola de calor', HERRAMIENTA, 21990),
]


class Command(BaseCommand):
    help = 'Crea un superusuario y productos de ejemplo (es seguro ejecutarlo más de una vez).'

    def add_arguments(self, parser):
        parser.add_argument('--admin-user', default='admin')
        parser.add_argument('--admin-email', default='admin@example.com')
        parser.add_argument('--admin-password', default=None,
                            help='Si se omite, se genera una contraseña aleatoria y se muestra en pantalla.')
        parser.add_argument('--sin-productos', action='store_true', help='No crear productos de ejemplo.')

    def handle(self, *args, **opciones):
        User = get_user_model()
        usuario = opciones['admin_user']

        if User.objects.filter(username=usuario).exists():
            self.stdout.write(f'El usuario "{usuario}" ya existe; no se modifica.')
        else:
            clave = opciones['admin_password'] or get_random_string(14)
            User.objects.create_superuser(usuario, opciones['admin_email'], clave)
            self.stdout.write(self.style.SUCCESS(f'Superusuario creado: {usuario}'))
            if not opciones['admin_password']:
                self.stdout.write(self.style.WARNING(f'Contraseña generada (guárdala): {clave}'))

        if opciones['sin_productos']:
            return

        creados = 0
        for archivo, nombre, tipo, precio in PRODUCTOS:
            if not (settings.MEDIA_ROOT / 'img' / archivo).exists():
                self.stdout.write(self.style.WARNING(f'Imagen no encontrada, se omite: {archivo}'))
                continue
            _, nuevo = Producto.objects.get_or_create(
                nombre_prod=nombre,
                defaults={'Tipo_prod': tipo, 'Precio': precio, 'Imagen': f'img/{archivo}'},
            )
            creados += int(nuevo)
        self.stdout.write(self.style.SUCCESS(f'Productos creados: {creados} (total: {Producto.objects.count()})'))
