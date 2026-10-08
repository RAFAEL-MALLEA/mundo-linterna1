/*
 * Carrito de compras (cliente).
 * El navegador solo muestra lo que responde el servidor: el carrito vive en la
 * sesión del servidor y el total se calcula allí, nunca en el navegador.
 */
(function () {
    'use strict';

    var sidebar = document.getElementById('cart-sidebar');
    if (!sidebar) { return; }

    var csrf = document.querySelector('meta[name="csrf-token"]').content;
    var urls = {
        detail: sidebar.dataset.urlDetail,
        add: sidebar.dataset.urlAdd,
        update: sidebar.dataset.urlUpdate,
        remove: sidebar.dataset.urlRemove
    };
    var placeholder = sidebar.dataset.placeholder;

    var elItems = document.getElementById('cart-items');
    var elTotal = document.getElementById('cart-total');
    var elBadge = document.getElementById('cart-badge');
    var elEmpty = document.getElementById('cart-empty');
    var elError = document.getElementById('cart-error');
    var elCheckout = document.getElementById('checkout-btn');

    var clp = new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 });

    function mostrarError(mensaje) {
        elError.textContent = mensaje || '';
        elError.classList.toggle('d-none', !mensaje);
    }

    function pedir(url, metodo, datos) {
        var opciones = { method: metodo, credentials: 'same-origin', headers: {} };
        if (metodo === 'POST') {
            opciones.headers['Content-Type'] = 'application/json';
            opciones.headers['X-CSRFToken'] = csrf;
            opciones.body = JSON.stringify(datos || {});
        }
        return fetch(url, opciones).then(function (resp) {
            return resp.json().catch(function () { return {}; }).then(function (cuerpo) {
                if (!resp.ok || !cuerpo.success) {
                    throw new Error(cuerpo.error || 'No se pudo completar la operación.');
                }
                return cuerpo;
            });
        });
    }

    function crear(etiqueta, clases, texto) {
        var el = document.createElement(etiqueta);
        if (clases) { el.className = clases; }
        if (texto !== undefined) { el.textContent = texto; }
        return el;
    }

    function boton(texto, accion, id, clases, etiquetaAria) {
        var b = crear('button', clases, texto);
        b.type = 'button';
        b.dataset.action = accion;
        b.dataset.id = id;
        if (etiquetaAria) { b.setAttribute('aria-label', etiquetaAria); }
        return b;
    }

    // Se construye el DOM con textContent (nunca innerHTML) para evitar XSS.
    function render(carrito) {
        elItems.textContent = '';
        carrito.items.forEach(function (item) {
            var li = crear('li', 'list-group-item');

            var fila = crear('div', 'd-flex align-items-center gap-2');
            var img = crear('img', 'thumb-sm');
            img.alt = '';
            img.src = item.imagen;
            img.onerror = function () { img.onerror = null; img.src = placeholder; };
            var info = crear('div', 'flex-grow-1');
            info.appendChild(crear('div', 'fw-semibold', item.nombre));
            info.appendChild(crear('small', 'text-muted', clp.format(item.precio) + ' c/u'));
            fila.appendChild(img);
            fila.appendChild(info);
            fila.appendChild(crear('span', 'fw-bold', clp.format(item.subtotal)));

            var acciones = crear('div', 'd-flex align-items-center gap-1 mt-2');
            acciones.appendChild(boton('\u2212', 'dec', item.id, 'btn btn-sm btn-outline-secondary', 'Quitar una unidad'));
            acciones.appendChild(crear('span', 'px-2', String(item.cantidad)));
            acciones.appendChild(boton('+', 'inc', item.id, 'btn btn-sm btn-outline-secondary', 'Agregar una unidad'));
            var quitar = boton('Eliminar', 'del', item.id, 'btn btn-sm btn-outline-danger ms-auto');
            acciones.appendChild(quitar);

            li.appendChild(fila);
            li.appendChild(acciones);
            li.dataset.cantidad = item.cantidad;
            li.dataset.id = item.id;
            elItems.appendChild(li);
        });

        var vacio = carrito.items.length === 0;
        elEmpty.classList.toggle('d-none', !vacio);
        elTotal.textContent = clp.format(carrito.total);
        elBadge.textContent = carrito.count;
        elCheckout.classList.toggle('disabled', vacio);
        elCheckout.setAttribute('aria-disabled', vacio ? 'true' : 'false');
    }

    function abrir() {
        bootstrap.Offcanvas.getOrCreateInstance(sidebar).show();
    }

    function ejecutar(promesa, abrirCarrito) {
        mostrarError('');
        return promesa.then(function (carrito) {
            render(carrito);
            if (abrirCarrito) { abrir(); }
        }).catch(function (error) {
            mostrarError(error.message);
            if (abrirCarrito) { abrir(); }
        });
    }

    // Agregar desde el catálogo
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.add-to-cart');
        if (!btn) { return; }
        ejecutar(pedir(urls.add, 'POST', { id: btn.dataset.id }), true);
    });

    // Acciones dentro del carrito (+, -, eliminar)
    elItems.addEventListener('click', function (e) {
        var btn = e.target.closest('button[data-action]');
        if (!btn) { return; }
        var id = btn.dataset.id;
        var li = btn.closest('li');
        var cantidad = parseInt(li.dataset.cantidad, 10);

        if (btn.dataset.action === 'del') {
            ejecutar(pedir(urls.remove, 'POST', { id: id }));
        } else {
            var nueva = btn.dataset.action === 'inc' ? cantidad + 1 : cantidad - 1;
            ejecutar(pedir(urls.update, 'POST', { id: id, cantidad: nueva }));
        }
    });

    // Evita ir a pagar con el carrito vacío
    elCheckout.addEventListener('click', function (e) {
        if (elCheckout.classList.contains('disabled')) { e.preventDefault(); }
    });

    // Carga inicial del carrito desde el servidor
    ejecutar(pedir(urls.detail, 'GET'));
})();
