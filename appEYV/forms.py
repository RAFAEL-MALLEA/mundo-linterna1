from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile

from .models import ContactoMensaje, Producto

TAMANO_MAX_IMAGEN = 2 * 1024 * 1024  # 2 MB


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, label='Nombres')
    last_name = forms.CharField(max_length=30, label='Apellidos')
    email = forms.EmailField(label='Correo electrónico')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo electrónico.')
        return email


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre_prod', 'Tipo_prod', 'Precio', 'Imagen']

    def clean_Imagen(self):
        imagen = self.cleaned_data.get('Imagen')
        # Solo se valida el tamaño de archivos recién subidos (no el que ya existe).
        if isinstance(imagen, UploadedFile) and imagen.size > TAMANO_MAX_IMAGEN:
            raise forms.ValidationError('La imagen no debe superar los 2 MB.')
        return imagen


class ContactoForm(forms.ModelForm):
    class Meta:
        model = ContactoMensaje
        fields = ['nombre', 'telefono', 'email', 'mensaje']
