/* ============================================================
   REGISTRO DE TUTORIALES + CENTRO DE AYUDA — Panel Matys
   ------------------------------------------------------------
   Fuente única de verdad de todos los tutoriales. Para añadir uno
   nuevo basta con agregar un objeto al array TOURS: aparecerá solo
   en el Centro de ayuda y en la ayuda contextual, sin tocar HTML.
   ============================================================ */
(function (window, document) {
  'use strict';

  var T = window.MatysTour;
  if (!T) { console.warn('[MatysTour] motor no cargado'); return; }

  /* ── Rutas del panel (deben coincidir con urls.py) ───────── */
  var P = {
    dashboard: '/gestion-matys/',
    categorias: '/gestion-matys/categorias/',
    imagenes: '/gestion-matys/imagenes/',
    inicio: '/gestion-matys/inicio/',
    ayuda: '/gestion-matys/ayuda/',
  };

  /* ── Categorías (para agrupar en el Centro de ayuda) ─────── */
  var CATEGORIES = [
    { id: 'primeros_pasos', label: 'Primeros pasos', icon: 'bi-compass' },
    { id: 'productos', label: 'Productos', icon: 'bi-box-seam' },
    { id: 'catalogo', label: 'Catálogo', icon: 'bi-list-ul' },
    { id: 'imagenes', label: 'Imágenes', icon: 'bi-images' },
    { id: 'config', label: 'Configuración', icon: 'bi-gear' },
    { id: 'pedidos', label: 'Pedidos y WhatsApp', icon: 'bi-whatsapp' },
  ];

  /* ── Helpers de preparación (abrir modales / menús) ──────── */
  function delay(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function openSidebarIfMobile() {
    if (window.innerWidth >= 768) return Promise.resolve();
    var sb = document.getElementById('appSidebar');
    if (!window.bootstrap || !sb) return Promise.resolve();
    window.bootstrap.Offcanvas.getOrCreateInstance(sb).show();
    return delay(340);
  }

  function clickAndWait(clickSelector, waitSelector) {
    var trigger = typeof clickSelector === 'function' ? clickSelector() : document.querySelector(clickSelector);
    if (!trigger) return Promise.resolve(null);
    trigger.click();
    return T.waitFor(function () {
      var m = document.querySelector(waitSelector);
      return m && m.classList.contains('show') ? m : null;
    }, 4000);
  }

  var openCreate = function () { return clickAndWait('#btnNuevaPrenda', '#createModal'); };
  var openEditFirst = function () {
    return clickAndWait(function () { return document.querySelector('.edit-prenda-btn'); }, '#editModal')
      .then(function () { return T.waitFor(function () {
        var i = document.getElementById('editNombre');
        return i && i.value ? i : null;   // esperar a que carguen los datos
      }, 3000); });
  };
  var openDeleteFirst = function () {
    return clickAndWait(function () { return document.querySelector('.delete-prenda-btn'); }, '#deleteModal');
  };
  var openImageEditFirst = function () {
    return clickAndWait(function () { return document.querySelector('.overlay-edit-btn'); }, '#editModal')
      .then(function () { return T.waitFor('#imgStrip .strip-card, #imgStrip', 3000); });
  };

  /* ── Definición de todos los tutoriales ──────────────────── */
  var TOURS = [
    /* ===================== PRIMEROS PASOS ===================== */
    {
      id: 'overview',
      title: 'Recorrido general del panel',
      category: 'primeros_pasos',
      icon: 'bi-compass',
      description: 'Conocé de un vistazo todas las secciones del panel: menú, indicadores y acciones principales.',
      estMinutes: 3,
      keywords: ['inicio', 'menu', 'navegacion', 'general', 'panel', 'dashboard'],
      path: P.dashboard,
      steps: [
        { selector: '.sb-brand', path: P.dashboard, pre: openSidebarIfMobile,
          title: '¡Bienvenida a tu panel!', placement: 'right',
          body: ['Este es el panel de administración de Confecciones Matys. Desde acá controlás todo lo que se ve en el sitio público.',
                 'Te haremos un recorrido rápido. Podés avanzar con <b>Siguiente</b> o cerrar cuando quieras.'] },
        { selector: '.sb-nav-item[href$="gestion-matys/"]', path: P.dashboard, pre: openSidebarIfMobile,
          title: 'Vista general', placement: 'right',
          body: 'Es la pantalla principal: acá ves el resumen del catálogo y la lista de prendas.',
          note: 'Es tu punto de partida para crear, editar o eliminar prendas.' },
        { selector: '.sb-nav-item[href*="categorias"]', path: P.dashboard, pre: openSidebarIfMobile,
          title: 'Categorías', placement: 'right',
          body: 'Acá definís los tipos de prenda (vestidos, blusas, trajes…) dentro de cada categoría.' },
        { selector: '.sb-nav-item[href*="inicio"]', path: P.dashboard, pre: openSidebarIfMobile,
          title: 'Textos del sitio', placement: 'right',
          body: 'Editás los textos de la página pública y tus datos de contacto (incluido el WhatsApp).' },
        { selector: '.sb-nav-item[href*="imagenes"]', path: P.dashboard, pre: openSidebarIfMobile,
          title: 'Imágenes', placement: 'right',
          body: 'Revisás todas las fotos de tus prendas y entrás a editarlas rápidamente.' },
        { selector: '.sb-nav-item[href*="ayuda"]', path: P.dashboard, pre: openSidebarIfMobile,
          title: 'Centro de ayuda', placement: 'right',
          body: 'Si alguna vez olvidás cómo hacer algo, volvé acá: encontrarás todos estos tutoriales para repetirlos cuando quieras.',
          note: 'Nunca vas a quedar sin ayuda: todo está a un clic.' },
        { selector: '.kpi-strip', path: P.dashboard,
          title: 'Indicadores rápidos', placement: 'bottom',
          body: 'Estas tarjetas muestran el estado de tu catálogo: total de prendas, disponibles, imágenes y prendas sin foto.' },
        { selector: '.work-surface', path: P.dashboard,
          title: 'Lista de prendas', placement: 'top',
          body: 'Acá aparece cada prenda con su categoría, tipo, precio y estado. Pasá el mouse (o tocá) una fila para ver sus acciones.' },
        { selector: '#btnNuevaPrenda', path: P.dashboard,
          title: 'Crear una prenda nueva', placement: 'left',
          body: 'Con este botón agregás una prenda nueva al catálogo.',
          action: 'Cuando quieras crear una prenda, empezá siempre por aquí.' },
        { selector: '#topbarHelpBtn', path: P.dashboard,
          title: 'Ayuda siempre a mano', placement: 'bottom',
          body: 'Este botón de ayuda te muestra el tutorial de la página en la que estés. ¡Listo! Ya conocés el panel.' },
      ],
    },

    /* ===================== PRODUCTOS ===================== */
    {
      id: 'create_product',
      title: 'Crear una prenda',
      category: 'productos',
      icon: 'bi-plus-circle',
      description: 'Aprendé a agregar una prenda nueva al catálogo, paso a paso, con foto incluida.',
      estMinutes: 4,
      keywords: ['crear', 'nueva', 'prenda', 'producto', 'agregar', 'alta'],
      path: P.dashboard,
      steps: [
        { selector: '#btnNuevaPrenda', path: P.dashboard,
          title: 'Empecemos a crear', placement: 'left',
          body: 'Todo comienza con este botón. Lo vamos a abrir por vos para mostrarte el formulario.',
          action: 'En el uso real, hacé clic en “Nueva prenda”.' },
        { selector: '#createNombre', path: P.dashboard, pre: openCreate,
          title: 'Nombre de la prenda', placement: 'bottom',
          body: 'Escribí un nombre claro y atractivo. Es lo primero que verá tu clienta en el catálogo.' },
        { selector: '#createPrecio', path: P.dashboard,
          title: 'Precio', placement: 'bottom',
          body: 'Indicá el precio en lempiras. Se mostrará como “L. …” en la ficha del producto.' },
        { selector: '#createDescripcion', path: P.dashboard,
          title: 'Descripción corta', placement: 'top',
          body: 'Una frase breve que describa la prenda. Aparece en la tarjeta del catálogo.' },
        { selector: '#createBtnTono', path: P.dashboard,
          title: 'Ayuda con IA (opcional)', placement: 'bottom',
          body: 'Si no sabés cómo redactarla, este asistente te sugiere varios tonos con inteligencia artificial.',
          note: 'Tenés un tutorial dedicado a esta función en la categoría Productos.' },
        { selector: '#createCategoria', path: P.dashboard,
          title: 'Categoría y tipo', placement: 'top',
          body: 'Elegí la categoría (Femenino, Masculino, Infantil) y luego el tipo. Los tipos se cargan según la categoría.' },
        { selector: '#createDisponible', path: P.dashboard,
          title: 'Disponible en el catálogo', placement: 'top',
          body: 'Si está marcada, la prenda se muestra en el sitio público. Si la desmarcás, queda oculta.',
          note: 'Útil para preparar prendas antes de publicarlas.' },
        { selector: '#createImgStrip', path: P.dashboard,
          title: 'Fotos de la prenda', placement: 'top',
          body: 'Agregá hasta 4 fotos. La primera será la imagen principal que se ve en el catálogo.' },
        { selector: '#createSubmitBtn', path: P.dashboard,
          title: 'Guardar la prenda', placement: 'left',
          body: 'Cuando todo esté listo, este botón crea la prenda y la publica según su disponibilidad.',
          action: 'Revisá los datos y hacé clic en “Crear prenda”.' },
      ],
    },
    {
      id: 'edit_product',
      title: 'Editar una prenda',
      category: 'productos',
      icon: 'bi-pencil-square',
      description: 'Modificá el nombre, precio, descripción, categoría o fotos de una prenda existente.',
      estMinutes: 3,
      keywords: ['editar', 'modificar', 'cambiar', 'prenda', 'producto', 'actualizar'],
      path: P.dashboard,
      steps: [
        { selector: function () { return document.querySelector('.edit-prenda-btn'); }, path: P.dashboard,
          title: 'Botón editar', placement: 'left',
          body: 'Cada fila tiene un lápiz para editar esa prenda. Lo abriremos por vos como ejemplo.',
          action: 'En el uso real, hacé clic en el lápiz de la prenda que quieras cambiar.' },
        { selector: '#editNombre', path: P.dashboard, pre: openEditFirst,
          title: 'Editá los datos', placement: 'bottom',
          body: 'Se abre el mismo formulario que al crear, pero con los datos ya cargados. Cambiá lo que necesites.' },
        { selector: '#editImgStrip', path: P.dashboard,
          title: 'Reordenar y cambiar fotos', placement: 'top',
          body: 'Arrastrá las fotos para reordenarlas. La primera es la principal. También podés eliminar o agregar (máx. 4).' },
        { selector: '#editSubmitBtn', path: P.dashboard,
          title: 'Guardar cambios', placement: 'left',
          body: 'Este botón guarda todo. Los cambios se ven al instante en el sitio público.',
          action: 'Hacé clic en “Guardar cambios” para confirmar.' },
      ],
    },
    {
      id: 'delete_product',
      title: 'Eliminar una prenda',
      category: 'productos',
      icon: 'bi-trash3',
      description: 'Quitá una prenda del catálogo de forma permanente y entendé cuándo conviene hacerlo.',
      estMinutes: 2,
      keywords: ['eliminar', 'borrar', 'quitar', 'prenda', 'producto'],
      path: P.dashboard,
      steps: [
        { selector: function () { return document.querySelector('.delete-prenda-btn'); }, path: P.dashboard,
          title: 'Botón eliminar', placement: 'left',
          body: 'El ícono de papelera elimina la prenda. Abriremos la confirmación como ejemplo.',
          note: 'Si solo querés ocultarla temporalmente, mejor usá “Disponible” en vez de eliminar.' },
        { selector: '#deleteModal .modal-content', path: P.dashboard, pre: openDeleteFirst,
          title: 'Confirmación de borrado', placement: 'top',
          body: 'Siempre se pide confirmación porque esta acción es <b>irreversible</b>: se borran la prenda y sus fotos.',
          action: 'Para cancelar, tocá “Cancelar”. Para borrar de verdad, “Eliminar definitivamente”.' },
      ],
    },
    {
      id: 'product_visibility',
      title: 'Disponibilidad y prendas destacadas',
      category: 'productos',
      icon: 'bi-eye',
      description: 'Controlá qué prendas se ven, cuáles se destacan en el inicio y cuáles son por encargo.',
      estMinutes: 3,
      keywords: ['disponible', 'oculta', 'destacada', 'inventario', 'stock', 'visibilidad', 'encargo'],
      path: P.dashboard,
      steps: [
        { selector: function () { return document.querySelector('.prenda-row .pcell-estado'); }, path: P.dashboard,
          title: 'Estado de cada prenda', placement: 'left',
          body: 'La columna Estado muestra si la prenda está <b>Activa</b> (visible) u <b>Oculta</b>. Así controlás tu inventario visible.' },
        { selector: '#editDisponible', path: P.dashboard, pre: openEditFirst,
          title: 'Disponible en el catálogo', placement: 'top',
          body: 'Marcá o desmarcá esta casilla para mostrar u ocultar la prenda del sitio público, sin borrarla.' },
        { selector: '#editPorEncargo', path: P.dashboard,
          title: 'Hecho por encargo', placement: 'top',
          body: 'Si está marcada, la tarjeta muestra la etiqueta “Por encargo”, indicando que se confecciona a pedido.' },
        { selector: '#editDestacada', path: P.dashboard,
          title: 'Prenda destacada', placement: 'top',
          body: 'Las destacadas aparecen en la “Colección Destacada” de la página de inicio (hasta 3 visibles).',
          action: 'Elegí tus mejores prendas para destacarlas y atraer más clientas.' },
      ],
    },
    {
      id: 'ai_tones',
      title: 'Asistente de redacción con IA',
      category: 'productos',
      icon: 'bi-stars',
      description: 'Generá descripciones en distintos tonos automáticamente cuando no sepas qué escribir.',
      estMinutes: 2,
      isNew: true,
      keywords: ['ia', 'inteligencia artificial', 'tono', 'descripcion', 'redaccion', 'copy', 'asistente'],
      path: P.dashboard,
      steps: [
        { selector: '#createDescripcion', path: P.dashboard, pre: openCreate,
          title: 'Escribí una idea base', placement: 'bottom',
          body: 'Primero escribí una descripción, aunque sea sencilla. El asistente la va a mejorar.' },
        { selector: '#createBtnTono', path: P.dashboard,
          title: 'Sugerir tonos con IA', placement: 'bottom',
          body: 'Al tocar este botón, la IA propone la misma descripción en varios tonos: profesional, casual, emocional y juvenil.',
          note: 'Es una función nueva: te ahorra tiempo cuando no sabés cómo redactar.',
          action: 'Elegí el tono que más te guste y tocá “Usar”.' },
      ],
    },

    /* ===================== CATÁLOGO ===================== */
    {
      id: 'categories',
      title: 'Gestionar categorías y tipos',
      category: 'catalogo',
      icon: 'bi-list-ul',
      description: 'Organizá tu catálogo creando, renombrando o eliminando los tipos de prenda de cada categoría.',
      estMinutes: 3,
      keywords: ['categoria', 'tipo', 'catalogo', 'organizar', 'femenino', 'masculino', 'infantil'],
      path: P.categorias,
      steps: [
        { selector: function () { return document.querySelector('.cats-grid .admin-card'); }, path: P.categorias,
          title: 'Tres categorías fijas', placement: 'bottom',
          body: 'Tu catálogo tiene tres categorías: Femenino, Masculino e Infantil. Cada tarjeta agrupa sus tipos de prenda.' },
        { selector: function () { return document.querySelector('.admin-card .chip'); }, path: P.categorias,
          title: 'Cantidad de tipos', placement: 'left',
          body: 'Este contador te dice cuántos tipos tenés en esa categoría.' },
        { selector: '#add-trigger-femenino', path: P.categorias,
          title: 'Agregar un tipo', placement: 'top',
          body: 'Con “Agregar tipo” creás un nuevo tipo (por ejemplo “Vestido de gala”). Se escribe el nombre y se guarda.',
          action: 'Probá agregar un tipo cuando necesites una nueva clasificación.' },
        { selector: function () { return document.querySelector('.data-row .edit-btn') || document.querySelector('.cats-grid .admin-card'); }, path: P.categorias,
          title: 'Editar o eliminar', placement: 'left',
          body: 'Pasá el mouse (o tocá) sobre un tipo para ver los botones de editar y eliminar.',
          note: 'No podés eliminar un tipo que tenga prendas asignadas: primero reasignalas.' },
      ],
    },

    /* ===================== IMÁGENES ===================== */
    {
      id: 'images',
      title: 'Gestionar imágenes',
      category: 'imagenes',
      icon: 'bi-images',
      description: 'Revisá las fotos de tus prendas y aprendé a reordenarlas, cambiarlas o agregar nuevas.',
      estMinutes: 3,
      keywords: ['imagen', 'foto', 'galeria', 'principal', 'reordenar', 'cloudinary'],
      path: P.imagenes,
      steps: [
        { selector: function () { return document.querySelector('.image-card'); }, path: P.imagenes,
          title: 'Galería de prendas', placement: 'bottom',
          body: 'Acá ves cada prenda que tiene fotos, con su categoría y cuántas imágenes tiene.' },
        { selector: function () { return document.querySelector('.overlay-edit-btn'); }, path: P.imagenes,
          title: 'Editar desde la foto', placement: 'bottom',
          body: 'Al pasar el mouse (o tocar) sobre una foto aparece “Editar prenda”. Abre el mismo editor que en la Vista general.',
          action: 'Tocá una foto para editar esa prenda.' },
        { selector: '#imgStrip', path: P.imagenes, pre: openImageEditFirst,
          title: 'Reordenar y administrar fotos', placement: 'top',
          body: 'Arrastrá para reordenar. La primera foto es la principal del catálogo. Podés eliminar o agregar (máx. 4).' },
        { selector: '#editSubmitBtn', path: P.imagenes,
          title: 'Guardar cambios', placement: 'left',
          body: 'Guardá para aplicar los cambios de fotos. Se reflejan al instante en el sitio.' },
      ],
    },

    /* ===================== CONFIGURACIÓN ===================== */
    {
      id: 'site_texts',
      title: 'Editar los textos del sitio',
      category: 'config',
      icon: 'bi-pencil-square',
      description: 'Cambiá los títulos, textos y datos de contacto de la página pública sin tocar código.',
      estMinutes: 3,
      keywords: ['textos', 'contenido', 'inicio', 'configuracion', 'contacto', 'redes', 'cms'],
      path: P.inicio,
      steps: [
        { selector: function () { return document.querySelector('.textos-grid .admin-card'); }, path: P.inicio,
          title: 'Todo el texto, editable', placement: 'bottom',
          body: 'Cada tarjeta agrupa los textos de una sección del sitio: inicio, contacto, redes sociales, etc.' },
        { selector: function () { return document.querySelector('.campo-block .input-admin'); }, path: P.inicio,
          title: 'Editá un campo', placement: 'bottom',
          body: 'Escribí el nuevo texto. Si dejás un campo vacío, vuelve automáticamente a su texto original.',
          note: 'Los campos modificados muestran una etiqueta “Editado”.' },
        { selector: function () { return document.querySelector('.save-bar'); }, path: P.inicio,
          title: 'Guardar y publicar', placement: 'top',
          body: 'Esta barra siempre visible te permite guardar. Los cambios se publican al instante.',
          action: 'Tocá “Ver sitio” para revisar cómo quedó, y “Guardar cambios” para publicar.' },
      ],
    },

    /* ===================== PEDIDOS / WHATSAPP ===================== */
    {
      id: 'whatsapp',
      title: 'Cómo llegan los pedidos por WhatsApp',
      category: 'pedidos',
      icon: 'bi-whatsapp',
      description: 'Entendé el flujo de pedidos: tus clientas te escriben por WhatsApp con el enlace de la prenda.',
      estMinutes: 2,
      keywords: ['whatsapp', 'pedido', 'orden', 'cliente', 'venta', 'contacto', 'cotizacion'],
      path: P.inicio,
      steps: [
        { selector: function () { return document.getElementById('campo-contacto_whatsapp') || document.querySelector('.textos-grid'); }, path: P.inicio,
          title: 'Tu número de WhatsApp', placement: 'bottom',
          body: ['Este es el número donde recibís los pedidos y consultas. Escribilo con código de país, sin espacios (ej: 50498267040).',
                 'Todos los botones de WhatsApp del sitio usan este número.'] },
        { selector: function () { return document.querySelector('.textos-grid'); }, path: P.inicio,
          title: 'El pedido incluye la prenda', placement: 'top',
          body: ['Cuando una clienta toca “Solicitar cotización” en una prenda, se abre WhatsApp con un mensaje ya armado: nombre, precio, talla y el <b>enlace directo</b> a esa prenda.',
                 'Así sabés exactamente qué producto te están pidiendo.'],
          note: 'No hay una bandeja de pedidos dentro del panel: las ventas se gestionan por WhatsApp. Por eso tu número correcto es tan importante.' },
      ],
    },
  ];

  T.registerAll(TOURS);

  /* Mapa página → tutorial principal (para la ayuda contextual) */
  var PAGE_TOUR = {};
  PAGE_TOUR[P.dashboard] = 'overview';
  PAGE_TOUR[P.categorias] = 'categories';
  PAGE_TOUR[P.imagenes] = 'images';
  PAGE_TOUR[P.inicio] = 'site_texts';

  function normPath(p) {
    p = (p || '').split('?')[0].split('#')[0];
    if (p.length > 1 && p.charAt(p.length - 1) !== '/') p += '/';
    return p;
  }

  function launchTour(id) {
    var tour = T.get(id);
    if (!tour) return;
    if (normPath(tour.path) === normPath(location.pathname)) {
      T.start(id);
    } else {
      location.assign(tour.path + '?tour=' + encodeURIComponent(id));
    }
  }
  window.MatysTour.launch = launchTour;

  /* ── Ayuda contextual (botón de la topbar) ───────────────── */
  function hasNewUncompleted() {
    return T.all().some(function (t) { return t.isNew && !T.isCompleted(t.id); });
  }

  function wireTopbarHelp() {
    var btn = document.getElementById('topbarHelpBtn');
    if (!btn) return;
    var here = normPath(location.pathname);
    var primary = PAGE_TOUR[here];

    // Punto rojo si hay tutoriales nuevos sin completar
    if (hasNewUncompleted()) {
      var dot = document.createElement('span');
      dot.className = 'topbar-help-dot';
      btn.appendChild(dot);
      btn.title = 'Ayuda · hay tutoriales nuevos';
    }

    btn.addEventListener('click', function (e) {
      e.preventDefault();
      if (primary) launchTour(primary);
      else location.assign(P.ayuda);
    });
  }

  /* ── Centro de ayuda (render dinámico) ───────────────────── */
  function fmtTime(min) { return min <= 1 ? '1 min' : min + ' min'; }

  function tourCardHtml(t) {
    var done = T.isCompleted(t.id);
    var badges = '';
    if (t.isNew && !done) badges += '<span class="help-badge-new"><i class="bi bi-stars"></i>Nuevo</span>';
    if (done) badges += '<span class="help-badge-done"><i class="bi bi-check-circle-fill"></i>Completado</span>';
    return '' +
      '<div class="help-card" data-tour-card="' + t.id + '" ' +
           'data-search="' + escapeAttr((t.title + ' ' + t.description + ' ' + (t.keywords || []).join(' ')).toLowerCase()) + '" ' +
           'data-cat="' + t.category + '">' +
        '<div class="help-card-top">' +
          '<div class="help-card-icon"><i class="bi ' + (t.icon || 'bi-book') + '"></i></div>' +
          '<div style="flex:1;min-width:0;">' +
            '<div class="help-card-title">' + escapeHtml(t.title) + '</div>' +
          '</div>' +
        '</div>' +
        '<div class="help-card-desc">' + escapeHtml(t.description) + '</div>' +
        '<div class="help-card-meta">' +
          '<span class="help-meta-item"><i class="bi bi-clock"></i>' + fmtTime(t.estMinutes || 2) + '</span>' +
          '<span class="help-meta-item"><i class="bi bi-list-ol"></i>' + t.steps.length + ' pasos</span>' +
          badges +
        '</div>' +
        '<button type="button" class="help-card-btn ' + (done ? 'is-replay' : '') + '" data-launch="' + t.id + '">' +
          '<i class="bi ' + (done ? 'bi-arrow-repeat' : 'bi-play-fill') + '"></i>' + (done ? 'Repetir' : 'Iniciar') +
        '</button>' +
      '</div>';
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function escapeAttr(s) { return escapeHtml(s).replace(/'/g, '&#39;'); }

  function renderHelpCenter() {
    var mount = document.getElementById('helpMount');
    if (!mount) return;

    // Chips de filtro por categoría (solo las que tienen tutoriales)
    var filters = document.getElementById('helpFilters');
    if (filters) {
      var chipsHtml = '<button type="button" class="help-filter-chip active" data-cat="all">Todos</button>';
      CATEGORIES.forEach(function (cat) {
        var count = T.all().filter(function (t) { return t.category === cat.id; }).length;
        if (!count) return;
        chipsHtml += '<button type="button" class="help-filter-chip" data-cat="' + cat.id + '">' +
          '<i class="bi ' + cat.icon + ' me-1"></i>' + cat.label + '</button>';
      });
      filters.innerHTML = chipsHtml;
    }

    var html = '';
    CATEGORIES.forEach(function (cat) {
      var tours = T.all().filter(function (t) { return t.category === cat.id; });
      if (!tours.length) return;
      html += '<div class="help-cat-block" data-cat-block="' + cat.id + '">' +
                '<div class="help-cat-title"><i class="bi ' + cat.icon + '"></i>' + cat.label + '</div>' +
                '<div class="help-grid">' +
                  tours.map(tourCardHtml).join('') +
                '</div></div>';
    });
    html += '<div class="help-empty" id="helpEmpty" style="display:none;">' +
              '<i class="bi bi-search"></i><div>No encontramos tutoriales que coincidan con tu búsqueda.</div></div>';
    mount.innerHTML = html;

    // Lanzar tutoriales
    mount.addEventListener('click', function (e) {
      var b = e.target.closest('[data-launch]');
      if (b) launchTour(b.getAttribute('data-launch'));
    });

    wireHelpFilters();
  }

  function wireHelpFilters() {
    var search = document.getElementById('helpSearch');
    var chips = document.querySelectorAll('.help-filter-chip');
    var activeCat = 'all';

    function apply() {
      var q = (search && search.value || '').trim().toLowerCase();
      var anyVisible = false;
      document.querySelectorAll('.help-cat-block').forEach(function (block) {
        var blockCat = block.getAttribute('data-cat-block');
        var catOk = activeCat === 'all' || activeCat === blockCat;
        var visibleInBlock = 0;
        block.querySelectorAll('[data-tour-card]').forEach(function (card) {
          var matchQ = !q || card.getAttribute('data-search').indexOf(q) !== -1;
          var show = catOk && matchQ;
          card.style.display = show ? '' : 'none';
          if (show) visibleInBlock++;
        });
        block.style.display = visibleInBlock ? '' : 'none';
        if (visibleInBlock) anyVisible = true;
      });
      var empty = document.getElementById('helpEmpty');
      if (empty) empty.style.display = anyVisible ? 'none' : 'block';
    }

    if (search) search.addEventListener('input', apply);
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        chips.forEach(function (c) { c.classList.remove('active'); });
        chip.classList.add('active');
        activeCat = chip.getAttribute('data-cat');
        apply();
      });
    });
  }

  /* ── Arranque en cada página del panel ───────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    wireTopbarHelp();
    renderHelpCenter();
    // Reanudar / iniciar un tutorial si la URL lo indica
    T.resumeFromUrl();
  });

  // Exponer categorías por si el template quiere construir los filtros
  window.MatysTour.categories = CATEGORIES;
})(window, document);
