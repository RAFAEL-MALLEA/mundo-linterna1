"""Acceso al SDK de Transbank (Webpay Plus). El SDK se importa solo cuando se necesita."""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_transaction():
    """Devuelve un objeto Transaction configurado según EYV/settings.py (TEST o LIVE)."""
    from transbank.common.integration_type import IntegrationType
    from transbank.common.options import WebpayOptions
    from transbank.webpay.webpay_plus.transaction import Transaction

    codigo = settings.TRANSBANK_COMMERCE_CODE
    api_key = settings.TRANSBANK_API_KEY
    if not codigo or not api_key:
        raise ImproperlyConfigured('Faltan TRANSBANK_COMMERCE_CODE / TRANSBANK_API_KEY.')

    tipo = IntegrationType.LIVE if settings.TRANSBANK_ENVIRONMENT == 'LIVE' else IntegrationType.TEST
    return Transaction(WebpayOptions(codigo, api_key, tipo))
