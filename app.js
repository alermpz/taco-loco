// ==========================================
// CONFIGURACIÓN DE URLS (Google Sheets)
// ==========================================
const URL_CSV_MENU = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=357751603&single=true&output=csv";
const URL_CSV_RESENAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=764839671&single=true&output=csv";
const URL_APPS_SCRIPT_RESENAS = "https://script.google.com/macros/s/AKfycbxCGiDEUAAvVXv4cfm05ajiVKotnCYgeQv8wmePsQoM_GgkCp8poM7iSCGGj5TEbIm4/exec";
const URL_APPS_SCRIPT_PEDIDOS = "https://script.google.com/macros/s/AKfycbyHzbARjCcog41iCwBvCvA4aburgAlGGHSA5EEQuGP64CQe36-j-piizwITeysVVA5u/exec";
const URL_CSV_CONFIG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=1180476633&single=true&output=csv"; // <-- ¡Pega aquí el enlace CSV de tu pestaña Configuración!
const WHATSAPP_NUMBER = "529611232147";

// ==========================================
// ESTADO GLOBAL DE LA APP (Memoria)
// ==========================================
const state = {
    carrito: {},      // { "Taco de Res": { precio: 15, cant: 2 }, ... }
    menu: { tacos: [], bebidas: [] },
    resenas: [],
    tiendaAbierta: true,
    forzarEstado: "AUTO" // Puede ser "AUTO", "CERRADO", o "ABIERTO"
};

// ==========================================
// CONTROL DE HORARIO DE PEDIDOS (8:00 PM - 10:30 PM)
// ==========================================
function estaEnHorario() {
    // 1. Validar el override por Google Sheets
    if (state.forzarEstado === "ABIERTO") return true;
    if (state.forzarEstado === "CERRADO") return false;

    // 2. Si está en "AUTO", procedemos con lógica de días normal
    const ahora = new Date();
    const dia = ahora.getDay(); // 0=Dom, 1=Lun, 2=Mar, 3=Mié, 4=Jue, 5=Vie, 6=Sáb
    const hora = ahora.getHours();
    const minutos = ahora.getMinutes();
    const tiempoActual = hora * 60 + minutos;
    const apertura = 20 * 60;       // 8:00 PM = minuto 1200
    const cierre = 22 * 60 + 30;    // 10:30 PM = minuto 1350

    const diasPermitidos = [1, 2, 3]; // Lunes, Martes, Miércoles
    const esDiaValido = diasPermitidos.includes(dia);
    const esHoraValida = tiempoActual >= apertura && tiempoActual < cierre;

    return esDiaValido && esHoraValida;
}

function verificarHorario() {
    const abierto = estaEnHorario();
    state.tiendaAbierta = abierto;

    const banner = document.getElementById('schedule-banner');
    if (banner) {
        if (abierto) {
            banner.classList.add('hidden');
        } else {
            banner.classList.remove('hidden');

            // Mensaje dinámico según si es día o hora incorrecta
            const ahora = new Date();
            const dia = ahora.getDay();
            const diasPermitidos = [1, 2, 3];
            const bannerTitle = banner.querySelector('.banner-title');
            const bannerSub = banner.querySelector('.banner-sub');

            if (state.forzarEstado === "CERRADO") {
                if (bannerTitle) bannerTitle.textContent = 'Cerrado temporalmente';
                if (bannerSub) bannerSub.innerHTML = 'Por el momento no estamos aceptando pedidos. ¡Regresaremos pronto!';
            } else if (!diasPermitidos.includes(dia)) {
                if (bannerTitle) bannerTitle.textContent = 'Hoy no hay servicio de pedidos';
                if (bannerSub) bannerSub.innerHTML = 'Pedidos solo <strong>Lunes, Martes y Miércoles</strong> de <strong>8:00 PM</strong> a <strong>10:30 PM</strong>';
            } else {
                if (bannerTitle) bannerTitle.textContent = 'Fuera de horario de pedidos';
                if (bannerSub) bannerSub.innerHTML = 'Aceptamos pedidos de <strong>8:00 PM</strong> a <strong>10:30 PM</strong>';
            }

            // Si la tienda cierra mientras tienen items, vaciar carrito
            if (Object.keys(state.carrito).length > 0) {
                state.carrito = {};
                actualizarCarritoHUD();
            }
        }
    }

    // Actualizar estado visual de botones del menú
    actualizarBotonesMenu();
}

