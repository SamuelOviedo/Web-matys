"""
Pruebas de flujo completo del panel /gestion-matys/ y del sitio público.

Cloudinary se mockea: `uploader.upload` devuelve un public_id falso y
`uploader.destroy` se registra para verificar que la limpieza remota ocurre.
"""
import json
from decimal import Decimal
from unittest.mock import patch

import cloudinary
from django.contrib.auth.models import User
from django.test import TestCase

from .models import Prenda, ImagenPrenda, TipoPrenda, SiteConfig
from .site_textos import DEFAULTS_TEXTOS

# Config falsa para que CloudinaryImage.build_url() funcione en tests
cloudinary.config(cloud_name='testcloud', api_key='key', api_secret='secret')


def crear_prenda(**kwargs):
    defaults = dict(
        nombre='Vestido Test',
        slug='vestido-test',
        categoria='femenino',
        tipo='vestido',
        precio=Decimal('500.00'),
        descripcion_corta='corta',
        descripcion_larga='larga',
    )
    defaults.update(kwargs)
    return Prenda.objects.create(**defaults)


class BaseStaffTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user('gestor', password='x', is_staff=True)

    def login(self):
        self.client.force_login(self.staff)


# ═══════════════════════════════ Autorización ══════════════════════════════

class AuthGuardTests(BaseStaffTestCase):
    def test_dashboard_redirige_anonimo(self):
        resp = self.client.get('/gestion-matys/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/gestion-matys/login/', resp['Location'])

    def test_endpoints_json_devuelven_403_anonimo(self):
        for url in ['/gestion-matys/prendas/crear/',
                    '/gestion-matys/prendas/1/editar/',
                    '/gestion-matys/prendas/1/eliminar/']:
            resp = self.client.post(url)
            self.assertEqual(resp.status_code, 403, url)
        resp = self.client.get('/gestion-matys/categorias/tipos-json/')
        self.assertEqual(resp.status_code, 403)

    def test_no_staff_no_entra(self):
        User.objects.create_user('cliente', password='x', is_staff=False)
        self.client.login(username='cliente', password='x')
        resp = self.client.get('/gestion-matys/')
        self.assertEqual(resp.status_code, 302)

    def test_login_y_logout(self):
        self.staff.set_password('clave-segura')
        self.staff.save()
        resp = self.client.post('/gestion-matys/login/',
                                {'username': 'gestor', 'password': 'clave-segura'})
        self.assertRedirects(resp, '/gestion-matys/')
        resp = self.client.get('/gestion-matys/logout/')
        self.assertRedirects(resp, '/')

    def test_acceso_legacy_redirige_al_login_del_panel(self):
        resp = self.client.get('/acceso/')
        self.assertRedirects(resp, '/gestion-matys/login/')


# ═══════════════════════════════ CRUD Prenda ═══════════════════════════════

@patch('matys.views.cloudinary.uploader.destroy')
@patch('matys.views.cloudinary.uploader.upload',
       return_value={'public_id': 'matys/nueva'})
