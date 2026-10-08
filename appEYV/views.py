import json
import logging
import time
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from . import webpay
from .cart import Cart
from .forms import ContactoForm, CustomUserCreationForm, ProductoForm
from .models import Cliente, ItemPedido, Pago, Pedido, Producto

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def staff_required(vista):
    """Exige sesión iniciada y que el usuario sea personal (is_staff)."""
    @login_required
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return vista(request, *args, **kwargs)
    return envoltura


# ---------------------------------------------------------------------------
# Catálogo
# ---------------------------------------------------------------------------
def product_list(request):
    tipo = request.GET.get('tipo')
    q = (request.GET.get('q') or '').strip()
    productos = Producto.objects.all()

    tipo_valor = None
    if tipo:
        try:
            tipo_valor = int(tipo)
        except ValueError:
            tipo_valor = None
        if tipo_valor is not None:
            productos = productos.filter(Tipo_prod=tipo_valor)

    if q:
        productos = productos.filter(nombre_prod__icontains=q)

    page_obj = Paginator(productos, 12).get_page(request.GET.get('page'))

    parametros = request.GET.copy()
    parametros.pop('page', None)

    return render(request, 'app/home.html', {
        'page_obj': page_obj,
        'tipo': tipo_valor,
        'q': q,
        'tipos': Producto.TIPOS_PROD,
        'querystring': parametros.urlencode(),
    })


# ---------------------------------------------------------------------------
# Cuentas
# ---------------------------------------------------------------------------
def registro(request):
    if request.user.is_authenticated:
        return redirect('product_list')

    formulario = CustomUserCreationForm(request.POST or None)
    if request.method == 'POST' and formulario.is_valid():
        with transaction.atomic():
            user = formulario.save()
            Cliente.objects.create(
                usuario=user,
                Nombre_cli=user.first_name,
                Apellido_cli=user.last_name,
                Email=user.email,
            )
        login(request, user)
        messages.success(request, '¡Registro correcto! Bienvenido a Mundo Linterna.')
        return redirect('product_list')
    return render(request, 'registration/registro.html', {'form': formulario})


# ---------------------------------------------------------------------------
# Contacto
# ---------------------------------------------------------------------------
@require_POST
def contacto(request):
    formulario = ContactoForm(request.POST)
    if formulario.is_valid():
        formulario.save()
        messages.success(request, 'Recibimos tu mensaje. Te contactaremos pronto.')
    else:
        messages.error(request, 'No pudimos enviar tu mensaje. Revisa los datos e inténtalo de nuevo.')

    destino = request.META.get('HTTP_REFERER', '')
    if not url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}):
        destino = reverse('product_list')
    return redirect(destino)


# ---------------------------------------------------------------------------
# Administración de productos (solo personal)
# ---------------------------------------------------------------------------
@staff_required
def listar_productos(request):
    return render(request, 'app/producto/listar.html', {'productos': Producto.objects.all()})


@staff_required
def agregar_producto(request):
    formulario = ProductoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and formulario.is_valid():
        formulario.save()
        messages.success(request, 'Producto guardado correctamente.')
        return redirect('listar-productos')
    return render(request, 'app/producto/agregar.html', {'form': formulario})


@staff_required
def modificar_producto(request, id):
    producto = get_object_or_404(Producto, pk=id)
    formulario = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if request.method == 'POST' and formulario.is_valid():
        formulario.save()
        messages.success(request, 'Producto modificado correctamente.')
        return redirect('listar-productos')
    return render(request, 'app/producto/modificar.html', {'form': formulario, 'producto': producto})


@staff_required
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, pk=id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('listar-productos')
    return render(request, 'app/producto/eliminar_confirmacion.html', {'producto': producto})


# ---------------------------------------------------------------------------
# Carrito (JSON). El total siempre lo calcula el servidor.
# ---------------------------------------------------------------------------
def _payload_carrito(cart):
    items = cart.items()
    return {
        'success': True,
        'count': sum(i['cantidad'] for i in items),
        'total': Cart.total_de(items),
        'items': [{
            'id': i['producto'].pk,
            'nombre': i['producto'].nombre_prod,
            'imagen': i['producto'].imagen_url,
            'precio': i['precio'],
            'cantidad': i['cantidad'],
            'subtotal': i['subtotal'],
        } for i in items],
    }


def _error_json(mensaje, status=400):
    return JsonResponse({'success': False, 'error': mensaje}, status=status)


