import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Tipo_prod', models.IntegerField(choices=[(1, 'Linterna'), (2, 'Herramienta')], verbose_name='Tipo de producto')),
                ('Precio', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Precio (CLP)')),
                ('nombre_prod', models.CharField(max_length=100, verbose_name='Nombre del producto')),
                ('Imagen', models.ImageField(blank=True, null=True, upload_to='img/', verbose_name='Imagen')),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Nombre_cli', models.CharField(max_length=30)),
                ('Apellido_cli', models.CharField(max_length=30)),
                ('Email', models.EmailField(max_length=254, unique=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ContactoMensaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('telefono', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('mensaje', models.TextField(max_length=1000)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('leido', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-creado'],
            },
        ),
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente de pago'), ('PAGADO', 'Pagado'), ('CANCELADO', 'Cancelado')], default='PENDIENTE', max_length=10)),
                ('total', models.PositiveIntegerField(default=0)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='pedidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-creado'],
            },
        ),
        migrations.CreateModel(
            name='ItemPedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('precio_unitario', models.PositiveIntegerField()),
                ('cantidad', models.PositiveIntegerField()),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='appEYV.pedido')),
                ('producto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='appEYV.producto')),
            ],
        ),
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Tipo_pago', models.CharField(default='Webpay Plus', max_length=30)),
                ('buy_order', models.CharField(max_length=26, unique=True)),
                ('token', models.CharField(blank=True, max_length=100, null=True, unique=True)),
                ('estado', models.CharField(choices=[('INICIADO', 'Iniciado'), ('AUTORIZADO', 'Autorizado'), ('RECHAZADO', 'Rechazado'), ('ABORTADO', 'Abortado por el usuario / tiempo agotado'), ('ERROR', 'Error (revisar)')], default='INICIADO', max_length=12)),
                ('monto', models.PositiveIntegerField()),
                ('codigo_autorizacion', models.CharField(blank=True, default='', max_length=20)),
                ('tarjeta_ultimos4', models.CharField(blank=True, default='', max_length=4)),
                ('tipo_pago_codigo', models.CharField(blank=True, default='', max_length=5)),
                ('cuotas', models.PositiveSmallIntegerField(default=0)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('actualizado', models.DateTimeField(auto_now=True)),
                ('datos_raw', models.JSONField(blank=True, default=dict)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pagos', to='appEYV.pedido')),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
    ]