class PrendaCrudTests(BaseStaffTestCase):

    def _crear_via_panel(self, files=0, **extra):
        from django.core.files.uploadedfile import SimpleUploadedFile
        data = {
            'nombre': 'Blusa Panel', 'precio': '350.50',
            'descripcion_corta': 'desc', 'categoria': 'femenino',
            'tipo': 'blusa', 'disponible': 'true', 'por_encargo': 'true',
        }
        data.update(extra)
        for i in range(files):
            data[f'imagen_{i}'] = SimpleUploadedFile(
                f'f{i}.jpg', b'bytes', content_type='image/jpeg')
        return self.client.post('/gestion-matys/prendas/crear/', data)

    def test_crear_sin_imagenes(self, mock_upload, mock_destroy):
        self.login()
        resp = self._crear_via_panel()
        self.assertTrue(resp.json()['success'])
        p = Prenda.objects.get(nombre='Blusa Panel')
        self.assertEqual(p.total_imagenes, 0)
        mock_upload.assert_not_called()

    def test_crear_con_imagenes_asigna_orden(self, mock_upload, mock_destroy):
        self.login()
        resp = self._crear_via_panel(files=3)
        self.assertTrue(resp.json()['success'])
        p = Prenda.objects.get(nombre='Blusa Panel')
        self.assertEqual(list(p.imagenes.values_list('orden', flat=True)), [0, 1, 2])
        self.assertEqual(mock_upload.call_count, 3)
        self.assertIsNotNone(p.imagen_principal)

    def test_crear_valida_tipo(self, mock_upload, mock_destroy):
        self.login()
        resp = self._crear_via_panel(tipo='tipo-inventado')
        self.assertFalse(resp.json()['success'])

    def test_crear_destacada(self, mock_upload, mock_destroy):
        self.login()
        resp = self._crear_via_panel(destacada='true')
        self.assertTrue(resp.json()['success'])
        self.assertTrue(Prenda.objects.get(nombre='Blusa Panel').destacada)

    def test_slug_unico_autoincrementa(self, mock_upload, mock_destroy):
        self.login()
        self._crear_via_panel()
        resp = self._crear_via_panel()
        self.assertTrue(resp.json()['success'])
        slugs = set(Prenda.objects.values_list('slug', flat=True))
        self.assertEqual(slugs, {'blusa-panel', 'blusa-panel-1'})

    def test_editar_get_devuelve_todo(self, mock_upload, mock_destroy):
        self.login()
        p = crear_prenda(destacada=True)
        ImagenPrenda.objects.create(prenda=p, imagen='a', orden=0)
        d = self.client.get(f'/gestion-matys/prendas/{p.pk}/editar/').json()
        self.assertEqual(d['nombre'], 'Vestido Test')
        self.assertTrue(d['destacada'])
        self.assertTrue(d['por_encargo'])
        self.assertEqual(len(d['imagenes']), 1)

    def test_editar_campos(self, mock_upload, mock_destroy):
        self.login()
        p = crear_prenda()
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': 'Editado', 'precio': '999', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'falda',
            'disponible': 'false', 'por_encargo': 'false', 'destacada': 'true',
        })
        self.assertTrue(resp.json()['success'])
        p.refresh_from_db()
        self.assertEqual((p.nombre, p.tipo, p.disponible, p.por_encargo, p.destacada),
                         ('Editado', 'falda', False, False, True))

    def test_editar_sin_por_encargo_no_lo_resetea(self, mock_upload, mock_destroy):
        """El modal de Imágenes no enviaba por_encargo/destacada: no deben resetearse."""
        self.login()
        p = crear_prenda(por_encargo=True, destacada=True)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
        })
        self.assertTrue(resp.json()['success'])
        p.refresh_from_db()
        self.assertTrue(p.por_encargo)
        self.assertTrue(p.destacada)

    def test_eliminar_imagen_destruye_en_cloudinary_y_recompacta(self, mock_upload, mock_destroy):
        self.login()
        p = crear_prenda()
        i0 = ImagenPrenda.objects.create(prenda=p, imagen='img0', orden=0)
        i1 = ImagenPrenda.objects.create(prenda=p, imagen='img1', orden=1)
        i2 = ImagenPrenda.objects.create(prenda=p, imagen='img2', orden=2)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
            'eliminar_imagen_ids': json.dumps([i0.pk]),
            'orden_imagenes': json.dumps([
                {'id': i1.pk, 'orden': 0}, {'id': i2.pk, 'orden': 1},
            ]),
        })
        self.assertTrue(resp.json()['success'])
        mock_destroy.assert_called_once_with('img0')
        ordenes = list(p.imagenes.order_by('orden').values_list('orden', flat=True))
        self.assertEqual(ordenes, [0, 1])           # re-compactado, orden=0 existe
        self.assertEqual(str(p.imagen_principal), str(p.imagenes.get(orden=0).imagen))

    def test_recompacta_aunque_no_envien_orden(self, mock_upload, mock_destroy):
        """Borrar la imagen principal sin reordenar igual debe dejar un orden=0."""
        self.login()
        p = crear_prenda()
        i0 = ImagenPrenda.objects.create(prenda=p, imagen='img0', orden=0)
        ImagenPrenda.objects.create(prenda=p, imagen='img1', orden=1)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
            'eliminar_imagen_ids': json.dumps([i0.pk]),
        })
        self.assertTrue(resp.json()['success'])
        self.assertIsNotNone(p.imagen_principal)    # antes quedaba huérfana en orden=1

    def test_no_permite_quedar_sin_imagenes(self, mock_upload, mock_destroy):
        self.login()
        p = crear_prenda()
        i0 = ImagenPrenda.objects.create(prenda=p, imagen='img0', orden=0)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
            'eliminar_imagen_ids': json.dumps([i0.pk]),
        })
        self.assertFalse(resp.json()['success'])
        self.assertEqual(p.total_imagenes, 1)
        mock_destroy.assert_not_called()

    def test_reemplazar_unica_imagen(self, mock_upload, mock_destroy):
        """Borrar la única foto Y subir una nueva en el mismo guardado: permitido."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.login()
        p = crear_prenda()
        i0 = ImagenPrenda.objects.create(prenda=p, imagen='vieja', orden=0)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
            'eliminar_imagen_ids': json.dumps([i0.pk]),
            'imagen_nueva': SimpleUploadedFile('n.jpg', b'b', content_type='image/jpeg'),
        })
        self.assertTrue(resp.json()['success'])
        mock_destroy.assert_called_once_with('vieja')
        self.assertEqual(p.total_imagenes, 1)
        img = p.imagenes.get()
        self.assertEqual((str(img.imagen), img.orden), ('matys/nueva', 0))

    def test_maximo_cuatro_imagenes(self, mock_upload, mock_destroy):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.login()
        p = crear_prenda()
        for i in range(4):
            ImagenPrenda.objects.create(prenda=p, imagen=f'i{i}', orden=i)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
            'imagen_nueva': SimpleUploadedFile('n.jpg', b'b', content_type='image/jpeg'),
        })
        self.assertFalse(resp.json()['success'])
        self.assertEqual(p.total_imagenes, 4)
        mock_upload.assert_not_called()

    def test_reordenar_imagenes(self, mock_upload, mock_destroy):
        self.login()
        p = crear_prenda()
        i0 = ImagenPrenda.objects.create(prenda=p, imagen='a', orden=0)
        i1 = ImagenPrenda.objects.create(prenda=p, imagen='b', orden=1)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/editar/', {
            'nombre': p.nombre, 'precio': '500', 'descripcion_corta': 'x',
            'categoria': 'femenino', 'tipo': 'vestido', 'disponible': 'true',
            'orden_imagenes': json.dumps([
                {'id': i1.pk, 'orden': 0}, {'id': i0.pk, 'orden': 1},
            ]),
        })
        self.assertTrue(resp.json()['success'])
        self.assertEqual(str(p.imagenes.get(orden=0).imagen), 'b')

    def test_eliminar_prenda_destruye_todas_las_imagenes(self, mock_upload, mock_destroy):
        self.login()
        p = crear_prenda()
        for i in range(3):
            ImagenPrenda.objects.create(prenda=p, imagen=f'pic{i}', orden=i)
        resp = self.client.post(f'/gestion-matys/prendas/{p.pk}/eliminar/')
        self.assertTrue(resp.json()['success'])
        self.assertFalse(Prenda.objects.filter(pk=p.pk).exists())
        self.assertEqual(mock_destroy.call_count, 3)


# ═══════════════════════ Categorías / TipoPrenda / Menú ════════════════════

class TipoPrendaTests(BaseStaffTestCase):
    def test_agregar_editar_eliminar(self):
        self.login()
        resp = self.client.post('/gestion-matys/categorias/',
                                {'action': 'agregar', 'nombre': 'Gabardina', 'categoria': 'femenino'})
        self.assertTrue(resp.json()['success'])
        tipo = TipoPrenda.objects.get(slug='gabardina')

        resp = self.client.post('/gestion-matys/categorias/',
                                {'action': 'editar', 'id': tipo.pk, 'nombre': 'Gabardina Larga'})
        self.assertTrue(resp.json()['success'])
        tipo.refresh_from_db()
        self.assertEqual(tipo.nombre, 'Gabardina Larga')
        self.assertEqual(tipo.slug, 'gabardina')  # slug estable: no rompe prendas

        resp = self.client.post('/gestion-matys/categorias/',
                                {'action': 'eliminar', 'id': tipo.pk})
        self.assertTrue(resp.json()['success'])
        self.assertFalse(TipoPrenda.objects.filter(pk=tipo.pk).exists())

    def test_no_elimina_tipo_en_uso(self):
        self.login()
        tipo = TipoPrenda.objects.create(nombre='Capa', slug='capa', categoria='femenino')
        crear_prenda(tipo='capa', slug='capa-roja')
        resp = self.client.post('/gestion-matys/categorias/',
                                {'action': 'eliminar', 'id': tipo.pk})
        self.assertFalse(resp.json()['success'])
        self.assertTrue(TipoPrenda.objects.filter(pk=tipo.pk).exists())

    def test_duplicado_misma_categoria_bloqueado(self):
        self.login()
        TipoPrenda.objects.create(nombre='Capa', slug='capa', categoria='femenino')
        resp = self.client.post('/gestion-matys/categorias/',
                                {'action': 'agregar', 'nombre': 'Capa', 'categoria': 'femenino'})
        self.assertFalse(resp.json()['success'])

    def test_menu_publico_se_actualiza_con_tipo_nuevo(self):
        """Agregar un tipo desde el panel debe aparecer al instante en /prendas/."""
        self.login()
        self.client.post('/gestion-matys/categorias/',
                         {'action': 'agregar', 'nombre': 'Poncho Andino', 'categoria': 'masculino'})
        resp = self.client.get('/prendas/')
        self.assertContains(resp, 'Poncho Andino')
        self.assertContains(resp, 'tipo=poncho-andino')

    def test_tipo_inactivo_no_aparece_en_menu(self):
        TipoPrenda.objects.create(nombre='Oculto', slug='oculto',
                                  categoria='femenino', activo=False)
        resp = self.client.get('/prendas/')
        self.assertNotContains(resp, 'Oculto')

    def test_tipos_json_filtra_por_categoria(self):
        self.login()
        TipoPrenda.objects.create(nombre='SoloFem', slug='solofem', categoria='femenino')
        TipoPrenda.objects.create(nombre='SoloMasc', slug='solomasc', categoria='masculino')
        data = self.client.get('/gestion-matys/categorias/tipos-json/?categoria=femenino').json()
        slugs = {t['slug'] for t in data['tipos']}
        self.assertIn('solofem', slugs)
        self.assertNotIn('solomasc', slugs)


# ═══════════════════════════════ Panel: páginas ════════════════════════════

class PanelPaginasTests(BaseStaffTestCase):
    def test_dashboard_renderiza_con_kpis_y_modales(self):
        self.login()
        crear_prenda()
        resp = self.client.get('/gestion-matys/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Vista general')
        self.assertContains(resp, 'editDestacada')    # nuevo toggle destacada
        self.assertContains(resp, 'createDestacada')

    def test_imagenes_renderiza_con_campos_completos(self):
        self.login()
        p = crear_prenda()
        ImagenPrenda.objects.create(prenda=p, imagen='pic', orden=0)
        resp = self.client.get('/gestion-matys/imagenes/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'editPorEncargo')   # antes faltaba y reseteaba el campo
        self.assertContains(resp, 'value="infantil"') # antes faltaba la categoría

    def test_categorias_renderiza(self):
        self.login()
        resp = self.client.get('/gestion-matys/categorias/')
        self.assertEqual(resp.status_code, 200)


# ═══════════════════════════════ Sitio público ═════════════════════════════

class SitioPublicoTests(TestCase):
    def test_inicio_solo_destacadas_disponibles(self):
        crear_prenda(slug='v1', destacada=True, disponible=True, nombre='Visible')
        crear_prenda(slug='v2', destacada=True, disponible=False, nombre='OcultaXYZ')
        resp = self.client.get('/')
        self.assertContains(resp, 'Visible')
        self.assertNotContains(resp, 'OcultaXYZ')

    def test_catalogo_filtra_por_categoria_y_tipo(self):
        crear_prenda(slug='f1', categoria='femenino', tipo='vestido', nombre='VestidoFem')
        crear_prenda(slug='m1', categoria='masculino', tipo='camisa', nombre='CamisaMasc')
        resp = self.client.get('/prendas/?categoria=masculino&tipo=camisa')
        self.assertContains(resp, 'CamisaMasc')
        self.assertNotContains(resp, 'VestidoFem')

    def test_detalle_prenda_oculta_404(self):
        crear_prenda(slug='oculta', disponible=False)
        self.assertEqual(self.client.get('/detalle_prendas/oculta/').status_code, 404)

    def test_detalle_renderiza(self):
        p = crear_prenda(slug='visible')
        ImagenPrenda.objects.create(prenda=p, imagen='pic', orden=0)
        resp = self.client.get('/detalle_prendas/visible/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Vestido Test')


# ═══════════════════════════════ CMS de textos ═════════════════════════════

class TextosCmsTests(BaseStaffTestCase):
    def test_panel_redirige_anonimo(self):
        resp = self.client.get('/gestion-matys/inicio/')
        self.assertEqual(resp.status_code, 302)

    def test_get_muestra_formulario_con_defaults(self):
        self.login()
        resp = self.client.get('/gestion-matys/inicio/')
        self.assertContains(resp, 'hero_titulo')
        self.assertContains(resp, DEFAULTS_TEXTOS['hero_titulo'])

    def test_guardar_texto_y_publicarlo(self):
        self.login()
        resp = self.client.post('/gestion-matys/inicio/',
                                {'hero_titulo': 'Alta Costura Matys'})
        self.assertTrue(resp.json()['success'])
        resp = self.client.get('/')
        self.assertContains(resp, 'Alta Costura Matys')
        self.assertNotContains(resp, '<h1 class="display-2 fw-bold enc">Confecciones Matys</h1>',
                               html=True)

    def test_vacio_restaura_default(self):
        self.login()
        self.client.post('/gestion-matys/inicio/', {'hero_titulo': 'Temporal'})
        self.client.post('/gestion-matys/inicio/', {'hero_titulo': ''})
        self.assertEqual(SiteConfig.get_solo().data, {})
        resp = self.client.get('/')
        self.assertContains(resp, DEFAULTS_TEXTOS['hero_titulo'])

    def test_valida_whatsapp_solo_digitos(self):
        self.login()
        resp = self.client.post('/gestion-matys/inicio/',
                                {'contacto_whatsapp': '+504 9826'})
        self.assertFalse(resp.json()['success'])

    def test_valida_url_redes(self):
        self.login()
        resp = self.client.post('/gestion-matys/inicio/',
                                {'red_facebook': 'facebook punto com'})
        self.assertFalse(resp.json()['success'])

    def test_whatsapp_se_propaga_a_footer_y_contacto(self):
        self.login()
        self.client.post('/gestion-matys/inicio/', {'contacto_whatsapp': '50499999999'})
        resp = self.client.get('/')
        self.assertContains(resp, 'wa.me/50499999999')
        self.assertContains(resp, 'data-whatsapp="50499999999"')
        resp = self.client.get('/contacto/')
        self.assertContains(resp, 'wa.me/50499999999')

    def test_textos_no_guardados_no_rompen_sitio(self):
        """Sin SiteConfig en DB el sitio rinde con los textos originales."""
        SiteConfig.objects.all().delete()
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, DEFAULTS_TEXTOS['quienes_titulo'])