// ==========================================
// 1. INICIALIZACIÓN DE LA SPA
// ==========================================
document.addEventListener("DOMContentLoaded", async () => {
    // Escuchar cambios de slider de reseñas en tiempo real
    document.getElementById("rev-stars").addEventListener("input", (e) => {
        document.getElementById("star-display").textContent = "⭐".repeat(e.target.value);
    });

    // Cargar datos asíncronos y mostrar vista principal
    await cargarConfiguracion(); // Descargamos la config de apertura manual
    await cargarMenu();
    await cargarResenas();

    document.getElementById("loader").classList.add("hidden");
    document.getElementById("view-menu").classList.remove("hidden");
    document.getElementById("main-footer").classList.remove("hidden");

    // Iniciar el enrutador
    initRouter();
    // Iniciar eventos del Carrito
    initCartEvents();
    // Inicializar menús fijos y scroll listeners
    initScrollSpy();
    // Inicializar animaciones de scroll
    initRevealAnimations();

    // Verificar horario de pedidos y actualizar cada 60 segundos
    verificarHorario();
    setInterval(async () => {
        await cargarConfiguracion();
        verificarHorario();
    }, 60000);
});

// ==========================================
// ANIMACIONES DE SCROLL (REVEAL ON SCROLL)
// ==========================================
function initRevealAnimations() {
    // Auto-agregar clase 'reveal' a elementos clave
    const selectors = '.product-card, .value-card, .review-card, .glass-card, .hero-text, .section-heading';
    document.querySelectorAll(selectors).forEach(el => {
        if (!el.classList.contains('reveal')) el.classList.add('reveal');
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, i) => {
            if (entry.isIntersecting) {
                // Escalonamiento sutil para efecto cascada
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, i * 60);
                observer.unobserve(entry.target);
            }
        });
    }, { rootMargin: '0px 0px -50px 0px', threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// ==========================================
// 2. LÓGICA DE NAVEGACIÓN (ROUTER SPA)
// ==========================================
function initRouter() {
    const navItems = document.querySelectorAll(".nav-item");
    const views = document.querySelectorAll(".view");
    const header = document.getElementById("main-header");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            // Actualizar botones activos
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            // Obtener el target a mostrar
            const targetId = item.getAttribute("data-target");

            // Ocultar cabecera solo si no es menú
            if (targetId === "view-menu") header.classList.remove("hidden");
            else header.classList.add("hidden");

            // Ocultar todas las vistas con opacidad, y quitar display none
            views.forEach(v => {
                if (!v.classList.contains("hidden")) {
                    v.classList.add("hidden");
                }
            });

            // Mostrar vista seleccionada
            const targetView = document.getElementById(targetId);
            targetView.classList.remove("hidden");

            // Recalcular métricas de animación si entramos a "Conócenos"
            if (targetId === "view-about" && typeof window.recalcularAnimacionTaco === 'function') {
                window.recalcularAnimacionTaco();
            }

            // Scroll hacia arriba
            if (targetId === "view-menu") {
                // Darle tiempo a pintar para que el sticky no se vuelva loco
                setTimeout(() => window.scrollTo({ top: document.getElementById("main-header").offsetHeight, behavior: "smooth" }), 100);
            } else {
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    });
}

function initScrollSpy() {
    const stickyNav = document.getElementById("sticky-category-nav");
    const header = document.getElementById("main-header");

    // Primero, ocultar/mostrar si pasamos el main-header o cuando usamos navs
    window.addEventListener("scroll", () => {
        // Solo importa si estamos en la vista Menu
        if (document.getElementById("view-menu").classList.contains("hidden")) return;

        // Obtenemos la altura del hero banner
        const hitPoint = header.offsetHeight - 50;
        if (window.scrollY > hitPoint) {
            stickyNav.classList.remove("hidden-nav");
        } else {
            stickyNav.classList.add("hidden-nav");
        }
    }, { passive: true });

    // Detectar en qué sección estamos (Tacos o Bebidas) usando IntersectionObserver
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Quita 'active' a todos
                const pills = document.querySelectorAll(".category-pill");
                pills.forEach(p => p.classList.remove("active"));

                // Agrega al actual
                if (entry.target.id === "seccion-tacos") pills[0]?.classList.add("active");
                if (entry.target.id === "seccion-bebidas") pills[1]?.classList.add("active");
            }
        });
    }, { rootMargin: "-100px 0px -60% 0px", threshold: 0 });

    const sTacos = document.getElementById("seccion-tacos");
    const sBebidas = document.getElementById("seccion-bebidas");
    if (sTacos) observer.observe(sTacos);
    if (sBebidas) observer.observe(sBebidas);
}

