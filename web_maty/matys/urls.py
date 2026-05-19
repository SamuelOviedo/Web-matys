from django.urls import path
from . import views


## Direccionamiento para servidor de imagenes

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('prendas/', views.prendas, name='prendas'),
    path('detalle_prendas/<slug:slug>/', views.detalle_prendas, name='detalle_prendas'),
    path('trayectoria/', views.trayectoria, name='trayectoria'),
    path('contacto/', views.contacto, name='contacto'),
    path('acceso/', views.admin_login, name='admin_login'),
    path('gestion-matys/', views.gestion_dashboard, name='gestion_dashboard'),
    path('gestion-matys/login/', views.gestion_login, name='gestion_login'),
    path('gestion-matys/logout/', views.gestion_logout, name='gestion_logout'),
    path('gestion-matys/categorias/', views.gestion_categorias, name='gestion_categorias'),
    path('gestion-matys/imagenes/', views.gestion_imagenes, name='gestion_imagenes'),
    path('gestion-matys/inicio/', views.gestion_inicio, name='gestion_inicio'),
]