def _leer_json(request):
    try:
        datos = json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return None
    return datos if isinstance(datos, dict) else None


def _leer_id_producto(datos):
    try:
        return int(datos['id'])
    except (KeyError, TypeError, ValueError):
        return None


@require_http_methods(['GET'])
def carrito_detalle(request):
    return JsonResponse(_payload_carrito(Cart(request)))


@require_POST
def carrito_agregar(request):
    datos = _leer_json(request)
    producto_id = _leer_id_producto(datos or {})
    if producto_id is None:
        return _error_json('Solicitud inválida.')
    if not Producto.objects.filter(pk=producto_id).exists():
        return _error_json('El producto no existe.', 404)
    cart = Cart(request)
    cart.agregar(producto_id)
    return JsonResponse(_payload_carrito(cart))


@require_POST
def carrito_actualizar(request):
    datos = _leer_json(request) or {}
    producto_id = _leer_id_producto(datos)
    try:
        cantidad = int(datos['cantidad'])
    except (KeyError, TypeError, ValueError):
        cantidad = None
    if producto_id is None or cantidad is None:
        return _error_json('Solicitud inválida.')
    if not Producto.objects.filter(pk=producto_id).exists():
        return _error_json('El producto no existe.', 404)
    cart = Cart(request)
    cart.establecer(producto_id, cantidad)
    return JsonResponse(_payload_carrito(cart))


@require_POST
def carrito_eliminar(request):
    producto_id = _leer_id_producto(_leer_json(request) or {})
    if producto_id is None:
        return _error_json('Solicitud inválida.')
    cart = Cart(request)
    cart.quitar(producto_id)
    return JsonResponse(_payload_carrito(cart))


# ---------------------------------------------------------------------------
# Pago con Webpay Plus (Transbank)
# ---------------------------------------------------------------------------
@login_required
def pago(request):
    """Resumen del pedido antes de ir a Webpay."""
    items = Cart(request).items()
    if not items:
        messages.info(request, 'Tu carrito está vacío.')
        return redirect('product_list')
    return render(request, 'app/pago.html', {'items': items, 'total': Cart.total_de(items)})