// ==========================================
// 3. CARGA DE BASE DE DATOS (PAPAPARSE)
// ==========================================
async function cargarMenu() {
    return new Promise((resolve) => {
        Papa.parse(URL_CSV_MENU, {
            download: true,
            header: true,
            complete: function (results) {
                const data = results.data;
                data.forEach(row => {
                    const obj = {
                        nombre: row.Nombre?.trim(),
                        precio: parseFloat(row.Precio),
                        img: row.Imagen?.trim(),
                        desc: row.Descripcion?.trim() || "",
                        categoria: row.Categoria?.trim().toLowerCase()
                    };
                    if (!obj.nombre || isNaN(obj.precio)) return; // Salto si fila vacía

                    if (obj.categoria === "taco") state.menu.tacos.push(obj);
                    else if (obj.categoria === "bebida") state.menu.bebidas.push(obj);
                });
                renderizarMenu();
                resolve();
            },
            error: function (err) {
                console.error("Error cargando el menú", err);
                toastErr("Error cargando menú del Excel");
                resolve();
            }
        });
    });
}

async function cargarResenas() {
    return new Promise((resolve) => {
        Papa.parse(URL_CSV_RESENAS, {
            download: true,
            header: true,
            complete: function (results) {
                state.resenas = results.data.filter(r => r.Nombre && r.Nombre.trim() !== "");
                renderizarResenas();
                resolve();
            },
            error: function (err) {
                console.error("Error cargando reseñas", err);
                resolve();
            }
        });
    });
}

async function cargarConfiguracion() {
    if (!URL_CSV_CONFIG || URL_CSV_CONFIG.trim() === "") {
        return Promise.resolve(); // Si el usuario no ha puesto la URL, pasamos
    }

    return new Promise((resolve) => {
        Papa.parse(URL_CSV_CONFIG, {
            download: true,
            header: true,
            complete: function (results) {
                const data = results.data;
                const rowEstado = data.find(r => r.Clave && r.Clave.trim() === "ForzarEstado");
                
                if (rowEstado && rowEstado.Valor) {
                    const val = rowEstado.Valor.trim().toUpperCase();
                    if (["AUTO", "ABIERTO", "CERRADO"].includes(val)) {
                        state.forzarEstado = val;
                    } else {
                        state.forzarEstado = "AUTO"; // Valor por defecto ante errores
                    }
                }
                resolve();
            },
            error: function (err) {
                console.error("Error cargando la hoja de configuración", err);
                resolve();
            }
        });
    });
}

