document.addEventListener('DOMContentLoaded', () => {
  
  /* ==========================================
     ELEMENTOS DEL DOM
  ========================================== */
  
  const header = document.querySelector('.head-blur');
  const matysLogo = document.querySelector('.matys-logo');
  const colorModeIcon = document.querySelector('.color-mode-icon');
  const toggleColorModeButton = document.querySelector('.toggle-color-mode-button');
  const navLinks = document.querySelectorAll('.nav-link');
  const headerLinks = document.querySelectorAll('.header-link');
  const popUpImages = document.querySelectorAll('.pop-img');
  
  /* ==========================================
     INICIALIZACIÓN
  ========================================== */
  
  checkHeaderStatus();
  checkIconStatus();
  initSmoothScroll();
  
  /* ==========================================
     SMOOTH SCROLL CON LENIS
  ========================================== */
  
  function initSmoothScroll() {
    const lenis = new window.Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true
    });
    
    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }
    
    requestAnimationFrame(raf);
  }
  
  /* ==========================================
     TOGGLE TEMA CLARO/OSCURO
  ========================================== */
  
  function toggleColorMode() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('matys-theme', newTheme);
    
    checkHeaderStatus();
    checkIconStatus();
  }
  
  /* ==========================================
     VERIFICAR Y ACTUALIZAR ICONO DE TEMA
  ========================================== */
  
  function checkIconStatus() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    
    if (currentTheme === 'dark') {
      colorModeIcon.classList.remove('bi-moon-stars-fill');
      colorModeIcon.classList.add('bi-sun-fill');
    } else {
      colorModeIcon.classList.remove('bi-sun-fill');
      colorModeIcon.classList.add('bi-moon-stars-fill');
    }
  }
  
  /* ==========================================
     HEADER CON EFECTO BLUR AL SCROLL
  ========================================== */
  
  function checkHeaderStatus() {
    if (window.scrollY > 100) {
      header.classList.add('scrolled');
      
      // Cambiar color de enlaces en scroll
      headerLinks.forEach(link => {
        link.classList.add('text-body');
        link.classList.remove('text-light');
      });
      
      colorModeIcon.classList.add('text-body');
      colorModeIcon.classList.remove('text-light');
      
    } else {
      header.classList.remove('scrolled');
      
      // Restaurar color original de enlaces
      headerLinks.forEach(link => {
        link.classList.remove('text-body');
        link.classList.add('text-light');
      });
      
      colorModeIcon.classList.remove('text-body');
      colorModeIcon.classList.add('text-light');
    }
  }
  
  /* ==========================================
     ANIMACIÓN HOVER EN NAV LINKS
  ========================================== */
  
  navLinks.forEach(navLink => {
    navLink.addEventListener('mouseenter', () => {
      navLink.classList.add('nav-link-enter');
      navLink.classList.remove('nav-link-leave');
    });
    
    navLink.addEventListener('mouseleave', () => {
      navLink.classList.add('nav-link-leave');
      navLink.classList.remove('nav-link-enter');
    });
  });
  
  /* ==========================================
     INTERSECTION OBSERVER PARA ANIMACIONES
  ========================================== */
  
  const observerOptions = {
    threshold: 0.3,
    rootMargin: '0px 0px -100px 0px'
  };
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add('intersecting');
        }, index * 150);
        
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);
  
  // Observar elementos con animación
  popUpImages.forEach(img => observer.observe(img));
  
  /* ==========================================
     CERRAR MENÚ MÓVIL AL HACER CLIC EN ENLACE
  ========================================== */
  
  const navbarToggler = document.querySelector('.navbar-toggler');
  const navbarCollapse = document.querySelector('.navbar-collapse');
  
  if (navbarCollapse) {
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 992 && navbarCollapse.classList.contains('show')) {
          navbarToggler.click();
        }
      });
    });
  }
  
  /* ==========================================
     EFECTO PARALLAX EN HERO (DESACTIVADO)
  ========================================== */
  
  // Parallax desactivado para evitar efecto visual no deseado
  
  /* ==========================================
     LAZY LOADING PARA IMÁGENES
  ========================================== */
  
  const lazyImages = document.querySelectorAll('img[data-src]');
  
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  });
  
  lazyImages.forEach(img => imageObserver.observe(img));
  
  /* ==========================================
     EVENTOS
  ========================================== */
  
  window.addEventListener('scroll', checkHeaderStatus);
  toggleColorModeButton.addEventListener('click', toggleColorMode);
  
  /* ==========================================
     VALIDACIÓN DE FORMULARIOS BOOTSTRAP
  ========================================== */
  
  const forms = document.querySelectorAll('.needs-validation');
  
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      
      form.classList.add('was-validated');
    }, false);
  });
  
  /* ==========================================
     ANIMACIÓN DE NÚMEROS (CONTADORES)
  ========================================== */
  
  const counters = document.querySelectorAll('.counter');
  
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const counter = entry.target;
        const target = +counter.getAttribute('data-target');
        const duration = 2000;
        const step = target / (duration / 16);
        
        let current = 0;
        const updateCounter = () => {
          current += step;
          if (current < target) {
            counter.textContent = Math.floor(current);
            requestAnimationFrame(updateCounter);
          } else {
            counter.textContent = target;
          }
        };
        
        updateCounter();
        counterObserver.unobserve(counter);
      }
    });
  }, { threshold: 0.5 });
  
  counters.forEach(counter => counterObserver.observe(counter));
  
  /* ==========================================
     PRELOADER (OPCIONAL)
  ========================================== */
  
  window.addEventListener('load', () => {
    const preloader = document.querySelector('.preloader');
    if (preloader) {
      setTimeout(() => {
        preloader.style.opacity = '0';
        setTimeout(() => {
          preloader.style.display = 'none';
        }, 300);
      }, 500);
    }
  });
  
  /* ==========================================
     FUNCIONALIDAD DE DETALLE DE PRENDA
  ========================================== */
  /* NOTA: la búsqueda del catálogo se resuelve en el servidor (vista
     `prendas`) con auto-submit; su handler vive en prendas.html. */
  
  // Cambiar imagen principal al hacer clic en miniatura
  const thumbnails = document.querySelectorAll('.thumbnail');
  const mainImage = document.getElementById('mainImage');
  
  if (thumbnails.length > 0 && mainImage) {
    thumbnails.forEach(thumb => {
      thumb.addEventListener('click', function() {
        // Remover clase active de todas las miniaturas
        thumbnails.forEach(t => t.classList.remove('active'));
        
        // Agregar clase active a la miniatura clickeada
        this.classList.add('active');
        
        // Cambiar imagen principal con efecto de transición
        mainImage.style.opacity = '0.5';
        setTimeout(() => {
          mainImage.src = this.getAttribute('data-full');
          mainImage.style.opacity = '1';
        }, 200);
      });
    });
  }
  
  // Selector de tallas
  const sizeButtons = document.querySelectorAll('.size-btn');
  
  if (sizeButtons.length > 0) {
    sizeButtons.forEach(btn => {
      btn.addEventListener('click', function() {
        // Remover clase active de todos los botones
        sizeButtons.forEach(b => b.classList.remove('active'));
        
        // Agregar clase active al botón clickeado
        this.classList.add('active');
        
        // Marcar la talla activa (se usa al construir el mensaje de WhatsApp)
        this.setAttribute('aria-pressed', 'true');
        sizeButtons.forEach(b => { if (b !== this) b.setAttribute('aria-pressed', 'false'); });
      });
    });
  }
});







