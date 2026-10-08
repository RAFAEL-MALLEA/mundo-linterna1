from django.contrib import admin

from .models import Cliente, ContactoMensaje, ItemPedido, Pago, Pedido, Producto, TipoProducto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('ID_prod', 'nombre_prod', 'Tipo_prod', 'Precio')
    list_filter = ('Tipo_prod',)
    search_fields = ('nombre_prod',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('Nombre_cli', 'Apellido_cli', 'Email')
    search_fields = ('Nombre_cli', 'Apellido_cli', 'Email')


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    can_delete = False
    readonly_fields = ('producto', 'nombre', 'precio_unitario', 'cantidad')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'estado', 'total', 'creado')
    list_filter = ('estado',)
    readonly_fields = ('usuario', 'total', 'creado', 'actualizado')
    inlines = [ItemPedidoInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('buy_order', 'pedido', 'estado', 'monto', 'fecha')
    list_filter = ('estado',)
    search_fields = ('buy_order', 'token')

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(ContactoMensaje)
class ContactoMensajeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono', 'creado', 'leido')
    list_filter = ('leido',)


admin.site.register(TipoProducto)