// ==========================================
// 4. RENDERIZADO DEL MENÚ Y RESEÑAS
// ==========================================
function renderizarMenu() {
    const contenedorTacos = document.getElementById("tacos-container");
    const contenedorBebidas = document.getElementById("bebidas-container");

    let htmlTacos = "";
    state.menu.tacos.forEach((taco) => {
        const cleanName = taco.nombre.replace(/'/g, "\\'");

        // Etiqueta de más vendido inteligente
        const isBestSeller = taco.nombre.toLowerCase().includes("puerco");
        const badgeHtml = isBestSeller ? `<span class="badge-tag">🥇 Más Vendido</span>` : '';

        htmlTacos += `
        <div class="product-card">
            <div>
                <div class="img-wrapper">
                    ${badgeHtml}
                    <img src="${taco.img}" onerror="this.src=''" alt="${taco.nombre}" loading="lazy">
                </div>
                <h3 class="product-title" style="margin-top: 6px;">${taco.nombre}</h3>
                <p class="product-desc">${taco.desc}</p>
            </div>
            <div>
                <span class="product-price">$${taco.precio}</span>
                <div id="controls-${taco.nombre.replace(/\s/g, "")}" class="btn-wrap">
                    <button class="btn-primary flex-btn" style="padding:10px;" onclick="agregarAlCarrito('${cleanName}')">Agregar al pedido</button>
                </div>
            </div>
        </div>`;
    });
    contenedorTacos.innerHTML = htmlTacos;

    let htmlBebidas = "";
    state.menu.bebidas.forEach((bebida) => {
        const cleanName = bebida.nombre.replace(/'/g, "\\'");
        htmlBebidas += `
        <div class="product-card">
            <div>
                <div class="img-wrapper">
                    <img src="${bebida.img}" onerror="this.src=''" alt="${bebida.nombre}" loading="lazy">
                </div>
                <h3 class="product-title" style="margin-top: 6px;">${bebida.nombre}</h3>
                <p class="product-desc">${bebida.desc || ""}</p>
            </div>
            <div>
                <span class="product-price">$${bebida.precio}</span>
                <div id="controls-${bebida.nombre.replace(/\s/g, "")}" class="btn-wrap">
                    <button class="btn-primary flex-btn" style="padding:10px;" onclick="agregarAlCarrito('${cleanName}')">Agregar al pedido</button>
                </div>
            </div>
        </div>`;
    });
    contenedorBebidas.innerHTML = htmlBebidas;
    actualizarBotonesMenu();
}

function renderizarResenas() {
    const contenedor = document.getElementById("reviews-container");
    if (state.resenas.length === 0) {
        contenedor.innerHTML = `<p class="text-center font-bold">Aún no hay reseñas. ¡Sé el primero!</p>`;
        return;
    }

    // Calcular promedio
    let suma = 0;
    state.resenas.forEach(r => {
        let stars = parseInt(parseFloat(r.Estrellas));
        if (isNaN(stars) || stars < 1) stars = 5;
        suma += stars;
    });
    const prom = (suma / state.resenas.length).toFixed(1);

    document.getElementById("avg-score").textContent = prom;
    document.getElementById("review-count").textContent = state.resenas.length;

    let html = "";
    const revArray = [...state.resenas].reverse(); // Más nuevas primero

    revArray.forEach(r => {
        let estrellas = parseInt(parseFloat(r.Estrellas));
        if (isNaN(estrellas) || estrellas < 1) estrellas = 5;

        const estHtm = "⭐".repeat(estrellas);
        let imgHtm = "";

        // Si hay URL de imagen y viene de Drive
        if (r.ImagenURL && r.ImagenURL !== "" && r.ImagenURL.includes("id=")) {
            const fileId = r.ImagenURL.split("id=")[1].split("&")[0];
            const thumbUrl = `https://drive.google.com/thumbnail?id=${fileId}&sz=w800`;
            imgHtm = `<img src="${thumbUrl}" loading="lazy" style="width:100%;border-radius:10px;margin-top:12px;object-fit:cover;max-height:220px;" onerror="this.style.display='none'">`;
        }

        html += `
        <div class="review-card">
            <div class="stars">${estHtm}</div>
            <p class="text">"${r.Comentarios || r.Comentario || ""}"</p>
            <p class="author">— ${r.Nombre} · ${r.Fecha}</p>
            ${imgHtm}
        </div>`;
    });
    contenedor.innerHTML = html;
}

// ==========================================
// 5. LÓGICA DEL CARRITO DE COMPRAS Y BOTTOM SHEET
// ==========================================
window.agregarAlCarrito = function (nombreItem) {
    // Guardia de horario
    if (!state.tiendaAbierta) {
        Swal.fire({
            icon: 'info',
            title: '🕗 Estamos cerrados',
            html: 'Nuestro horario de pedidos es:<br><strong>Lunes, Martes y Miércoles</strong><br>de <strong>8:00 PM a 10:30 PM</strong><br>¡Te esperamos!',
            confirmButtonColor: '#FF6B00'
        });
        return;
    }

    const item = [...state.menu.tacos, ...state.menu.bebidas].find(i => i.nombre === nombreItem);
    if (!item) return;

    if (state.carrito[item.nombre]) {
        state.carrito[item.nombre].cant++;
    } else {
        state.carrito[item.nombre] = { precio: item.precio, cant: 1 };
    }
    toastOk(`¡1 ${item.nombre} agregado!`);
    actualizarCarritoHUD();

    // Animación de agitar para el Carrito HUD
    const flotante = document.getElementById("floating-cart");
    flotante.classList.remove("cart-shake");
    void flotante.offsetWidth; // Dispara un reflow para reiniciar la animacion
    flotante.classList.add("cart-shake");
};

window.quitarDelCarrito = function (nombreItem) {
    if (state.carrito[nombreItem]) {
        state.carrito[nombreItem].cant--;
        if (state.carrito[nombreItem].cant <= 0) {
            delete state.carrito[nombreItem];
        }
        toastErr(`¡1 ${nombreItem} quitado!`);
        actualizarCarritoHUD();
    }
};

function actualizarBotonesMenu() {
    // Restaurar primero todos los botones
    const allBtnWraps = document.querySelectorAll(".btn-wrap");

    // Obtener todo el menu para restaurar el boton Add
    [...state.menu.tacos, ...state.menu.bebidas].forEach(item => {
        const cleanName = item.nombre.replace(/\s/g, "");
        const cnt = document.getElementById(`controls-${cleanName}`);
        if (!cnt) return;

        const cartItem = state.carrito[item.nombre];

        // Si la tienda está cerrada, mostrar botón deshabilitado
        if (!state.tiendaAbierta) {
            cnt.innerHTML = `<button class="btn-disabled-schedule">🕗 Abrimos a las 8 PM</button>`;
            return;
        }

        if (cartItem && cartItem.cant > 0) {
            // Mostrar contador +-
            cnt.innerHTML = `
            <div class="qty-controls">
                <button class="qty-btn" onclick="quitarDelCarrito('${item.nombre.replace(/'/g, "\\'")}')">－</button>
                <span class="qty-display">${cartItem.cant}</span>
                <button class="qty-btn" onclick="agregarAlCarrito('${item.nombre.replace(/'/g, "\\'")}')">＋</button>
            </div>
            `;
        } else {
            // Mostrar boton normal
            cnt.innerHTML = `<button class="btn-primary flex-btn" style="padding:10px;" onclick="agregarAlCarrito('${item.nombre.replace(/'/g, "\\'")}')">Agregar al pedido</button>`;
        }
    });

    renderizarModalCarrito();
}

function actualizarCarritoHUD() {
    let totalItems = 0;
    let totalDinero = 0;

    for (let key in state.carrito) {
        totalItems += state.carrito[key].cant;
        totalDinero += (state.carrito[key].cant * state.carrito[key].precio);
    }

    const flotante = document.getElementById("floating-cart");
    const badge = document.getElementById("cart-badge");
    const bTotal = document.getElementById("cart-total");
    const mdTotal = document.getElementById("modal-total");

    badge.textContent = totalItems;
    bTotal.textContent = `$${totalDinero.toFixed(2)}`;
    mdTotal.textContent = `$${totalDinero.toFixed(2)}`;

    if (totalItems > 0) {
        flotante.classList.remove("hidden");
    } else {
        flotante.classList.add("hidden");
        // Si el modal está abierto y se vació, cerramos el modal
        const modal = document.getElementById("cart-modal-overlay");
        if (!modal.classList.contains("hidden")) {
            modal.classList.add("hidden");
        }
    }

    actualizarBotonesMenu();
}

function initCartEvents() {
    const modal = document.getElementById("cart-modal-overlay");
    const flotante = document.getElementById("floating-cart");
    const btnCerrar = document.getElementById("close-modal");

    // Abrir Modal
    flotante.addEventListener("click", () => {
        modal.classList.remove("hidden");
    });

    // Cerrar Modal
    btnCerrar.addEventListener("click", () => {
        modal.classList.add("hidden");
    });

    // Cerrar si se da click fuera del contenido (en el overlay)
    modal.addEventListener("click", (e) => {
        if (e.target === modal) {
            modal.classList.add("hidden");
        }
    });

    // Cambiar vista de transferencia si selecciona
    document.getElementById("order-payment").addEventListener("change", (e) => {
        const tBox = document.getElementById("transfer-info");
        if (e.target.value === "Transferencia 📱") tBox.classList.remove("hidden");
        else tBox.classList.add("hidden");
    });

    // Vaciar carrito
    document.getElementById("btn-empty-cart").addEventListener("click", () => {
        state.carrito = {};
        actualizarCarritoHUD();
        modal.classList.add("hidden");
    });

    // Enviar pedido
    document.getElementById("btn-confirm-order").addEventListener("click", evConfirmOrder);

    // Formulario Reseñas
    document.getElementById("review-form").addEventListener("submit", evSubmitResena);
}

function renderizarModalCarrito() {
    const list = document.getElementById("cart-items");
    let html = "";

    let tieneTacos = false;
    let tieneBebidas = false;

    for (let n in state.carrito) {
        const curr = state.carrito[n];

        // Evaluar condiciones para el Up-sell cruzado
        const esTaco = state.menu.tacos.some(t => t.nombre === n);
        const esBebida = state.menu.bebidas.some(b => b.nombre === n);
        if (esTaco) tieneTacos = true;
        if (esBebida) tieneBebidas = true;

        const safeObjName = n.replace(/'/g, "\\'");
        html += `
        <div class="cart-item-row">
            <div class="cart-item-info">
                <p class="cart-item-name">${n}</p>
                <p class="cart-item-price">$${curr.precio} x ${curr.cant} = $${curr.precio * curr.cant}</p>
            </div>
            <div class="cart-item-qty">
                <button class="clr-red qty-btn" onclick="quitarDelCarrito('${safeObjName}')">－</button>
                <span class="font-bold" style="padding: 0 5px;">${curr.cant}</span>
                <button class="clr-primary qty-btn" onclick="agregarAlCarrito('${safeObjName}')">＋</button>
            </div>
        </div>
        `;
    }
    list.innerHTML = html;

    // ==========================================
    // LOGICA DE UP-SELL (VENTAS CRUZADAS)
    // ==========================================
    const upsellContainer = document.getElementById("upsell-container");
    // Si metió tacos pero ignoró las bebidas, le sugerimos bebidas inmediatamente!
    if (tieneTacos && !tieneBebidas && state.menu.bebidas.length > 0) {
        let upsellHtml = `
            <div class="upsell-section">
                <h4 class="upsell-title">🥤 ¿Se te antoja algo de tomar?</h4>
                <div class="upsell-items">
        `;

        // Sugerimos hasta un máximo de 4 bebidas aleatoriamente o las primeras 4
        const suggestedDrinks = state.menu.bebidas.slice(0, 4);
        suggestedDrinks.forEach(b => {
            const cleanName = b.nombre.replace(/'/g, "\\'");
            upsellHtml += `
                <div class="upsell-card">
                    <div class="upsell-img-box">
                        <img src="${b.img}" onerror="this.src=''" alt="${b.nombre}">
                    </div>
                    <p class="upsell-card-name">${b.nombre}</p>
                    <p class="upsell-card-price">$${b.precio}</p>
                    <button class="upsell-btn" onclick="agregarAlCarrito('${cleanName}')">+ Agregar</button>
                </div>
            `;
        });

        upsellHtml += `
                </div>
            </div>
        `;
        upsellContainer.innerHTML = upsellHtml;
    } else {
        upsellContainer.innerHTML = ""; // Se limpia si ya compró bebida o no tiene tacos
    }
}

// ==========================================
// 6. FLUJO DE PEDIDO, WHATSAPP Y EXCEL
// ==========================================
function evConfirmOrder() {
    // ======== RATE LIMITING PARA PEDIDOS (1 minuto) ========
    const lastOrderTime = localStorage.getItem("lastOrderTime");
    const now = Date.now();
    if (lastOrderTime && now - parseInt(lastOrderTime) < 60000) {
        Swal.fire({
            icon: 'warning',
            title: 'Espera un momento',
            text: 'Has realizado un pedido recientemente. Por favor espera 1 minuto antes de enviar otro.',
            confirmButtonColor: '#FF6B00'
        });
        return;
    }
    // =======================================================

    // ======== VERIFICACIÓN DE HORARIO ========
    if (!state.tiendaAbierta) {
        Swal.fire({
            icon: 'info',
            title: '🕗 Fuera de horario',
            html: 'Los pedidos solo se aceptan<br><strong>Lunes, Martes y Miércoles</strong><br>de <strong>8:00 PM a 10:30 PM</strong>',
            confirmButtonColor: '#FF6B00'
        });
        return;
    }
    // =========================================

    const nombre = document.getElementById("order-name").value.trim();
    const dir = document.getElementById("order-address").value.trim();
    const ref = document.getElementById("order-ref").value.trim();
    const notas = document.getElementById("order-notes").value.trim();
    const pago = document.getElementById("order-payment").value;

    if (!nombre || !dir) {
        Swal.fire({
            icon: 'error',
            title: 'Oops...',
            text: '¡Por favor llena tu nombre y dirección!',
            confirmButtonColor: '#FF6B00'
        });
        return;
    }

    let textoPedidoWhastapp = "";
    let textoPedidoExcel = "";
    let totalVenta = 0;

    for (let key in state.carrito) {
        const cant = state.carrito[key].cant;
        const subtotal = cant * state.carrito[key].precio;
        totalVenta += subtotal;

        textoPedidoWhastapp += `• ${cant}x ${key} ($${subtotal})\n`;
        textoPedidoExcel += `${cant}x ${key}, `;
    }

    let msgNotas = notas ? `\n📝 *Notas:* ${notas}\n` : "\n";
    let msgWhatsApp = `Hola Taco Loco 🌮, soy *${nombre}*.\n\n*MI PEDIDO:*\n${textoPedidoWhastapp}${msgNotas}\n💰 *Total de platillos: $${totalVenta}*\n📍 *Dir:* ${dir}\n🏠 *Ref:* ${ref}\n💸 *Pago:* ${pago}\n\n🛵 *Nota: El costo de envío por mandadito es extra y depende de la distancia.*`;

    if (pago === "Transferencia 📱") {
        msgWhatsApp += `\n\n🧾 *Adjunto mi comprobante de transferencia.*`;
    }

    // Preparar objeto para Excel (Segundo Plano sin Bloquear)
    const datosExcel = {
        cliente: nombre,
        direccion: `${dir} (${ref})`,
        pedido: notas ? `${textoPedidoExcel} | NOTAS: ${notas}` : textoPedidoExcel,
        total: totalVenta,
        pago: pago
    };

    fetch(URL_APPS_SCRIPT_PEDIDOS, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datosExcel)
    }).catch(e => console.log("Post background Excel err:", e));
    
    // ======== REGISTRAR TIEMPO DE PEDIDO ========
    localStorage.setItem("lastOrderTime", Date.now());
    // ===========================================

    // Mostrar alerta de éxito
    document.getElementById("cart-modal-overlay").classList.add("hidden");

    Swal.fire({
        title: '¡Pedido Generado!',
        text: "Vamos a abrir WhatsApp para enviar tu pedido.",
        icon: 'success',
        confirmButtonText: 'Enviar WhatsApp',
        confirmButtonColor: '#FF6B00',
        allowOutsideClick: false
    }).then((result) => {
        if (result.isConfirmed) {
            const encoded = encodeURIComponent(msgWhatsApp);
            const wUrl = `https://api.whatsapp.com/send?phone=${WHATSAPP_NUMBER}&text=${encoded}`;
            window.open(wUrl, '_blank');
            // Vaciar carrito
            state.carrito = {};
            actualizarCarritoHUD();
        }
    });
}

// ==========================================
// 7. ENVÍO DE FORMULARIO DE RESEÑAS
// ==========================================
async function evSubmitResena(e) {
    e.preventDefault();

    // ======== RATE LIMITING PARA RESEÑAS (1 minuto) ========
    const lastReviewTime = localStorage.getItem("lastReviewTime");
    const now = Date.now();
    if (lastReviewTime && now - parseInt(lastReviewTime) < 60000) {
        toastErr("Has publicado una reseña recientemente. Por favor espera 1 minuto.");
        return;
    }
    // =======================================================
    const btn = e.target.querySelector("button[type='submit']");
    btn.textContent = "Enviando...";
    btn.disabled = true;

    const nombre = document.getElementById("rev-name").value;
    const estrellas = document.getElementById("rev-stars").value;
    const comentario = document.getElementById("rev-comment").value;

    const dt = new Date();
    const strFecha = `${("0" + dt.getDate()).slice(-2)}/${("0" + (dt.getMonth() + 1)).slice(-2)}/${dt.getFullYear()}`;

    const imageInput = document.getElementById("rev-image");
    let base64String = "";
    let mimeType = "";
    let fileName = "";

    if (imageInput && imageInput.files.length > 0) {
        const file = imageInput.files[0];
        fileName = file.name;
        mimeType = file.type;
        btn.textContent = "Procesando imagen...";

        try {
            base64String = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result.split(',')[1]);
                reader.onerror = error => reject(error);
                reader.readAsDataURL(file);
            });
        } catch (error) {
            console.error("Error al leer la imagen:", error);
            toastErr("No se pudo procesar la imagen.");
            btn.textContent = "Publicar Reseña ⭐";
            btn.disabled = false;
            return; // Salir si falla la imagen
        }
    }

    btn.textContent = "Enviando...";

    const nueva = {
        nombre: nombre,
        estrellas: parseInt(estrellas),
        comentario: comentario,
        fecha: strFecha,
        imagen_b64: base64String,
        imagen_tipo: mimeType,
        imagen_nombre: fileName
    };

    // Agregar a la UI inmediatamente para dar sensación de rapidez ("Optimistic UI")
    state.resenas.unshift({
        Nombre: nombre,
        Estrellas: estrellas,
        Comentarios: comentario,
        Fecha: "Justo ahora"
    });
    renderizarResenas();

    // Guardar en Apps Script sin bloquear
    fetch(URL_APPS_SCRIPT_RESENAS, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nueva)
    })
        .catch(err => console.error(err))
        .finally(() => {
            // ======== REGISTRAR TIEMPO DE RESEÑA ========
            localStorage.setItem("lastReviewTime", Date.now());
            // ============================================

            btn.textContent = "Publicar Reseña ⭐";
            btn.disabled = false;
            e.target.reset();
            document.getElementById("star-display").textContent = "⭐⭐⭐⭐⭐";
            toastOk("¡Reseña publicada! Gracias.");
        });
}

