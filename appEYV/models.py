from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.templatetags.static import static


class TipoProducto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    TIPOS_PROD = [
        (1, 'Linterna'),
        (2, 'Herramienta'),
    ]

    Tipo_prod = models.IntegerField(choices=TIPOS_PROD, verbose_name='Tipo de producto')
    Precio = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name='Precio (CLP)')
    nombre_prod = models.CharField(max_length=100, verbose_name='Nombre del producto')
    Imagen = models.ImageField(upload_to='img/', blank=True, null=True, verbose_name='Imagen')

    class Meta:
        ordering = ['id']

    @property
    def ID_prod(self):
        """Código visible del producto (001, 002, ...), derivado del id."""
        return f'{self.pk:03d}' if self.pk else ''

    @property
    def imagen_url(self):
        """URL de la imagen o de un placeholder si el producto no tiene imagen."""
        if self.Imagen:
            return self.Imagen.url
        return static('app/img/sin_imagen.svg')

    def __str__(self):
        return f'{self.ID_prod} - {self.nombre_prod}'


class Cliente(models.Model):
    Nombre_cli = models.CharField(max_length=30)
    Apellido_cli = models.CharField(max_length=30)
    Email = models.EmailField(unique=True)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.Nombre_cli} {self.Apellido_cli}'


class ContactoMensaje(models.Model):
    """Mensajes enviados desde el formulario de contacto del pie de página."""
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30)
    email = models.EmailField()
    mensaje = models.TextField(max_length=1000)
    creado = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f'{self.nombre} ({self.creado:%d-%m-%Y})'


class Pedido(models.Model):
    PENDIENTE = 'PENDIENTE'
    PAGADO = 'PAGADO'
    CANCELADO = 'CANCELADO'
    ESTADOS = [
        (PENDIENTE, 'Pendiente de pago'),
        (PAGADO, 'Pagado'),
        (CANCELADO, 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos'
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default=PENDIENTE)
    total = models.PositiveIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f'Pedido #{self.pk} - {self.get_estado_display()}'


class ItemPedido(models.Model):
    """Línea de un pedido. Guarda nombre y precio al momento de la compra."""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    nombre = models.CharField(max_length=100)
    precio_unitario = models.PositiveIntegerField()
    cantidad = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def __str__(self):
        return f'{self.cantidad} x {self.nombre}'


class Pago(models.Model):
    """Intento de pago con Webpay Plus asociado a un pedido."""
    INICIADO = 'INICIADO'
    AUTORIZADO = 'AUTORIZADO'
    RECHAZADO = 'RECHAZADO'
    ABORTADO = 'ABORTADO'
    ERROR = 'ERROR'
    ESTADOS = [
        (INICIADO, 'Iniciado'),
        (AUTORIZADO, 'Autorizado'),
        (RECHAZADO, 'Rechazado'),
        (ABORTADO, 'Abortado por el usuario / tiempo agotado'),
        (ERROR, 'Error (revisar)'),
    ]

    pedido = models.ForeignKey(Pedido, on_delete=models.PROTECT, related_name='pagos')
    Tipo_pago = models.CharField(max_length=30, default='Webpay Plus')
    buy_order = models.CharField(max_length=26, unique=True)
    token = models.CharField(max_length=100, unique=True, null=True, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=INICIADO)
    monto = models.PositiveIntegerField()
    codigo_autorizacion = models.CharField(max_length=20, blank=True, default='')
    tarjeta_ultimos4 = models.CharField(max_length=4, blank=True, default='')
    tipo_pago_codigo = models.CharField(max_length=5, blank=True, default='')
    cuotas = models.PositiveSmallIntegerField(default=0)
    fecha = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    datos_raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.buy_order} - {self.get_estado_display()}'
