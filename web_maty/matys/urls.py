from django.urls import path
from . import views

## Direccionamiento para servidor de imagenes

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('prendas/', views.prendas, name='prendas'),
    path('detalle_prendas/', views.detalle_prendas, name='detalle_prendas'),
    path('trayectoria/', views.trayectoria, name='trayectoria'),
    path('contacto/', views.contacto, name='contacto'),
    ]