// ==========================================
// 8. TOASTS UTILIDADES (SweetAlert2 Mixin)
// ==========================================
const Toast = Swal.mixin({
    toast: true, position: 'top-end', showConfirmButton: false, timer: 2000,
    timerProgressBar: true, background: '#FF6B00', color: '#fff',
    customClass: { popup: 'toast-below-nav' },
    didOpen: (toast) => { toast.style.marginTop = '60px'; toast.addEventListener('mouseenter', Swal.stopTimer); toast.addEventListener('mouseleave', Swal.resumeTimer); }
});

function toastOk(msg) { Toast.fire({ icon: 'success', title: msg }); }
function toastErr(msg) {
    Swal.mixin({
        toast: true, position: 'top-end', showConfirmButton: false, timer: 2000,
        timerProgressBar: true, background: '#D32F2F', color: '#fff',
        didOpen: (toast) => { toast.style.marginTop = '60px'; }
    }).fire({ icon: 'info', title: msg });
}

// ==========================================
// 9. ANIMACIÓN SCROLL (CONÓCENOS)
// ==========================================
// Variables globales de la animación
const TOTAL_FRAMES = 240; // Ajustado exactamente a la cantidad extraída por ffmpeg
const NATIVE_W = 1280; // Resolución Nativa original para máxima calidad
const NATIVE_H = 720;
const FRAMES_DIR = './frames/';
const pad = n => String(n).padStart(4, '0');

