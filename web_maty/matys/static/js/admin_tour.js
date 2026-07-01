/* ============================================================
   MOTOR DE TUTORIALES GUIADOS — Panel Matys
   ------------------------------------------------------------
   Motor genérico e independiente de datos. Los tutoriales se
   definen en admin_tours.js y se registran con MatysTour.register().

   Un "tour" es: { id, title, category, description, icon,
                   estMinutes, isNew, path, onEnd, steps: [...] }
   Un "paso" es:  { selector, title, body, note, action,
                    placement, path, pre }
     - selector : string CSS | función que devuelve un elemento | null
     - body     : string | array de strings (párrafos)
     - note     : (opcional) aclaración destacada ("por qué existe")
     - action   : (opcional) qué debe hacer la administradora
     - placement: 'auto' | 'top' | 'bottom' | 'left' | 'right'
     - path     : (opcional) ruta donde vive el paso; si difiere de la
                  actual, el motor navega y reanuda el tour ahí.
     - pre      : (opcional) función (puede ser async) que prepara la
                  vista antes de resaltar (p. ej. abrir un modal).

   Persistencia (localStorage):
     - matys_active_tour     : {id, index}  → reanudar tras navegar
     - matys_tours_completed : [id, ...]    → tutoriales completados
   ============================================================ */
