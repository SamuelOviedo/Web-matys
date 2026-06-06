from .site_textos import get_textos


def site_textos(request):
    """Inyecta los textos editables del sitio como `txt` en todos los templates."""
    return {'txt': get_textos()}