let dpr, vpW, vpH;
let sectionTop = 0, scrollRange = 0;
let currentIdx = -1;
const frames = new Array(TOTAL_FRAMES);
let loadedCount = 0;
let animSection, animCanvas, animCtx, animHint;
let isAnimInitialized = false;

function initScrollAnimation() {
    animSection = document.getElementById('scroll-section');
    animCanvas = document.getElementById('frame-canvas');
    if(!animCanvas) return;
    animCtx = animCanvas.getContext('2d', { alpha: false });
    animHint = document.getElementById('scroll-hint');

    sizeCanvas();
    preloadAnimFrames().then(() => {
        updateAnimMetrics(); 
        currentIdx = -1; 
        drawAnimFrame(0);
        window.addEventListener('scroll', onAnimScroll, { passive: true });
    });
    
    window.addEventListener('resize', () => {
        if (document.getElementById("view-about").classList.contains("hidden")) return;
        sizeCanvas(); 
        updateAnimMetrics();
        const saved = currentIdx < 0 ? 0 : currentIdx;
        currentIdx = -1; 
        drawAnimFrame(saved);
    });
    isAnimInitialized = true;
}

function sizeCanvas() {
    if(!animCanvas || !animSection) return;
    dpr = window.devicePixelRatio || 1;
    const stage = document.getElementById('sticky-stage');
    vpW = stage.clientWidth;
    vpH = stage.clientHeight;
    animCanvas.style.width = vpW + 'px';
    animCanvas.style.height = vpH + 'px';
    animCanvas.width = Math.round(vpW * dpr);
    animCanvas.height = Math.round(vpH * dpr);
    animCtx.scale(dpr, dpr);
}

