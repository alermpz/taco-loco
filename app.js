// ==========================================
// CONFIGURACIÓN DE URLS (Google Sheets)
// ==========================================
const URL_CSV_MENU = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=357751603&single=true&output=csv";
const URL_CSV_RESENAS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=764839671&single=true&output=csv";
const URL_APPS_SCRIPT_RESENAS = "https://script.google.com/macros/s/AKfycbxCGiDEUAAvVXv4cfm05ajiVKotnCYgeQv8wmePsQoM_GgkCp8poM7iSCGGj5TEbIm4/exec";
const URL_APPS_SCRIPT_PEDIDOS = "https://script.google.com/macros/s/AKfycbyHzbARjCcog41iCwBvCvA4aburgAlGGHSA5EEQuGP64CQe36-j-piizwITeysVVA5u/exec";
const WHATSAPP_NUMBER = "529681171392";

// ==========================================
// ESTADO GLOBAL DE LA APP (Memoria)
// ==========================================
const state = {
    carrito: {},      // { "Taco de Res": { precio: 15, cant: 2 }, ... }
    menu: { tacos: [], bebidas: [] },
    resenas: [],
    tiendaAbierta: true // En el futuro se podría leer de otro CSV si se desea
};

// ==========================================
// 1. INICIALIZACIÓN DE LA SPA
// ==========================================
document.addEventListener("DOMContentLoaded", async () => {
    // Escuchar cambios de slider de reseñas en tiempo real
    document.getElementById("rev-stars").addEventListener("input", (e) => {
        document.getElementById("star-display").textContent = "⭐".repeat(e.target.value);
    });

    // Cargar datos asíncronos y mostrar vista principal
    await cargarMenu();
    await cargarResenas();

    document.getElementById("loader").classList.add("hidden");
    document.getElementById("view-menu").classList.remove("hidden");
    document.getElementById("main-footer").classList.remove("hidden");

    // Iniciar el enrutador
    initRouter();
    // Iniciar eventos del Carrito
    initCartEvents();
});

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

            // Scroll hacia arriba
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    });
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

// ==========================================
// 4. RENDERIZADO DEL MENÚ Y RESEÑAS
// ==========================================
function renderizarMenu() {
    const contenedorTacos = document.getElementById("tacos-container");
    const contenedorBebidas = document.getElementById("bebidas-container");

    let htmlTacos = "";
    state.menu.tacos.forEach((taco) => {
        const cleanName = taco.nombre.replace(/'/g, "\\'");
        htmlTacos += `
        <div class="product-card">
            <div>
                <img src="${taco.img}" onerror="this.src=''" alt="${taco.nombre}" loading="lazy">
                <h3 class="product-title">${taco.nombre}</h3>
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
                <img src="${bebida.img}" onerror="this.src=''" alt="${bebida.nombre}" loading="lazy">
                <h3 class="product-title">${bebida.nombre}</h3>
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
    const item = [...state.menu.tacos, ...state.menu.bebidas].find(i => i.nombre === nombreItem);
    if (!item) return;

    if (state.carrito[item.nombre]) {
        state.carrito[item.nombre].cant++;
    } else {
        state.carrito[item.nombre] = { precio: item.precio, cant: 1 };
    }
    toastOk(`¡1 ${item.nombre} agregado!`);
    actualizarCarritoHUD();
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

    for (let n in state.carrito) {
        const curr = state.carrito[n];
        html += `
        <div class="cart-item-row">
            <div class="cart-item-info">
                <p class="cart-item-name">${n}</p>
                <p class="cart-item-price">$${curr.precio} x ${curr.cant} = $${curr.precio * curr.cant}</p>
            </div>
            <div class="cart-item-qty">
                <button class="clr-red" onclick="quitarDelCarrito('${n}')">－</button>
                <span>${curr.cant}</span>
                <button class="clr-primary" onclick="agregarAlCarrito('${curr.fullItem}')">＋</button>
            </div>
        </div>
        `;
    }
    list.innerHTML = html;
}

// ==========================================
// 6. FLUJO DE PEDIDO, WHATSAPP Y EXCEL
// ==========================================
function evConfirmOrder() {
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
    toast: true, position: 'top', showConfirmButton: false, timer: 2000,
    timerProgressBar: true, background: '#FF6B00', color: '#fff',
    didOpen: (toast) => { toast.addEventListener('mouseenter', Swal.stopTimer); toast.addEventListener('mouseleave', Swal.resumeTimer); }
});

function toastOk(msg) { Toast.fire({ icon: 'success', title: msg }); }
function toastErr(msg) {
    Swal.mixin({
        toast: true, position: 'top', showConfirmButton: false, timer: 2000,
        timerProgressBar: true, background: '#D32F2F', color: '#fff'
    }).fire({ icon: 'info', title: msg });
}
