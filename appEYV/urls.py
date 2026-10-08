from django.urls import path

from . import views

urlpatterns = [
    # Catálogo y cuentas
    path('', views.product_list, name='product_list'),
    path('registro/', views.registro, name='registro'),
    path('contacto/', views.contacto, name='contacto'),

    # Administración de productos (solo personal)
    path('agregar-producto/', views.agregar_producto, name='agregar-producto'),
    path('listar-producto/', views.listar_productos, name='listar-productos'),
    path('modificar-producto/<int:id>/', views.modificar_producto, name='modificar-producto'),
    path('eliminar-producto/<int:id>/', views.eliminar_producto, name='eliminar-producto'),

    # Carrito (JSON)
    path('carrito/', views.carrito_detalle, name='carrito'),
    path('carrito/agregar/', views.carrito_agregar, name='carrito_agregar'),
    path('carrito/actualizar/', views.carrito_actualizar, name='carrito_actualizar'),
    path('carrito/eliminar/', views.carrito_eliminar, name='carrito_eliminar'),

    # Pago con Webpay Plus
    path('pago/', views.pago, name='pago'),
    path('iniciar-pago-transbank/', views.iniciar_pago_transbank, name='iniciar_pago_transbank'),
    path('resultado-transbank/', views.resultado_transbank, name='resultado_transbank'),
    path('pago/resultado/<str:buy_order>/', views.pago_resultado, name='pago_resultado'),
    path('mis-compras/', views.mis_compras, name='mis_compras'),
]