function drawAnimCover(img) {
    if (!img || !img.naturalWidth) {
        // Transparent fallback instead of a dark box
        animCtx.clearRect(0, 0, vpW, vpH);
        return;
    }
    const imgAspect = NATIVE_W / NATIVE_H;
    const canvasAspect = vpW / vpH;
    let srcX, srcY, srcW, srcH;
    if (canvasAspect > imgAspect) {
        srcW = NATIVE_W; 
        srcH = NATIVE_W / canvasAspect;
        srcX = 0; 
        srcY = (NATIVE_H - srcH) / 2;
    } else {
        srcH = NATIVE_H; 
        srcW = NATIVE_H * canvasAspect;
        srcY = 0; 
        srcX = (NATIVE_W - srcW) / 2;
    }
    animCtx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, vpW, vpH);
}

function updateAnimMetrics() {
    if(!animSection) return;
    sectionTop = animSection.offsetTop;
    scrollRange = animSection.offsetHeight - window.innerHeight;
    if(scrollRange < 0) scrollRange = 0;
}

function preloadAnimFrames() {
    return new Promise(resolve => {
        // Timeout de seguridad más largo para evitar trabar la inicialización
        let resolveFired = false;
        setTimeout(() => { if(!resolveFired) { resolveFired=true; resolve(); } }, 5000); 

        for (let i = 0; i < TOTAL_FRAMES; i++) {
            const img = new Image();
            img.onload = img.onerror = () => {
                loadedCount++;
                
                // Forzar el dibujado del primer frame apenas cargue para evitar pantalla negra
                if (i === 0 && currentIdx <= 0 && isAnimInitialized) {
                    drawAnimFrame(0);
                }

                if (loadedCount === TOTAL_FRAMES && !resolveFired) {
                    resolveFired = true;
                    resolve();
                }
            };
            img.src = FRAMES_DIR + 'frame_' + pad(i + 1) + '.jpg';
            frames[i] = img;
        }
    });
}

