# Textos editables del sitio público.
# Cada campo tiene un default = el texto original del diseño.
# El cliente edita estos textos desde /gestion-matys/inicio/.
# Si un campo guardado está vacío, se usa el default automáticamente.

SECCIONES_TEXTOS = [
    {
        'key': 'hero',
        'titulo': 'Portada (Hero)',
        'icono': 'bi-image',
        'descripcion': 'Lo primero que se ve al entrar al sitio.',
        'campos': [
            {'key': 'hero_titulo', 'label': 'Título principal', 'widget': 'input',
             'default': "Confecciones Matys"},
            {'key': 'hero_subtitulo', 'label': 'Subtítulo', 'widget': 'input',
             'default': "Confeccionando con amor y gratitud"},
            {'key': 'hero_boton', 'label': 'Texto del botón', 'widget': 'input',
             'default': "Ver Colección"},
        ],
    },
    {
        'key': 'quienes',
        'titulo': 'Quiénes somos',
        'icono': 'bi-people',
        'descripcion': 'Sección "Nuestra Pasión" de la página de inicio.',
        'campos': [
            {'key': 'quienes_eyebrow', 'label': 'Etiqueta superior', 'widget': 'input',
             'default': "Nuestra Pasión"},
            {'key': 'quienes_titulo', 'label': 'Título', 'widget': 'input',
             'default': "Creando Moda con Tradición"},
            {'key': 'quienes_parrafo1', 'label': 'Primer párrafo', 'widget': 'textarea',
             'default': "En Matys, transformamos telas en obras de arte. Cada prenda es "
                        "confeccionada con dedicación, precisión y un profundo respeto por la elegancia."},
            {'key': 'quienes_parrafo2', 'label': 'Segundo párrafo', 'widget': 'textarea',
             'default': "Especializados en vestidos, blusas, trajes formales y prendas a medida, "
                        "llevamos años vistiendo a quienes valoran la calidad y el estilo personal."},
            {'key': 'quienes_boton', 'label': 'Texto del botón', 'widget': 'input',
             'default': "Conoce Nuestra Historia"},
        ],
    },
    {
        'key': 'especialidades',
        'titulo': 'Nuestras Especialidades',
        'icono': 'bi-scissors',
        'descripcion': 'Las 4 tarjetas de especialidades.',
        'campos': [
            {'key': 'esp_eyebrow', 'label': 'Etiqueta superior', 'widget': 'input',
             'default': "Lo Que Hacemos"},
            {'key': 'esp_titulo', 'label': 'Título de la sección', 'widget': 'input',
             'default': "Nuestras Especialidades"},
            {'key': 'esp1_titulo', 'label': 'Tarjeta 1 — Título', 'widget': 'input',
             'default': "Moda Femenina"},
            {'key': 'esp1_texto', 'label': 'Tarjeta 1 — Texto', 'widget': 'textarea',
             'default': "Vestidos, blusas, faldas y chalecos diseñados para realzar tu estilo único."},
            {'key': 'esp2_titulo', 'label': 'Tarjeta 2 — Título', 'widget': 'input',
             'default': "Trajes Formales"},
            {'key': 'esp2_texto', 'label': 'Tarjeta 2 — Texto', 'widget': 'textarea',
             'default': "Sacos, pantalones y camisas para lucir impecable en toda ocasión."},
            {'key': 'esp3_titulo', 'label': 'Tarjeta 3 — Título', 'widget': 'input',
             'default': "A Medida"},
            {'key': 'esp3_texto', 'label': 'Tarjeta 3 — Texto', 'widget': 'textarea',
             'default': "Prendas personalizadas que se ajustan perfectamente a tu cuerpo."},
            {'key': 'esp4_titulo', 'label': 'Tarjeta 4 — Título', 'widget': 'input',
             'default': "Arreglos"},
            {'key': 'esp4_texto', 'label': 'Tarjeta 4 — Texto', 'widget': 'textarea',
             'default': "Modificaciones y ajustes profesionales para renovar tu guardarropa."},
        ],
    },
    {
        'key': 'destacadas',
        'titulo': 'Colección Destacada',
        'icono': 'bi-star',
        'descripcion': 'Encabezados de la sección de prendas destacadas. '
                       'Las prendas se eligen marcando "Destacada" al editarlas.',
        'campos': [
            {'key': 'dest_eyebrow', 'label': 'Etiqueta superior', 'widget': 'input',
             'default': "Colección Destacada"},
            {'key': 'dest_titulo', 'label': 'Título', 'widget': 'input',
             'default': "Nuestras Prendas Favoritas"},
            {'key': 'dest_vacio', 'label': 'Mensaje cuando no hay destacadas', 'widget': 'input',
             'default': "Aún no hay prendas destacadas. ¡Pronto agregaremos nuevas prendas!"},
            {'key': 'dest_boton', 'label': 'Texto del botón', 'widget': 'input',
             'default': "Ver Toda la Colección"},
        ],
    },
    {
        'key': 'cta',
        'titulo': 'Llamado a la acción',
        'icono': 'bi-megaphone',
        'descripcion': 'Banner azul de cotización en la página de inicio.',
        'campos': [
            {'key': 'cta_titulo', 'label': 'Título', 'widget': 'input',
             'default': "¿Buscas algo especial?"},
            {'key': 'cta_texto', 'label': 'Texto', 'widget': 'input',
             'default': "Contáctanos y creamos la prenda perfecta para ti"},
            {'key': 'cta_boton', 'label': 'Texto del botón', 'widget': 'input',
             'default': "Solicitar Cotización"},
        ],
    },
    {
        'key': 'ventajas',
        'titulo': '¿Por Qué Elegirnos?',
        'icono': 'bi-award',
        'descripcion': 'Las 4 ventajas al final de la página de inicio.',
        'campos': [
            {'key': 'vent_eyebrow', 'label': 'Etiqueta superior', 'widget': 'input',
             'default': "Ventajas"},
            {'key': 'vent_titulo', 'label': 'Título de la sección', 'widget': 'input',
             'default': "¿Por Qué Elegirnos?"},
            {'key': 'vent1_titulo', 'label': 'Ventaja 1 — Título', 'widget': 'input',
             'default': "Calidad Garantizada"},
            {'key': 'vent1_texto', 'label': 'Ventaja 1 — Texto', 'widget': 'input',
             'default': "Materiales premium y acabados impecables"},
            {'key': 'vent2_titulo', 'label': 'Ventaja 2 — Título', 'widget': 'input',
             'default': "Años de Experiencia"},
            {'key': 'vent2_texto', 'label': 'Ventaja 2 — Texto', 'widget': 'input',
             'default': "Tradición y conocimiento en cada costura"},
            {'key': 'vent3_titulo', 'label': 'Ventaja 3 — Título', 'widget': 'input',
             'default': "Atención Personalizada"},
            {'key': 'vent3_texto', 'label': 'Ventaja 3 — Texto', 'widget': 'input',
             'default': "Nos importa tu satisfacción"},
            {'key': 'vent4_titulo', 'label': 'Ventaja 4 — Título', 'widget': 'input',
             'default': "Entrega a Tiempo"},
            {'key': 'vent4_texto', 'label': 'Ventaja 4 — Texto', 'widget': 'input',
             'default': "Cumplimos con los plazos acordados"},
        ],
    },
    {
        'key': 'contacto',
        'titulo': 'Contacto y redes',
        'icono': 'bi-telephone',
        'descripcion': 'Datos de contacto que aparecen en el pie de página, '
                       'el botón de WhatsApp y la página de contacto.',
        'campos': [
            {'key': 'contacto_telefono', 'label': 'Teléfono (como se muestra)', 'widget': 'input',
             'default': "+504 9826-7040"},
            {'key': 'contacto_whatsapp', 'label': 'WhatsApp (solo dígitos, con código de país)',
             'widget': 'input', 'valida': 'digits', 'default': "50498267040"},
            {'key': 'contacto_email', 'label': 'Correo electrónico', 'widget': 'input',
             'default': "confeccionesmaty62@gmail.com"},
            {'key': 'contacto_direccion', 'label': 'Dirección', 'widget': 'input',
             'default': "Siguatepeque, Honduras"},
            {'key': 'red_facebook', 'label': 'Facebook (URL)', 'widget': 'input', 'valida': 'url',
             'default': "https://www.facebook.com/maryurihern/reels/"},
            {'key': 'red_instagram', 'label': 'Instagram (URL)', 'widget': 'input', 'valida': 'url',
             'default': "https://www.instagram.com/confe_ccionesmaty?utm_source=ig_web_button_share_sheet&igsh=ZDNlZDc0MzIxNw=="},
            {'key': 'red_tiktok', 'label': 'TikTok (URL)', 'widget': 'input', 'valida': 'url',
             'default': "https://www.tiktok.com/@confeccinesmaty4?is_from_webapp=1&sender_device=pc"},
            {'key': 'red_youtube', 'label': 'YouTube (URL)', 'widget': 'input', 'valida': 'url',
             'default': "https://youtube.com/@maty-2020?si=ncsHDzw-QCMJGlX1"},
        ],
    },
]

# key -> default, para merge rápido
DEFAULTS_TEXTOS = {
    campo['key']: campo['default']
    for seccion in SECCIONES_TEXTOS
    for campo in seccion['campos']
}

# key -> tipo de validación ('url' | 'digits')
VALIDACIONES_TEXTOS = {
    campo['key']: campo['valida']
    for seccion in SECCIONES_TEXTOS
    for campo in seccion['campos']
    if campo.get('valida')
}


def get_textos():
    """
    Defaults + overrides guardados en SiteConfig.
    Valores vacíos o de tipo incorrecto se ignoran (cae al default),
    así el cliente nunca puede dejar el sitio sin texto.
    """
    from .models import SiteConfig
    textos = dict(DEFAULTS_TEXTOS)
    try:
        data = SiteConfig.get_solo().data or {}
    except Exception:
        return textos  # tabla aún no migrada / DB no disponible
    for key, val in data.items():
        if key in textos and isinstance(val, str) and val.strip():
            textos[key] = val.strip()
    return textos