@login_required
@require_POST
def iniciar_pago_transbank(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        messages.info(request, 'Tu carrito está vacío.')
        return redirect('product_list')
    total = Cart.total_de(items)

    # 1) Se crea el pedido con los precios actuales de la BD y un intento de pago.
    with transaction.atomic():
        pedido = Pedido.objects.create(usuario=request.user, total=total)
        ItemPedido.objects.bulk_create([
            ItemPedido(
                pedido=pedido,
                producto=i['producto'],
                nombre=i['producto'].nombre_prod,
                precio_unitario=i['precio'],
                cantidad=i['cantidad'],
            ) for i in items
        ])
        buy_order = f'MLP-{pedido.pk}-{int(time.time())}'  # máx. 26 caracteres
        pago_obj = Pago.objects.create(pedido=pedido, buy_order=buy_order, monto=total)

    # 2) Se crea la transacción en Webpay (fuera de la transacción de BD).
    return_url = request.build_absolute_uri(reverse('resultado_transbank'))
    session_id = request.session.session_key or f'pedido-{pedido.pk}'
    try:
        respuesta = webpay.get_transaction().create(buy_order, session_id, total, return_url)
        token, url = respuesta['token'], respuesta['url']
    except Exception:
        logger.exception('No se pudo crear la transacción Webpay (buy_order=%s)', buy_order)
        pago_obj.estado = Pago.ERROR
        pago_obj.save(update_fields=['estado', 'actualizado'])
        messages.error(request, 'No pudimos conectar con Webpay. Inténtalo nuevamente en unos minutos.')
        return redirect('pago')

    pago_obj.token = token
    pago_obj.save(update_fields=['token', 'actualizado'])
    request.session['pedido_id'] = pedido.pk
    return render(request, 'app/webpay_redirect.html', {'url': url, 'token': token})


def _a_entero(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _confirmar_pago(pago_obj):
    """Confirma (commit) la transacción en Webpay y actualiza pago y pedido. Es idempotente."""
    if pago_obj.estado != Pago.INICIADO:
        return

    respuesta, error = None, None
    try:
        respuesta = webpay.get_transaction().commit(pago_obj.token)
    except Exception as exc:
        logger.exception('Error al confirmar pago Webpay (buy_order=%s)', pago_obj.buy_order)
        error = str(exc)

    with transaction.atomic():
        pago_obj = Pago.objects.select_for_update().select_related('pedido').get(pk=pago_obj.pk)
        if pago_obj.estado != Pago.INICIADO:  # otro proceso ya lo resolvió
            return

        if error is not None or not isinstance(respuesta, dict):
            pago_obj.estado = Pago.ERROR
            pago_obj.datos_raw = {'error': error or 'Respuesta inesperada de Webpay'}
            pago_obj.save()
            return

        pago_obj.datos_raw = respuesta
        autorizado = respuesta.get('status') == 'AUTHORIZED' and respuesta.get('response_code') == 0

        if not autorizado:
            pago_obj.estado = Pago.RECHAZADO
        elif _a_entero(respuesta.get('amount')) != pago_obj.monto or pago_obj.monto != pago_obj.pedido.total:
            # Webpay autorizó un monto distinto al esperado: se deja marcado para revisión manual.
            logger.error('Monto inconsistente en pago %s: %s', pago_obj.buy_order, respuesta)
            pago_obj.estado = Pago.ERROR
        else:
            pago_obj.estado = Pago.AUTORIZADO
            pago_obj.codigo_autorizacion = str(respuesta.get('authorization_code') or '')[:20]
            pago_obj.tarjeta_ultimos4 = str((respuesta.get('card_detail') or {}).get('card_number') or '')[-4:]
            pago_obj.tipo_pago_codigo = str(respuesta.get('payment_type_code') or '')[:5]
            pago_obj.cuotas = _a_entero(respuesta.get('installments_number')) or 0
            pago_obj.pedido.estado = Pedido.PAGADO
            pago_obj.pedido.save(update_fields=['estado', 'actualizado'])
        pago_obj.save()


def _marcar_abortado(pago_obj, datos):
    with transaction.atomic():
        pago_obj = Pago.objects.select_for_update().get(pk=pago_obj.pk)
        if pago_obj.estado == Pago.INICIADO:
            pago_obj.estado = Pago.ABORTADO
            pago_obj.datos_raw = {k: v for k, v in datos.items() if k.startswith('TBK_') or k == 'token_ws'}
            pago_obj.save()


@csrf_exempt  # Webpay vuelve con un POST desde otro dominio, sin token CSRF. No depende de la sesión.
@require_http_methods(['GET', 'POST'])
def resultado_transbank(request):
    datos = request.POST if request.method == 'POST' else request.GET
    token = datos.get('token_ws')
    tbk_token = datos.get('TBK_TOKEN')
    tbk_orden = datos.get('TBK_ORDEN_COMPRA')
    pago_obj = None

    if tbk_token or tbk_orden:
        # Pago abortado, tiempo agotado o error en el formulario: no hay nada que confirmar.
        if tbk_token:
            pago_obj = Pago.objects.filter(token=tbk_token).first()
        if pago_obj is None and tbk_orden:
            pago_obj = Pago.objects.filter(buy_order=tbk_orden).first()
        if pago_obj is not None:
            _marcar_abortado(pago_obj, datos)
    elif token:
        pago_obj = Pago.objects.filter(token=token).first()
        if pago_obj is not None:
            _confirmar_pago(pago_obj)

    if pago_obj is None:
        messages.error(request, 'No pudimos identificar la transacción.')
        return redirect('product_list')
    return redirect('pago_resultado', buy_order=pago_obj.buy_order)


@login_required
def pago_resultado(request, buy_order):
    pago_obj = get_object_or_404(
        Pago.objects.select_related('pedido').prefetch_related('pedido__items'),
        buy_order=buy_order,
        pedido__usuario=request.user,
    )
    # Si el pago fue exitoso, se vacía el carrito que originó este pedido.
    if pago_obj.estado == Pago.AUTORIZADO and request.session.get('pedido_id') == pago_obj.pedido_id:
        Cart(request).vaciar()
        del request.session['pedido_id']
    return render(request, 'app/pago_resultado.html', {'pago': pago_obj, 'pedido': pago_obj.pedido})


@login_required
def mis_compras(request):
    pedidos = (
        Pedido.objects.filter(usuario=request.user, estado=Pedido.PAGADO)
        .prefetch_related('items', 'pagos')
    )
    return render(request, 'app/mis_compras.html', {'pedidos': pedidos})