function drawAnimFrame(idx) {
    if (idx === currentIdx) return;
    currentIdx = idx;
    drawAnimCover(frames[idx]);
}

let animRafPending = false;
function onAnimScroll() {
    // Si la vista está oculta, no hacer nada para optimizar rendimiento
    if (document.getElementById("view-about").classList.contains("hidden")) return;

    const scrolled = window.scrollY - sectionTop;
    let progress = 0;
    if(scrollRange > 0) progress = Math.max(0, Math.min(1, scrolled / scrollRange));
    
    let nextIdx = Math.min(TOTAL_FRAMES - 1, Math.floor(progress * TOTAL_FRAMES));
    if(isNaN(nextIdx) || nextIdx < 0) nextIdx = 0;

    if (scrolled > 20 && animHint) animHint.classList.add('gone');
    else if (scrolled <= 20 && animHint) animHint.classList.remove('gone');

    if (!animRafPending) {
        animRafPending = true;
        requestAnimationFrame(() => { 
            drawAnimFrame(nextIdx); 
            animRafPending = false; 
        });
    }
}

// Hook expuesto globalmente para que el Router SPA lo ejecute al entrar a la vista
window.recalcularAnimacionTaco = function() {
    if(!isAnimInitialized) {
        initScrollAnimation();
    } else {
        setTimeout(() => {
            sizeCanvas();
            updateAnimMetrics();
            drawAnimFrame(currentIdx < 0 ? 0 : currentIdx);
        }, 150); // Timeout leve para permitir que CSS rinda el display primero
    }
};