/**
 * Función para alternar el estado (activo/inactivo) de una opción de contacto.
 * Simula el comportamiento de un acordeón o menú desplegable.
 */
function toggleDetails(element) {
    // 1. Alterna la clase 'active' en el elemento clickeado.
    // Esto activa los estilos CSS para el despliegue y rotación de flecha.
    element.classList.toggle('active');

    // OPCIONAL: Desactiva otros elementos si solo quieres que uno esté abierto a la vez.
    // const allOptions = document.querySelectorAll('.contact-option');
    // allOptions.forEach(option => {
    //     if (option !== element && option.classList.contains('active')) {
    //         option.classList.remove('active');
    //     }
    // });
}

  
  /* ==========================================
     COTIZACIÓN POR WHATSAPP CON DATOS DINÁMICOS
  ========================================== */
  
  const btnCotizacion = document.getElementById('btnCotizacion');

  if (btnCotizacion) {
    // Número de WhatsApp de la empresa (editable desde el panel → Inicio)
    const whatsappNumber = document.body.dataset.whatsapp || '50498267040';

    // Construye el mensaje de cotización SIEMPRE con el enlace directo a la
    // prenda. La URL actual (window.location) es exactamente la del producto
    // que se está viendo, por lo que apunta siempre al artículo correcto y le
    // sirve tanto al cliente como al administrador para abrir la ficha exacta.
    function buildCotizacionURL() {
      const productName = document.querySelector('h2')?.textContent.trim() || 'una prenda';
      const productPrice = document.querySelector('.product-price')?.textContent.trim() || 'Consultar';
      const selectedSizeBtn = document.querySelector('.size-btn.active');
      const selectedSize = selectedSizeBtn ? selectedSizeBtn.getAttribute('data-size') : 'No seleccionada';
      const productURL = window.location.href;

      const message = `Hola Matys, me interesa solicitar una cotización:

📦 *Producto:* ${productName}
💰 *Precio:* ${productPrice}
📏 *Talla:* ${selectedSize}
🔗 *Enlace:* ${productURL}

¿Podrían confirmarme disponibilidad y tiempo de entrega?`;

      return `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(message)}`;
    }

    btnCotizacion.addEventListener('click', function () {
      window.open(buildCotizacionURL(), '_blank');
    });

    // El botón flotante de WhatsApp, en la ficha de producto, también apunta a
    // la prenda concreta (mismo mensaje) en lugar del texto genérico del sitio.
    const floatingWhatsApp = document.querySelector('#whatsapp-contacts a');
    if (floatingWhatsApp) {
      floatingWhatsApp.href = buildCotizacionURL();
    }
  }