(function (window, document) {
  'use strict';

  var REGISTRY = {};
  var LS_ACTIVE = 'matys_active_tour';
  var LS_DONE = 'matys_tours_completed';

  var state = {
    tour: null,
    index: 0,
    active: false,
    currentEl: null,
    placement: 'bottom',
    rafId: null,
    lastFocus: null,
  };

  /* ── Utilidades de almacenamiento ───────────────────────── */
  function readJSON(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; }
    catch (e) { return fallback; }
  }
  function writeJSON(key, val) {
    try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {}
  }
  function getCompleted() { return readJSON(LS_DONE, []); }
  function isCompleted(id) { return getCompleted().indexOf(id) !== -1; }
  function markCompleted(id) {
    var done = getCompleted();
    if (done.indexOf(id) === -1) { done.push(id); writeJSON(LS_DONE, done); }
    document.dispatchEvent(new CustomEvent('matystour:completed', { detail: { id: id } }));
  }

  function normPath(p) {
    if (!p) return p;
    p = p.split('?')[0].split('#')[0];
    if (p.length > 1 && p.charAt(p.length - 1) !== '/') p += '/';
    return p;
  }

  /* ── Espera a que aparezca un elemento (para modales async) ─ */
  function waitFor(selector, timeout) {
    timeout = timeout || 4000;
    return new Promise(function (resolve) {
      var found = resolveEl(selector);
      if (found) return resolve(found);
      var start = Date.now();
      var iv = setInterval(function () {
        var el = resolveEl(selector);
        if (el) { clearInterval(iv); resolve(el); }
        else if (Date.now() - start > timeout) { clearInterval(iv); resolve(null); }
      }, 80);
    });
  }

  function resolveEl(selector) {
    if (!selector) return null;
    try {
      if (typeof selector === 'function') return selector() || null;
      var el = document.querySelector(selector);
      return el && el.offsetParent !== null ? el : (el || null);
    } catch (e) { return null; }
  }

  /* ── Construcción del DOM del motor (una sola vez) ───────── */
  var dom = {};
  function buildDom() {
    if (dom.tip) return;

    dom.backdrop = document.createElement('div');
    dom.backdrop.id = 'tourBackdrop';

    dom.spotlight = document.createElement('div');
    dom.spotlight.id = 'tourSpotlight';

    dom.tip = document.createElement('div');
    dom.tip.id = 'tourTip';
    dom.tip.setAttribute('role', 'dialog');
    dom.tip.setAttribute('aria-modal', 'true');
    dom.tip.setAttribute('aria-live', 'polite');
    dom.tip.tabIndex = -1;

    document.body.appendChild(dom.backdrop);
    document.body.appendChild(dom.spotlight);
    document.body.appendChild(dom.tip);
  }

  /* ── Posicionamiento del popover respecto al objetivo ────── */
  function pickPlacement(rect, preferred) {
    var tipW = dom.tip.offsetWidth || 340;
    var tipH = dom.tip.offsetHeight || 260;
    var gap = 14;
    var vw = window.innerWidth, vh = window.innerHeight;
    var space = {
      bottom: vh - rect.bottom,
      top: rect.top,
      right: vw - rect.right,
      left: rect.left,
    };
    var order = preferred && preferred !== 'auto'
      ? [preferred, 'bottom', 'top', 'right', 'left']
      : ['bottom', 'top', 'right', 'left'];
    for (var i = 0; i < order.length; i++) {
      var p = order[i];
      if ((p === 'bottom' || p === 'top') && space[p] >= tipH + gap) return p;
      if ((p === 'left' || p === 'right') && space[p] >= tipW + gap) return p;
    }
    // El que tenga más espacio
    return Object.keys(space).sort(function (a, b) { return space[b] - space[a]; })[0];
  }

  function place(rect) {
    var isMobile = window.innerWidth <= 640;
    var pad = 6;

    if (rect) {
      dom.spotlight.style.left = (rect.left - pad) + 'px';
      dom.spotlight.style.top = (rect.top - pad) + 'px';
      dom.spotlight.style.width = (rect.width + pad * 2) + 'px';
      dom.spotlight.style.height = (rect.height + pad * 2) + 'px';
      dom.spotlight.classList.add('tour-visible');
      dom.backdrop.classList.remove('tour-visible');
    } else {
      dom.spotlight.classList.remove('tour-visible');
      dom.backdrop.classList.add('tour-visible');
    }

    if (isMobile) return; // en móvil el CSS ancla el popover abajo

    var tipW = dom.tip.offsetWidth || 340;
    var tipH = dom.tip.offsetHeight || 260;
    var gap = 14;
    var vw = window.innerWidth, vh = window.innerHeight;
    var left, top;

    if (!rect) {
      left = (vw - tipW) / 2;
      top = (vh - tipH) / 2;
    } else {
      var p = state.placement;
      if (p === 'bottom') { top = rect.bottom + gap; left = rect.left + rect.width / 2 - tipW / 2; }
      else if (p === 'top') { top = rect.top - tipH - gap; left = rect.left + rect.width / 2 - tipW / 2; }
      else if (p === 'right') { left = rect.right + gap; top = rect.top + rect.height / 2 - tipH / 2; }
      else { left = rect.left - tipW - gap; top = rect.top + rect.height / 2 - tipH / 2; }
    }
    // Mantener dentro del viewport
    left = Math.max(12, Math.min(left, vw - tipW - 12));
    top = Math.max(12, Math.min(top, vh - tipH - 12));
    dom.tip.style.left = left + 'px';
    dom.tip.style.top = top + 'px';
  }

  function startTracking() {
    stopTracking();
    function loop() {
      if (!state.active) return;
      var rect = state.currentEl ? state.currentEl.getBoundingClientRect() : null;
      // si el elemento desapareció (p. ej. modal cerrado), tratamos como centrado
      place(rect && rect.width ? rect : null);
      state.rafId = window.requestAnimationFrame(loop);
    }
    state.rafId = window.requestAnimationFrame(loop);
  }
  function stopTracking() {
    if (state.rafId) { window.cancelAnimationFrame(state.rafId); state.rafId = null; }
  }

  /* ── Render del contenido de un paso ─────────────────────── */
  function renderTipContent(step) {
    var tour = state.tour;
    var total = tour.steps.length;
    var n = state.index + 1;
    var pct = Math.round((n / total) * 100);

    var bodyHtml = '';
    var paras = Array.isArray(step.body) ? step.body : (step.body ? [step.body] : []);
    paras.forEach(function (p) { bodyHtml += '<p>' + p + '</p>'; });

    var noteHtml = step.note
      ? '<div class="tour-note"><i class="bi bi-lightbulb-fill"></i><span>' + step.note + '</span></div>'
      : '';
    var actionHtml = step.action
      ? '<div class="tour-action"><i class="bi bi-hand-index-thumb-fill"></i><span>' + step.action + '</span></div>'
      : '';

    dom.tip.innerHTML =
      '<div class="tour-progress-wrap">' +
        '<div class="tour-tip-header">' +
          '<span class="tour-tip-eyebrow"><i class="bi ' + (tour.icon || 'bi-compass') + '"></i>' +
            '<span class="tour-eyebrow-text">' + escapeHtml(tour.title) + '</span></span>' +
          '<button type="button" class="tour-tip-close" data-tour="skip" aria-label="Cerrar tutorial">&times;</button>' +
        '</div>' +
        '<div class="tour-progress-row"><span>Paso ' + n + ' de ' + total + '</span><span>' + pct + '%</span></div>' +
        '<div class="tour-progress-bar"><div class="tour-progress-fill" style="width:' + pct + '%"></div></div>' +
      '</div>' +
      '<h3 class="tour-tip-title">' + escapeHtml(step.title || '') + '</h3>' +
      '<div class="tour-tip-body">' + bodyHtml + '</div>' +
      noteHtml + actionHtml +
      '<div class="tour-tip-footer">' +
        '<button type="button" class="tour-btn tour-btn-skip" data-tour="skip">Saltar</button>' +
        '<button type="button" class="tour-btn tour-btn-prev" data-tour="prev"' + (state.index === 0 ? ' disabled' : '') + '>' +
          '<i class="bi bi-arrow-left"></i>Atrás</button>' +
        '<button type="button" class="tour-btn tour-btn-next" data-tour="next">' +
          (n === total ? 'Finalizar<i class="bi bi-check-lg"></i>' : 'Siguiente<i class="bi bi-arrow-right"></i>') +
        '</button>' +
      '</div>';
  }

  function renderFinish() {
    stopTracking();
    state.currentEl = null;
    dom.spotlight.classList.remove('tour-visible');
    dom.backdrop.classList.add('tour-visible');
    dom.tip.innerHTML =
      '<div class="tour-finish">' +
        '<div class="tour-finish-check"><i class="bi bi-check-lg"></i></div>' +
        '<h3 class="tour-finish-title">¡Tutorial completado!</h3>' +
        '<p class="tour-finish-text">Ya conocés este flujo. Podés repetir cualquier tutorial cuando quieras desde el <strong>Centro de ayuda</strong>.</p>' +
        '<div class="tour-finish-actions">' +
          '<button type="button" class="tour-btn tour-btn-next" data-tour="finish-close" style="justify-content:center;">Entendido</button>' +
          '<button type="button" class="tour-btn tour-btn-prev" data-tour="go-help" style="justify-content:center;">Ver Centro de ayuda</button>' +
        '</div>' +
      '</div>';
    place(null);
    dom.tip.classList.add('tour-visible');
    focusTip();
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function focusTip() {
    var next = dom.tip.querySelector('[data-tour="next"]');
    (next || dom.tip).focus();
  }

  /* ── Mostrar un paso concreto ────────────────────────────── */
  async function showStep(index) {
    var tour = state.tour;
    if (!tour) return;
    if (index < 0) index = 0;
    if (index >= tour.steps.length) { finish(); return; }

    var step = tour.steps[index];

    // ¿El paso vive en otra página? Navegamos y reanudamos allí.
    if (step.path && normPath(step.path) !== normPath(location.pathname)) {
      writeJSON(LS_ACTIVE, { id: tour.id, index: index });
      location.assign(step.path + '?tour=' + encodeURIComponent(tour.id) + '&step=' + index);
      return;
    }

    state.index = index;
    writeJSON(LS_ACTIVE, { id: tour.id, index: index });

    // Preparación (abrir modal, etc.)
    if (typeof step.pre === 'function') {
      try { await step.pre(); } catch (e) { /* seguimos igual */ }
    }

    // Localizar el elemento (esperando si hace falta)
    var el = null;
    if (step.selector) el = await waitFor(step.selector, step.waitMs || 3500);
    state.currentEl = el;
    state.placement = 'bottom';

    // Render del contenido primero (para medir tamaño del popover)
    renderTipContent(step);
    dom.tip.classList.add('tour-visible');

    if (el) {
      try { el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' }); } catch (e) {}
      // esperar breve para que el scroll asiente y medir
      await new Promise(function (r) { setTimeout(r, 260); });
      var rect = el.getBoundingClientRect();
      state.placement = pickPlacement(rect, step.placement);
    }

    startTracking();
    focusTip();
  }

  /* ── Controles ───────────────────────────────────────────── */
  function next() {
    if (state.index + 1 >= state.tour.steps.length) { finish(); }
    else { showStep(state.index + 1); }
  }
  function prev() { if (state.index > 0) showStep(state.index - 1); }

  function cleanupUrl() {
    if (location.search.indexOf('tour=') !== -1 || location.search.indexOf('step=') !== -1) {
      var url = location.pathname + location.hash;
      window.history.replaceState({}, document.title, url);
    }
  }

  function teardown() {
    stopTracking();
    state.active = false;
    state.currentEl = null;
    if (dom.tip) { dom.tip.classList.remove('tour-visible'); }
    if (dom.spotlight) dom.spotlight.classList.remove('tour-visible');
    if (dom.backdrop) dom.backdrop.classList.remove('tour-visible');
    document.removeEventListener('keydown', onKey, true);
    // cerrar cualquier modal abierto por el tour
    closeOpenModals();
    if (state.lastFocus && state.lastFocus.focus) { try { state.lastFocus.focus(); } catch (e) {} }
    localStorage.removeItem(LS_ACTIVE);
  }

  function finish() {
    var tour = state.tour;
    if (tour) {
      markCompleted(tour.id);
      if (typeof tour.onEnd === 'function') { try { tour.onEnd(); } catch (e) {} }
    }
    localStorage.removeItem(LS_ACTIVE);
    document.removeEventListener('keydown', onKey, true);
    closeOpenModals();
    renderFinish();
    // el tour queda "inactivo" salvo por la pantalla final
    stopTracking();
    state.active = false;
  }

  function endHard() {
    var tour = state.tour;
    if (tour && typeof tour.onEnd === 'function') { try { tour.onEnd(); } catch (e) {} }
    teardown();
    cleanupUrl();
    state.tour = null;
  }

  function closeOpenModals() {
    if (!window.bootstrap) return;
    document.querySelectorAll('.modal.show').forEach(function (m) {
      var inst = window.bootstrap.Modal.getInstance(m);
      if (inst) inst.hide();
    });
  }

  /* ── Teclado ─────────────────────────────────────────────── */
  function onKey(e) {
    if (!state.active) return;
    if (e.key === 'Escape') { e.preventDefault(); endHard(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
  }

  /* ── Delegación de clics del popover ─────────────────────── */
  function onTipClick(e) {
    var btn = e.target.closest('[data-tour]');
    if (!btn) return;
    var act = btn.getAttribute('data-tour');
    if (act === 'next') next();
    else if (act === 'prev') prev();
    else if (act === 'skip') endHard();
    else if (act === 'finish-close') { teardown(); cleanupUrl(); state.tour = null; }
    else if (act === 'go-help') {
      teardown(); state.tour = null;
      location.assign('/gestion-matys/ayuda/');
    }
  }

  /* ── API pública ─────────────────────────────────────────── */
  function register(tour) { REGISTRY[tour.id] = tour; }
  function registerAll(list) { (list || []).forEach(register); }
  function get(id) { return REGISTRY[id]; }
  function all() { return Object.keys(REGISTRY).map(function (k) { return REGISTRY[k]; }); }

  function start(id, fromIndex) {
    var tour = REGISTRY[id];
    if (!tour) { console.warn('[MatysTour] tour no encontrado:', id); return; }
    buildDom();
    state.lastFocus = document.activeElement;
    state.tour = tour;
    state.active = true;
    dom.tip.removeEventListener('click', onTipClick);
    dom.tip.addEventListener('click', onTipClick);
    document.addEventListener('keydown', onKey, true);
    showStep(fromIndex || 0);
  }

  // Reanuda tras navegar entre páginas si la URL trae ?tour=&step=
  function resumeFromUrl() {
    var params = new URLSearchParams(location.search);
    var id = params.get('tour');
    if (!id || !REGISTRY[id]) return false;
    var step = parseInt(params.get('step'), 10);
    if (isNaN(step)) step = 0;
    // pequeño retraso para que el resto de scripts de la página monten
    setTimeout(function () { start(id, step); }, 350);
    return true;
  }

  window.MatysTour = {
    register: register,
    registerAll: registerAll,
    start: start,
    get: get,
    all: all,
    isCompleted: isCompleted,
    getCompleted: getCompleted,
    resumeFromUrl: resumeFromUrl,
    waitFor: waitFor,
    _registry: REGISTRY,
  };
})(window, document);
