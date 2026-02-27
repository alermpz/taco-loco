import streamlit as st
import urllib.parse
import pandas as pd
import base64 
import requests 
import threading 
import re
import altair as alt

# ==========================================
# 1. CONFIGURACIÓN INICIAL DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="EL TACO LOCO", page_icon="🌮", layout="wide")

# ==========================================
# 2. VARIABLES DE ESTADO Y MEMORIA (SESSION)
# ==========================================
if 'carrito' not in st.session_state:
    st.session_state.carrito = {}

if 'fase_pedido' not in st.session_state:
    st.session_state.fase_pedido = 1

# Variables del Perfil Administrador
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if 'tienda_abierta' not in st.session_state:
    st.session_state.tienda_abierta = True

# Memoria de inventario (Guarda los nombres de los platillos agotados)
if 'agotados' not in st.session_state:
    st.session_state.agotados = []

# URL del CSV de Reseñas (pestaña "Reseñas" publicada en tu Google Sheets)
URL_CSV_RESENAS = "https://script.google.com/macros/s/AKfycbxCGiDEUAAvVXv4cfm05ajiVKotnCYgeQv8wmePsQoM_GgkCp8poM7iSCGGj5TEbIm4/exec"

# Memoria de reseñas de clientes (se recarga desde Sheets)
if 'resenas' not in st.session_state:
    st.session_state.resenas = []
# URL del Apps Script para guardar reseñas
URL_APPS_SCRIPT_RESENAS = "https://script.google.com/macros/s/AKfycbxCGiDEUAAvVXv4cfm05ajiVKotnCYgeQv8wmePsQoM_GgkCp8poM7iSCGGj5TEbIm4/exec"


# ==========================================
# 3. FUNCIONES PRINCIPALES DEL SISTEMA
# ==========================================
def agregar_al_carrito(producto, tipo):
    if producto in st.session_state.carrito:
        st.session_state.carrito[producto] += 1
    else:
        st.session_state.carrito[producto] = 1
    
    icono = "🌮" if tipo == "taco" else "🥤"
    st.toast(f"¡1 {producto} agregado!", icon=icono)

def quitar_del_carrito(producto):
    if producto in st.session_state.carrito:
        st.session_state.carrito[producto] -= 1
        if st.session_state.carrito[producto] <= 0:
            del st.session_state.carrito[producto] 
        st.toast(f"¡1 {producto} quitado!", icon="➖")

def obtener_total_items():
    return sum(st.session_state.carrito.values())

def enviar_datos_excel(url, datos):
    try:
        requests.post(url, json=datos, timeout=5)
    except:
        pass

def enviar_resena_sheets(url, datos):
    """Envía la reseña al Apps Script (con imagen en base64 si hay)."""
    try:
        requests.post(url, json=datos, timeout=10)
    except:
        pass

@st.cache_data(ttl=30)
def cargar_resenas_sheets(url_csv):
    """Carga reseñas desde Google Sheets publicado como CSV."""
    try:
        df = pd.read_csv(url_csv)
        resenas = []
        for _, row in df.iterrows():
            resenas.append({
                "fecha":       str(row.get("Fecha", "")).strip(),
                "nombre":      str(row.get("Nombre", "")).strip(),
                "estrellas":   int(float(str(row.get("Estrellas", 5)))),
                "comentario":  str(row.get("Comentario", "")).strip(),
                "imagen_url":  str(row.get("ImagenURL", "")).strip(),
            })
        return list(reversed(resenas))   # las más nuevas primero
    except Exception:
        return []

# Cargamos imágenes a la memoria RAM
@st.cache_data
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

logo_base64 = get_img_as_base64("imagenes/logo.png")
bg_base64 = get_img_as_base64("imagenes/fondotacos.png")

# CARGA DE IMÁGENES DEL CARRUSEL Y UBICACIÓN
historia_base64 = get_img_as_base64("imagenes/historia.png")
carrusel_1_base64 = get_img_as_base64("imagenes/carrusel_1.jpg")
carrusel_2_base64 = get_img_as_base64("imagenes/carrusel_2.jpg")
carrusel_3_base64 = get_img_as_base64("imagenes/carrusel_3.jpg")

logo_src = f"data:image/png;base64,{logo_base64}" if logo_base64 else ""
historia_src = f"data:image/png;base64,{historia_base64}" if historia_base64 else logo_src
carr_1_src = f"data:image/jpeg;base64,{carrusel_1_base64}" if carrusel_1_base64 else logo_src
carr_2_src = f"data:image/jpeg;base64,{carrusel_2_base64}" if carrusel_2_base64 else logo_src
carr_3_src = f"data:image/jpeg;base64,{carrusel_3_base64}" if carrusel_3_base64 else logo_src

# ==========================================
# 4. MOTOR VISUAL Y ESTILOS CSS BASE
# ==========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Oswald:wght@700&display=swap" rel="stylesheet">
<style>
:root { --color-naranja: #FF6B00; --color-rojo: #D32F2F; --color-crema: #F4F6F8; --color-texto: #1D1D1F; }
header, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu { display: none !important; visibility: hidden !important; }
div[class*="viewerBadge"], div[class*="stDeployButton"], a[href*="streamlit"], button[kind="header"] { display: none !important; opacity: 0 !important; pointer-events: none !important; z-index: -9999 !important; }
[data-testid="stAppViewBlockContainer"], [data-testid="stVerticalBlock"] { opacity: 1 !important; }
[data-testid="stAppViewContainer"], .stApp { background-color: var(--color-crema) !important; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 200 200'%3E%3Cg stroke='%231D1D1F' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round' opacity='0.06'%3E%3Cpath d='M20,80 C20,50 70,50 70,80 C70,85 20,85 20,80 Z'/%3E%3Cpath d='M25,75 Q45,60 65,75'/%3E%3Cpath d='M30,70 L35,60 M45,72 L47,58 M60,68 L58,58'/%3E%3Cpath d='M150,30 C170,30 180,60 160,80 C140,100 120,70 150,30 Z'/%3E%3Cpath d='M150,30 Q145,20 135,15'/%3E%3Ccircle cx='50' cy='150' r='20'/%3E%3Ccircle cx='50' cy='150' r='15'/%3E%3Cline x1='50' y1='135' x2='50' y2='165'/%3E%3Cline x1='35' y1='150' x2='65' y2='150'/%3E%3Cline x1='39' y1='139' x2='61' y2='161'/%3E%3Cline x1='39' y1='161' x2='61' y2='139'/%3E%3Cpath d='M140,150 C120,150 120,180 140,180 C160,180 160,150 140,150 Z'/%3E%3Ccircle cx='140' cy='168' r='8'/%3E%3Cpolygon points='90,100 110,60 130,100'/%3E%3Cpath d='M100,75 L102,77 M115,90 L117,92'/%3E%3Cpath d='M90,20 L95,25 M95,20 L90,25'/%3E%3Cpath d='M20,120 L25,125 M25,120 L20,125'/%3E%3Cpath d='M180,130 A5,5 0 0,1 190,130 A5,5 0 0,1 180,130'/%3E%3C/g%3E%3C/svg%3E") !important; background-size: 400px 400px; font-family: 'Inter', sans-serif !important; }
.stApp { margin-top: -50px; }
h1, h2, h3, h4, p, div, span, label, li { color: var(--color-texto) !important; font-family: 'Inter', sans-serif; }
div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea { background-color: white !important; color: #1D1D1F !important; border: 2px solid #E0E0E0 !important; border-radius: 12px; padding: 12px; font-weight: 500; }
div[data-baseweb="input"] input:focus, div[data-baseweb="textarea"] textarea:focus { border: 2px solid var(--color-naranja) !important; }
div[data-baseweb="input"] input::placeholder, div[data-baseweb="textarea"] textarea::placeholder { color: #888888 !important; font-weight: 400; }
div[role="dialog"] { background: linear-gradient(135deg, var(--color-naranja), var(--color-rojo)) !important; border: 2px solid white; border-radius: 24px !important; }
div[role="dialog"] h1, div[role="dialog"] h2, div[role="dialog"] h3, div[role="dialog"] p, div[role="dialog"] span, div[role="dialog"] label { color: white !important; }
div[role="dialog"] div[data-baseweb="select"] > div { background-color: white !important; border: 2px solid transparent !important; border-radius: 12px; }
div[role="dialog"] div[data-baseweb="select"] span { color: #1D1D1F !important; font-weight: 600; }
div[data-baseweb="popover"] div { background-color: white !important; color: #FF6B00 !important; font-weight: 700; }
div[data-baseweb="toast"] { background-color: var(--color-naranja) !important; border: 2px solid white; border-radius: 12px; }
div[data-baseweb="toast"] div { color: white !important; font-weight: 700; }
[data-testid="stExpander"] { background-color: transparent !important; border-radius: 10px; border: 1px solid rgba(0,0,0,0.08) !important; box-shadow: none !important; }
[data-testid="stExpander"] details summary { color: rgba(100,100,100,0.4) !important; font-weight: normal; }
[data-testid="stExpander"] details summary p { color: rgba(100,100,100,0.4) !important; font-family: 'Inter', sans-serif; font-size: 0.85rem; letter-spacing: 0px; }
[data-testid="stExpander"] details summary svg { fill: rgba(100,100,100,0.3) !important; }
.header-container { background-color: #1A1A1A; padding: 4.5rem 2rem; border-radius: 0 0 30px 30px; text-align: center; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.15); position: relative; border-bottom: 5px solid var(--color-naranja); }
.logo-esquina { display: block; margin: 0 auto 15px auto; width: 110px; border-radius: 50%; border: 4px solid white; box-shadow: 0 4px 20px rgba(0,0,0,0.4); }
.header-frase-peque { color: var(--color-naranja) !important; font-weight: 900; font-size: 1.2rem; margin: 0; letter-spacing: 4px; text-transform: uppercase; text-shadow: 1px 1px 5px rgba(0,0,0,0.5); }
.header-frase-grande { color: white !important; font-family: 'Oswald', sans-serif !important; font-weight: 700; font-size: 4.5rem; line-height: 1.1; margin: 5px 0 0 0; text-shadow: 3px 3px 15px rgba(0,0,0,0.7); text-transform: uppercase; }
.stButton>button, [data-testid="stFormSubmitButton"]>button { background: linear-gradient(45deg, var(--color-naranja), var(--color-rojo)) !important; color: white !important; border: none; border-radius: 25px; font-weight: 700; font-size: 1rem; padding: 10px 0; transition: all 0.2s ease; }
.stButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(255, 107, 0, 0.4); }
.stButton>button:active, [data-testid="stFormSubmitButton"]>button:active { transform: scale(0.95); }
div[data-testid="column"] button[kind="primary"] { background: white !important; color: var(--color-rojo) !important; border: 2px solid var(--color-rojo) !important; }
div[data-testid="column"] button[kind="primary"]:hover { box-shadow: 0 8px 15px rgba(211, 47, 47, 0.2); transform: translateY(-2px); }
.stTabs [data-baseweb="tab-list"] { background-color: transparent; padding: 5px; gap: 10px; }
.stTabs [data-baseweb="tab"] { background-color: white !important; color: #888888 !important; font-weight: 600; border-radius: 20px; padding: 10px 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.stTabs [aria-selected="true"] { background-color: var(--color-naranja) !important; color: white !important; box-shadow: 0 5px 15px rgba(255, 107, 0, 0.3); }
[data-testid="column"] { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(5px); padding: 20px; border-radius: 20px; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.03); }
.precio-tag { color: var(--color-naranja) !important; font-weight: 900; font-size: 1.6rem; display: block; margin-bottom: 15px; }
.nombre-prod { font-size: 1.3rem; font-weight: 800; color: #1D1D1F !important; margin-top: 10px; }
.desc-prod { font-size: 0.95rem; color: #888888 !important; margin-bottom: 15px; line-height: 1.4; font-weight: 500;}
.ubicacion-box { background-color: rgba(255, 255, 255, 0.9); padding: 25px; border-radius: 20px; border-left: 5px solid var(--color-naranja); margin-top: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
[data-testid="stImage"] img { transition: transform 0.4s ease; border-radius: 12px; }
[data-testid="stImage"] img:hover { transform: scale(1.04); }
.contador-item { text-align: center; font-weight: 900; font-size: 1.4rem; color: var(--color-texto); margin-top: 5px; }
.about-hero { text-align: center; margin-bottom: 40px; margin-top: 10px;}
.about-hero h2 { font-family: 'Oswald', sans-serif !important; font-size: 3rem; color: var(--color-naranja) !important; line-height: 1.1; letter-spacing: -1px; margin-bottom: 5px; }
.about-hero p { font-size: 1.2rem; color: var(--color-texto) !important; font-weight: 700; opacity: 0.8; text-transform: uppercase; letter-spacing: 2px; }
.about-grid { display: flex; flex-wrap: wrap; gap: 40px; align-items: center; margin-bottom: 50px; }
.about-text-box { flex: 1; min-width: 300px; padding: 10px; }
.about-text-box p { font-size: 1.1rem; line-height: 1.7; color: #1D1D1F !important; text-align: justify; margin-bottom: 15px; font-weight: 500; }
.carousel-wrapper { flex: 1; min-width: 300px; height: 400px; position: relative; border-radius: 20px; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.15); border: 4px solid white; background-color: #f4f4f4; }
.img-carrusel { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; border-radius: 16px; transition: transform 0.5s ease; }
.img-1 { z-index: 1; opacity: 1; animation: fade1 16s infinite; }
.img-2 { z-index: 2; opacity: 0; animation: fade2 16s infinite; }
.img-3 { z-index: 3; opacity: 0; animation: fade3 16s infinite; }
.img-4 { z-index: 4; opacity: 0; animation: fade4 16s infinite; }
@keyframes fade1 { 0%, 20% { opacity: 1; } 25%, 95% { opacity: 0; } 100% { opacity: 1; } }
@keyframes fade2 { 0%, 20% { opacity: 0; } 25%, 45% { opacity: 1; } 50%, 100% { opacity: 0; } }
@keyframes fade3 { 0%, 45% { opacity: 0; } 50%, 70% { opacity: 1; } 75%, 100% { opacity: 0; } }
@keyframes fade4 { 0%, 70% { opacity: 0; } 75%, 95% { opacity: 1; } 100% { opacity: 0; } }
.carousel-wrapper:hover .img-carrusel { transform: scale(1.05); }
.valores-title { text-align: center; font-family: 'Oswald', sans-serif !important; color: var(--color-rojo) !important; font-size: 2.2rem; margin-bottom: 30px; text-transform: uppercase; }
.valores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
.valor-item { background: white; padding: 25px 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border-left: 5px solid var(--color-naranja); display: flex; align-items: flex-start; gap: 18px; transition: transform 0.2s ease; }
.valor-item:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
.valor-icon svg { width: 32px; height: 32px; fill: var(--color-naranja); flex-shrink: 0; }
div[data-testid="stAppViewContainer"] .valor-text h4 { margin: 0 0 8px 0; color: #1D1D1F !important; font-family: 'Oswald', sans-serif !important; font-size: 1.35rem; letter-spacing: 0.5px; text-transform: uppercase; }
div[data-testid="stAppViewContainer"] .valor-text p { margin: 0; color: #666 !important; font-size: 0.95rem; line-height: 1.4; }
.footer-container { background-color: #1A1A1A; padding: 4rem 2rem; text-align: center; border-radius: 30px 30px 0 0; margin-top: 5rem; box-shadow: 0 -10px 30px rgba(0,0,0,0.15); border-top: 5px solid var(--color-naranja); }
.footer-container, .footer-container h3, .footer-container p, .footer-container span, .footer-container div { color: #FFFFFF !important; }
.footer-container h3 { font-family: 'Oswald', sans-serif !important; font-size: 2.5rem; letter-spacing: 1px; text-shadow: 2px 2px 10px rgba(0,0,0,0.8); }
.social-link svg { transition: transform 0.3s ease, fill 0.3s ease; fill: var(--color-naranja); margin: 0 15px; }
.social-link:hover svg { fill: white !important; transform: scale(1.2); }
.texto-creditos { color: #CCCCCC !important; font-size: 0.85rem !important; margin-top: 40px !important; letter-spacing: 1px; text-transform: uppercase; font-weight: 600; text-shadow: 1px 1px 5px rgba(0,0,0,0.8); }
.resena-card { background: white; border-radius: 18px; padding: 22px 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.06); border-left: 5px solid var(--color-naranja); margin-bottom: 15px; transition: transform 0.2s ease; }
.resena-card:hover { transform: translateY(-3px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
.resena-stars { color: #FF6B00; font-size: 1.3rem; margin-bottom: 6px; }
.resena-texto { color: #1D1D1F !important; font-size: 1rem; line-height: 1.6; margin-bottom: 10px; font-weight: 500; font-style: italic; }
.resena-autor { color: #888 !important; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
.resena-header { text-align: center; margin-bottom: 35px; margin-top: 10px; }
.resena-header h2 { font-family: 'Oswald', sans-serif !important; font-size: 2.8rem; color: var(--color-naranja) !important; line-height: 1.1; margin-bottom: 5px; }
.resena-header p { font-size: 1rem; color: var(--color-texto) !important; font-weight: 600; opacity: 0.7; text-transform: uppercase; letter-spacing: 2px; }
.promedio-box { background: linear-gradient(135deg, var(--color-naranja), var(--color-rojo)); border-radius: 20px; padding: 25px; text-align: center; margin-bottom: 30px; color: white !important; }
.promedio-numero { font-family: 'Oswald', sans-serif; font-size: 4rem; color: white !important; line-height: 1; margin: 0; }
.promedio-stars { font-size: 1.8rem; margin: 5px 0; }
.promedio-label { font-size: 0.9rem; color: rgba(255,255,255,0.85) !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# INYECCIÓN DINÁMICA DE LA IMAGEN DE FONDO
if bg_base64:
    st.markdown(f"""
<style>
.header-container {{ background: linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.85)), url('data:image/png;base64,{bg_base64}') center/cover no-repeat !important; }}
.footer-container {{ background: linear-gradient(to top, rgba(0,0,0,0.9), rgba(0,0,0,0.6)), url('data:image/png;base64,{bg_base64}') center/cover no-repeat !important; }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 5. BASE DE DATOS DEL MENÚ (GOOGLE SHEETS)
# ==========================================
@st.cache_data(ttl=15) 
def cargar_menu(url_csv):
    try:
        df = pd.read_csv(url_csv)
        tacos, bebidas = {}, {}
        for _, row in df.iterrows():
            categoria = str(row["Categoria"]).strip().lower()
            nombre = str(row["Nombre"]).strip()
            item = {
                "precio": float(row["Precio"]),
                "img": str(row["Imagen"]).strip(),
                "desc": str(row["Descripcion"]).strip() if pd.notna(row["Descripcion"]) else ""
            }
            if categoria == "taco": tacos[nombre] = item
            elif categoria == "bebida": bebidas[nombre] = item
        return tacos, bebidas
    except Exception:
        return {}, {}

URL_CSV_MENU = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=357751603&single=true&output=csv" 
menu_tacos, menu_bebidas = cargar_menu(URL_CSV_MENU)
menu_completo = {**menu_tacos, **menu_bebidas}

if not menu_tacos and not menu_bebidas:
    st.error("⚠️ No se pudo cargar el menú. Revisa tu Excel.")

# ==========================================
# 6. LOGICA DEL MODAL DE PEDIDOS (CARRITO)
# ==========================================
@st.dialog("Tu Pedido")
def mostrar_carrito_modal():
    if st.session_state.fase_pedido == 1:
        if not st.session_state.carrito:
            st.info("Tu carrito está vacío.")
            return
            
        vista_fase1 = st.empty()
        with vista_fase1.container():
            total_venta = 0
            texto_pedido = ""
            texto_para_excel = ""
            for item, cant in st.session_state.carrito.items():
                if item not in menu_completo: continue 
                precio_u = menu_completo[item]["precio"]
                subtotal = cant * precio_u
                total_venta += subtotal
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.markdown(f"**{item}**")
                c2.markdown(f"x{cant}")
                c3.markdown(f"${subtotal}")
                texto_pedido += f"• {cant}x {item} (${subtotal})\n"
                texto_para_excel += f"{cant}x {item}, "
            
            st.divider()
            st.markdown(f"<h3 style='text-align: right; color: white !important;'>Total: ${total_venta}</h3>", unsafe_allow_html=True)
            
            with st.form("form_pedido", border=False):
                st.markdown("#### Datos de envío")
                nombre = st.text_input("Nombre:")
                direccion = st.text_area("Dirección exacta:")
                ref = st.text_input("Referencia de la casa:")
                notas = st.text_area("Instrucciones especiales (Opcional):", placeholder="Ej. Sin cebolla, salsas aparte...")
                pago = st.selectbox("Forma de Pago:", ["Efectivo 💵", "Transferencia 📱"])
                confirmar = st.form_submit_button("Hacer Pedido", type="secondary", use_container_width=True)
            
            if st.button("Vaciar Carrito", use_container_width=True):
                st.session_state.carrito = {}
                st.rerun()

        if confirmar:
            if nombre and direccion:
                msg_notas = f"\n📝 *Notas:* {notas}\n" if notas else "\n"
                msg_final = f"Hola Taco Loco 🌮, soy *{nombre}*.\n\n*MI PEDIDO:*\n{texto_pedido}{msg_notas}\n💰 *Total: ${total_venta}*\n📍 *Dir:* {direccion}\n🏠 *Ref:* {ref}\n💸 *Pago:* {pago}"
                url_google_guardar = "https://script.google.com/macros/s/AKfycbyHzbARjCcog41iCwBvCvA4aburgAlGGHSA5EEQuGP64CQe36-j-piizwITeysVVA5u/exec" 
                texto_excel_con_notas = texto_para_excel
                if notas: texto_excel_con_notas += f" | NOTAS: {notas}"
                datos_excel = {"cliente": nombre, "direccion": f"{direccion} ({ref})", "pedido": texto_excel_con_notas, "total": total_venta, "pago": pago}
                
                threading.Thread(target=enviar_datos_excel, args=(url_google_guardar, datos_excel)).start()
                msg_encoded = urllib.parse.quote(msg_final.encode('utf-8'))
                st.session_state.whatsapp_url = f"https://api.whatsapp.com/send?phone=529681171392&text={msg_encoded}"
                st.session_state.fase_pedido = 2
                vista_fase1.empty()
                st.markdown("<div style='background-color: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; border: 2px solid white; text-align: center; margin-bottom: 20px;'><h2>¡Pedido registrado!</h2><p style='font-size: 1.1rem;'>Toca el botón para enviarnos tu pedido por WhatsApp y prepararlo rápido.</p></div>", unsafe_allow_html=True)
                st.link_button("Enviar WhatsApp ahora", st.session_state.whatsapp_url, type="secondary", use_container_width=True)
                if st.button("Terminar y limpiar", use_container_width=True):
                    st.session_state.carrito = {}
                    st.session_state.fase_pedido = 1
                    st.rerun()
            else:
                st.error("⚠️ Completa tu nombre y dirección por favor.")

    elif st.session_state.fase_pedido == 2:
        st.markdown("<div style='background-color: rgba(255,255,255,0.2); padding: 20px; border-radius: 15px; border: 2px solid white; text-align: center; margin-bottom: 20px;'><h2>¡Pedido registrado!</h2><p style='font-size: 1.1rem;'>Toca el botón para enviarnos tu pedido por WhatsApp y prepararlo rápido.</p></div>", unsafe_allow_html=True)
        st.link_button("Enviar WhatsApp ahora", st.session_state.whatsapp_url, type="secondary", use_container_width=True)
        if st.button("Terminar y limpiar", use_container_width=True):
            st.session_state.carrito = {}
            st.session_state.fase_pedido = 1
            st.rerun()

# ==========================================
# 7. ESTRUCTURA VISUAL DE LA PÁGINA (UI)
# ==========================================
logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="logo-esquina">' if logo_base64 else ''
st.markdown(f"""
<div class="header-container">
{logo_html}
<p class="header-frase-peque">¿CON HAMBRE?</p>
<p class="header-frase-grande">REVISA NUESTRO MENÚ</p>
</div>
""", unsafe_allow_html=True)

# --- BANNER DE TIENDA CERRADA ---
if not st.session_state.tienda_abierta:
    st.markdown("""
    <div style='background: linear-gradient(135deg, var(--color-rojo), #9A0000); color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 2px solid white; box-shadow: 0 5px 15px rgba(211,47,47,0.4);'>
        <h2 style='color: white !important; margin: 0; font-family: Oswald, sans-serif; letter-spacing: 1px;'>⚠️ ¡ESTAMOS A REVENTAR! 🌮</h2>
        <p style='margin: 10px 0 0 0; font-size: 1.1rem; font-weight: 500;'>Hemos pausado los pedidos en línea por un momento para darte el mejor servicio. Vuelve a intentar en unos minutos.</p>
    </div>
    """, unsafe_allow_html=True)

col_titulo, col_carrito = st.columns([7, 2])
with col_titulo:
    st.subheader("🔥 Menú del Día")

with col_carrito:
    total_items = obtener_total_items()
    label_btn = "🛒 Ver Pedido"
    tipo_btn = "secondary"
    if total_items > 0:
        label_btn = f"🛒 Ver Pedido ({total_items})"
        tipo_btn = "primary"
        
    if st.session_state.tienda_abierta:
        if st.button(label_btn, type=tipo_btn, use_container_width=True):
            st.session_state.fase_pedido = 1 
            mostrar_carrito_modal()
    else:
        st.button("🚫 Pedidos Pausados", disabled=True, use_container_width=True)

tabs = st.tabs(["Tacos", "Bebidas", "Ubicación", "Conócenos", "⭐ Reseñas"])

with tabs[0]:
    if not menu_tacos:
        st.info("Aún no hay tacos en el menú. ¡Agrega algunos en tu Excel!")
    else:
        cols = st.columns(2)
        for i, (nombre, info) in enumerate(menu_tacos.items()):
            with cols[i % 2]:
                try: st.image(info["img"], use_container_width=True)
                except: st.error("Sin imagen")
                st.markdown(f"<div class='nombre-prod'>{nombre}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='desc-prod'>{info['desc']}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='precio-tag'>${int(info['precio'])}</span>", unsafe_allow_html=True)
                
                if not st.session_state.tienda_abierta:
                    st.button("⏸️ Pausado", key=f"pause_t_{i}", disabled=True, use_container_width=True)
                elif nombre in st.session_state.agotados:
                    st.button("🚫 Agotado", key=f"agotado_t_{i}", disabled=True, use_container_width=True)
                else:
                    cantidad_actual = st.session_state.carrito.get(nombre, 0)
                    if cantidad_actual > 0:
                        col_min, col_num, col_plus = st.columns([1, 1.2, 1])
                        with col_min: st.button("－", key=f"min_t_{i}", on_click=quitar_del_carrito, args=(nombre,), use_container_width=True)
                        with col_num: st.markdown(f"<div class='contador-item'>{cantidad_actual}</div>", unsafe_allow_html=True)
                        with col_plus: st.button("＋", key=f"plus_t_{i}", on_click=agregar_al_carrito, args=(nombre, "taco"), use_container_width=True)
                    else:
                        st.button("Agregar al pedido", key=f"add_t_{i}", on_click=agregar_al_carrito, args=(nombre, "taco"), use_container_width=True)

with tabs[1]:
    if not menu_bebidas:
        st.info("Aún no hay bebidas en el menú. ¡Agrega algunas en tu Excel!")
    else:
        cols_b = st.columns(3)
        for i, (nombre, info) in enumerate(menu_bebidas.items()):
            with cols_b[i % 3]:
                try: st.image(info["img"], use_container_width=True)
                except: st.info("Sin imagen")
                st.markdown(f"<div class='nombre-prod'>{nombre}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='precio-tag'>${int(info['precio'])}</span>", unsafe_allow_html=True)
                
                if not st.session_state.tienda_abierta:
                    st.button("⏸️ Pausado", key=f"pause_b_{i}", disabled=True, use_container_width=True)
                elif nombre in st.session_state.agotados:
                    st.button("🚫 Agotado", key=f"agotado_b_{i}", disabled=True, use_container_width=True)
                else:
                    cantidad_actual = st.session_state.carrito.get(nombre, 0)
                    if cantidad_actual > 0:
                        col_min, col_num, col_plus = st.columns([1, 1.2, 1])
                        with col_min: st.button("－", key=f"min_b_{i}", on_click=quitar_del_carrito, args=(nombre,), use_container_width=True)
                        with col_num: st.markdown(f"<div class='contador-item'>{cantidad_actual}</div>", unsafe_allow_html=True)
                        with col_plus: st.button("＋", key=f"plus_b_{i}", on_click=agregar_al_carrito, args=(nombre, "bebida"), use_container_width=True)
                    else:
                        st.button("Agregar al pedido", key=f"add_b_{i}", on_click=agregar_al_carrito, args=(nombre, "bebida"), use_container_width=True)

with tabs[2]:
    st.markdown("### Encuéntranos")
    mapa_html = """<iframe src="https://www.google.com/maps?q=16.753554732500405,-93.37373160552643&hl=es&z=16&output=embed" width="100%" height="350" style="border:0; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);" allowfullscreen="" loading="lazy"></iframe>"""
    st.markdown(mapa_html, unsafe_allow_html=True)
    st.markdown("<div class='ubicacion-box'><h4 style='color: #FF6B00 !important; margin-top: 0;'>📍 Dirección</h4><p><strong>El Taco Loco</strong><br>Ocozocoautla de Espinosa, Chiapas.</p><h4 style='color: #FF6B00 !important; margin-top: 15px;'>🕒 Horario</h4><p>Lunes a Domingo: <strong>6:00 PM - 12:00 AM</strong></p></div>", unsafe_allow_html=True)
    st.markdown("#### Conoce nuestro local:")
    try: st.image("imagenes/local_nuevo.jpg", caption="¡Te esperamos con los mejores tacos!", use_container_width=True)
    except: st.info("Guarda la foto del carrito de frente como 'local_nuevo.jpg' en la carpeta 'imagenes'.")

with tabs[3]:
    st.markdown(f"""
<div class="about-hero">
<h2>EL TACO LOCO: 20 AÑOS DE TRADICIÓN</h2>
<p>Una empresa 100% familiar hecha en Ocozocoautla</p>
</div>
<div class="about-grid">
<div class="about-text-box">
<p>Nuestra historia comenzó en noviembre de 2005, no como un gran plan de negocios, sino por el inmenso amor de una madre. Ante la necesidad económica y el deseo de sacar adelante a su familia, <strong>Ana Lleli García Espinosa</strong> tomó la valiente decisión de empezar a vender tacos.</p>
<p>Lo que hoy es un legado, empezó con un esfuerzo enorme. Trabajando de viernes a domingo, Ana Lleli cocinaba los tres sabores que hoy son nuestra insignia —res, puerco y tripa— y salía de manera arriesgada a ofrecerlos de casa en casa, esperando que los vecinos confiaran en su sazón.</p>
<p>El trabajo duro rindió frutos. Ese esfuerzo a pie se convirtió en el capital suficiente para comprar una caseta, nuestro primer local oficial. Con el tiempo y el éxito de esa receta inigualable, su esposo, <strong>Bolivar Montones Lizarde</strong>, se sumó al proyecto, logrando abrir una segunda caseta.</p>
<p>Hoy, a casi dos décadas de que Ana Lleli diera el primer paso, la tradición se fortalece con la llegada de la nueva generación: su hijo <strong>Jonathan Montanes</strong>. En El Taco Loco seguimos siendo ese mismo negocio familiar, manteniendo intacto el sabor de los tres tacos que lo iniciaron todo y demostrando que el trabajo hecho con cariño siempre prospera.</p>
</div>
<div class="carousel-wrapper">
<img src="{historia_src}" class="img-carrusel img-1" alt="Historia del Taco Loco">
<img src="{carr_1_src}" class="img-carrusel img-2" alt="Preparación">
<img src="{carr_2_src}" class="img-carrusel img-3" alt="Tacos">
<img src="{carr_3_src}" class="img-carrusel img-4" alt="Local interior">
</div>
</div>
<div style="display: flex; flex-wrap: wrap; gap: 30px; background-color: #FFFFFF !important; padding: 40px; border-radius: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border-top: 5px solid #FF6B00; border-bottom: 5px solid #FF6B00; margin-bottom: 50px;">
<div style="flex: 1; min-width: 250px;">
<h3 style="color: #FF6B00 !important; font-family: 'Oswald', sans-serif !important; font-size: 1.8rem; margin-bottom: 15px; border-bottom: 2px solid rgba(255,107,0,0.2); padding-bottom: 10px; letter-spacing: 1px; margin-top: 0;">🎯 NUESTRA MISIÓN</h3>
<p style="color: #1D1D1F !important; line-height: 1.6; font-size: 1.05rem; font-weight: 500; margin: 0;">Ofrecer a cada cliente una experiencia auténtica y deliciosa, sirviendo tacos tradicionales de res, puerco y tripa con el sabor casero que nos define. Brindamos un servicio excepcional y cercano, marcado por la calidez, paciencia y el amor de una familia que ha crecido sirviendo, haciendo que cada persona se sienta bienvenida y valorada.</p>
</div>
<div style="flex: 1; min-width: 250px;">
<h3 style="color: #FF6B00 !important; font-family: 'Oswald', sans-serif !important; font-size: 1.8rem; margin-bottom: 15px; border-bottom: 2px solid rgba(255,107,0,0.2); padding-bottom: 10px; letter-spacing: 1px; margin-top: 0;">👁️ NUESTRA VISIÓN</h3>
<p style="color: #1D1D1F !important; line-height: 1.6; font-size: 1.05rem; font-weight: 500; margin: 0;">Consolidarnos como la taquería de tradición preferida en nuestra comunidad, siendo un referente de cómo el sabor inigualable y la atención humana pueden perdurar por generaciones. Aspiramos a ser un legado familiar que inspire, demostrando que el trabajo hecho con cariño y perseverancia es el ingrediente principal del éxito.</p>
</div>
</div>
<h2 class="valores-title">NUESTROS VALORES</h2>
<div class="valores-grid">
<div class="valor-item">
<div class="valor-icon"><svg viewBox="0 0 24 24"><path d="M12 .587l3.668 7.568 8.332 1.151-6.064 5.828 1.48 8.279-7.416-3.967-7.417 3.967 1.481-8.279-6.064-5.828 8.332-1.151z"/></svg></div>
<div class="valor-text">
<h4>Calidad y Sabor</h4>
<p>Compromiso total con un sabor auténtico y delicioso en cada bocado.</p>
</div>
</div>
<div class="valor-item">
<div class="valor-icon"><svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg></div>
<div class="valor-text">
<h4>Servicio Amable</h4>
<p>Creemos que un buen taco se disfruta más con una sonrisa. Atendemos con respeto y paciencia.</p>
</div>
</div>
<div class="valor-item">
<div class="valor-icon"><svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg></div>
<div class="valor-text">
<h4>Pasión y Cariño</h4>
<p>Hacemos nuestro trabajo con amor genuino todos los días, y se nota en la comida.</p>
</div>
</div>
<div class="valor-item">
<div class="valor-icon"><svg viewBox="0 0 24 24"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z"/></svg></div>
<div class="valor-text">
<h4>Perseverancia</h4>
<p>Honramos nuestra historia. El éxito se construye día a día con constancia absoluta.</p>
</div>
</div>
<div class="valor-item">
<div class="valor-icon"><svg viewBox="0 0 24 24"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></div>
<div class="valor-text">
<h4>Unión Familiar</h4>
<p>Somos un equipo unido por lazos de familia. Esa unidad se refleja en nuestro servicio.</p>
</div>
</div>
<div class="valor-item">
<div class="valor-icon"><svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/></svg></div>
<div class="valor-text">
<h4>Honestidad</h4>
<p>Actuamos con total transparencia en la calidad de los productos que te ofrecemos.</p>
</div>
</div>
</div>
""", unsafe_allow_html=True)

with tabs[4]:
    from datetime import datetime

    # Cargar reseñas desde Sheets (se actualiza cada 30 seg)
    resenas_sheets = cargar_resenas_sheets(URL_CSV_RESENAS) if "PEGA_AQUI" not in URL_CSV_RESENAS else []
    # Combinar las reseñas de Sheets con las nuevas de sesión (antes de que recarguen)
    todas_resenas = st.session_state.resenas + resenas_sheets

    # ── CABECERA ──
    st.markdown("""
<div class="resena-header">
<h2>LO QUE DICEN NUESTROS CLIENTES</h2>
<p>Opiniones reales de nuestra comunidad</p>
</div>
""", unsafe_allow_html=True)

    # ── CAJA DE PROMEDIO ──
    if todas_resenas:
        promedio = sum(r["estrellas"] for r in todas_resenas) / len(todas_resenas)
        estrellas_promedio = "⭐" * round(promedio)
        total_resenas = len(todas_resenas)
        st.markdown(f"""
<div class="promedio-box">
<p class="promedio-numero">{promedio:.1f}</p>
<p class="promedio-stars">{estrellas_promedio}</p>
<p class="promedio-label">Basado en {total_resenas} reseña{"s" if total_resenas != 1 else ""}</p>
</div>
""", unsafe_allow_html=True)

    # ── FORMULARIO NUEVA RESEÑA ──
    st.markdown("<h3 style='color: var(--color-naranja) !important; font-family: Oswald, sans-serif; font-size: 1.6rem; margin-bottom: 5px;'>✍️ DEJA TU OPINIÓN</h3>", unsafe_allow_html=True)

    with st.form("form_resena", clear_on_submit=True):
        col_nom, col_est = st.columns([3, 2])
        with col_nom:
            nombre_resena = st.text_input("Tu nombre:", placeholder="Ej. Ana García")
        with col_est:
            estrellas_input = st.select_slider(
                "Calificación:",
                options=[1, 2, 3, 4, 5], value=5,
                format_func=lambda x: "⭐" * x
            )
        comentario_resena = st.text_area(
            "Tu comentario:",
            placeholder="¿Qué fue lo que más te gustó? ¡Cuéntanos!",
            height=100
        )
        foto_resena = st.file_uploader(
            "📷 Agrega una foto (opcional) — JPG o PNG, máx. 3 MB",
            type=["jpg", "jpeg", "png"],
            help="Comparte una foto de tus tacos o del local 🌮"
        )
        enviar_resena = st.form_submit_button("Publicar Reseña ⭐", type="primary", use_container_width=True)

    if enviar_resena:
        if nombre_resena.strip() and comentario_resena.strip():
            # Procesar imagen si se subió
            imagen_b64 = ""
            imagen_tipo = ""
            imagen_nombre = ""
            if foto_resena is not None:
                if foto_resena.size > 3 * 1024 * 1024:
                    st.error("⚠️ La imagen es muy grande. Por favor sube una de menos de 3 MB.")
                    st.stop()
                imagen_b64 = base64.b64encode(foto_resena.read()).decode("utf-8")
                imagen_tipo = foto_resena.type
                imagen_nombre = foto_resena.name

            nueva_resena = {
                "nombre":       nombre_resena.strip(),
                "estrellas":    estrellas_input,
                "comentario":   comentario_resena.strip(),
                "fecha":        datetime.now().strftime("%d/%m/%Y"),
                "imagen_b64":   imagen_b64,
                "imagen_tipo":  imagen_tipo,
                "imagen_nombre": imagen_nombre,
            }

            # Guardar en Google Sheets via Apps Script (hilo separado)
            if "PEGA_AQUI" not in URL_APPS_SCRIPT_RESENAS:
                threading.Thread(
                    target=enviar_resena_sheets,
                    args=(URL_APPS_SCRIPT_RESENAS, nueva_resena)
                ).start()

            # Mostrar inmediatamente en sesión
            nueva_local = {
                "nombre":     nombre_resena.strip(),
                "estrellas":  estrellas_input,
                "comentario": comentario_resena.strip(),
                "fecha":      datetime.now().strftime("%b %Y"),
                "imagen_url": "",   # La URL real llega cuando Sheets recargue
            }
            if imagen_b64:
                nueva_local["imagen_b64_preview"] = imagen_b64
                nueva_local["imagen_tipo_preview"] = imagen_tipo

            st.session_state.resenas.insert(0, nueva_local)
            cargar_resenas_sheets.clear()   # forzar recarga del caché
            st.toast(f"¡Gracias {nombre_resena.strip().split()[0]}! Tu reseña fue publicada 🌮", icon="⭐")
            st.rerun()
        else:
            st.error("Por favor escribe tu nombre y un comentario.")

    st.divider()

    # ── GRID DE RESEÑAS ──
    st.markdown("<h3 style='color: var(--color-texto) !important; font-family: Oswald, sans-serif; font-size: 1.5rem; margin-bottom: 20px;'>TODAS LAS RESEÑAS</h3>", unsafe_allow_html=True)

    if todas_resenas:
        col_a, col_b = st.columns(2)
        for i, r in enumerate(todas_resenas):
            col = col_a if i % 2 == 0 else col_b
            estrellas_html = "⭐" * r["estrellas"] + "☆" * (5 - r["estrellas"])
            with col:
                st.markdown(f"""
<div class="resena-card">
<div class="resena-stars">{estrellas_html}</div>
<p class="resena-texto">"{r['comentario']}"</p>
<p class="resena-autor">— {r['nombre']} &nbsp;·&nbsp; {r['fecha']}</p>
</div>
""", unsafe_allow_html=True)
                # Mostrar imagen si existe URL de Drive o preview base64
                img_url = r.get("imagen_url", "")
                img_b64_prev = r.get("imagen_b64_preview", "")
                img_tipo_prev = r.get("imagen_tipo_preview", "image/jpeg")
                if img_url and img_url not in ("", "nan"):
                    st.image(img_url, use_container_width=True)
                elif img_b64_prev:
                    st.markdown(
                        f'<img src="data:{img_tipo_prev};base64,{img_b64_prev}" '
                        f'style="width:100%;border-radius:12px;margin-top:-8px;margin-bottom:12px;">',
                        unsafe_allow_html=True
                    )
    else:
        st.info("Aún no hay reseñas. ¡Sé el primero en comentar!")

# ==========================================
# 9. FOOTER O PIE DE PÁGINA
# ==========================================
st.markdown("""
<div class='footer-container'>
<h3 style="margin-bottom: 5px;">El Taco Loco</h3>
<p style="margin-bottom: 30px; font-weight: 500;">Los mejores tacos de Coita, a un clic de distancia.</p>
<div style="display: flex; justify-content: center; margin-bottom: 20px;">
<a href='https://www.facebook.com/share/1GSfLr4nxj/?mibextid=wwXIfr' target='_blank' title="Facebook" class="social-link"><svg width="30" height="30" viewBox="0 0 24 24"><path d="M22.675 0h-21.35C.597 0 0 .597 0 1.325v21.351C0 23.403.597 24 1.325 24H12.82v-9.294H9.692v-3.622h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12V24h6.116c.73 0 1.323-.597 1.323-1.324V1.325C24 .597 23.403 0 22.675 0z"/></svg></a>
<a href='#' target='_blank' title="Instagram" class="social-link"><svg width="30" height="30" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 1.76-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 1.76 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-1.762 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-1.778-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4s1.791-4 4-4 4 1.79 4 4-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg></a>
<a href='#' target='_blank' title="TikTok" class="social-link"><svg width="30" height="30" viewBox="0 0 24 24"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.53 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg></a>
</div>
<p class="texto-creditos">© 2026 ElTacoLoco. Todos los derechos reservados. Hecho con 🔥 por AleRampz</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 8. PANEL DE ADMINISTRADOR SECRETO Y DASHBOARD
# ==========================================
with st.expander("⚙️"):
    st.markdown(f'<div style="text-align:center; margin-bottom: 15px;">{logo_html}</div>', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: var(--color-naranja) !important; font-family: Oswald, sans-serif; margin-bottom: 20px;'>PANEL DE CONTROL</h2>", unsafe_allow_html=True)
    
    if not st.session_state.admin_logged_in:
        pwd = st.text_input("Contraseña maestra:", type="password")
        if st.button("Entrar al sistema", type="primary", use_container_width=True):
            if pwd == "TacoLoco2026":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Acceso denegado. Contraseña incorrecta.")
    else:
        st.success("✅ Autenticado como Administrador")
        
        # --- PESTAÑAS PARA NO AMONTONAR EL DISEÑO ---
        tab_operacion, tab_metricas = st.tabs(["🎛️ Control Operativo", "📊 Reporte de Ventas"])
        
        # --- PESTAÑA 1: CONTROL OPERATIVO ---
        with tab_operacion:
            st.markdown("""
                <div style='background-color: var(--color-crema); padding: 20px; border-radius: 15px; border-left: 5px solid var(--color-naranja); margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05);'>
                    <h4 style='margin-top:0; color: var(--color-texto) !important; font-family: Oswald, sans-serif;'>🎛️ ESTADO DE LA TAQUERÍA</h4>
                    <p style='color: #666 !important; font-size: 0.95rem; margin-bottom: 0;'>Pausa toda la tienda si hay demasiada gente y no puedes recibir pedidos.</p>
                </div>
            """, unsafe_allow_html=True)
            
            nuevo_estado = st.toggle("🟢 RECIBIENDO PEDIDOS", value=st.session_state.tienda_abierta)
            if nuevo_estado != st.session_state.tienda_abierta:
                st.session_state.tienda_abierta = nuevo_estado
                st.rerun()
                
            st.divider()
            
            st.markdown("""
                <div style='background-color: var(--color-crema); padding: 20px; border-radius: 15px; border-left: 5px solid var(--color-rojo); margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05);'>
                    <h4 style='margin-top:0; color: var(--color-texto) !important; font-family: Oswald, sans-serif;'>🥩 INVENTARIO (AGOTAR PLATILLOS)</h4>
                    <p style='color: #666 !important; font-size: 0.95rem; margin-bottom: 0;'>Activa el botón si se acabó un producto para que los clientes ya no puedan pedirlo.</p>
                </div>
            """, unsafe_allow_html=True)
            
            for item in menu_completo.keys():
                is_agotado = item in st.session_state.agotados
                marcar_agotado = st.toggle(f"🚫 Agotar: {item}", value=is_agotado, key=f"admin_agotado_{item}")
                
                if marcar_agotado and not is_agotado:
                    st.session_state.agotados.append(item)
                    if item in st.session_state.carrito: del st.session_state.carrito[item]
                    st.rerun()
                elif not marcar_agotado and is_agotado:
                    st.session_state.agotados.remove(item)
                    st.rerun()

        # --- PESTAÑA 2: MÉTRICAS Y GRÁFICAS ---
        with tab_metricas:
            # Enlace modificado a formato CSV para lectura rápida
            URL_CSV_PEDIDOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQTIoRwg327pe_n_h-paHJ2OMmufADQgIfeiTvXBWTzfnDyJn21dDhhSYq97WZIVb8ZzQfwaHlGGmvd/pub?gid=0&single=true&output=csv"
            
            try:
                df_pedidos = pd.read_csv(URL_CSV_PEDIDOS)
                
                # Buscamos columnas de manera segura sin importar mayúsculas
                col_total = next((c for c in df_pedidos.columns if 'total' in c.lower()), None)
                col_pedido = next((c for c in df_pedidos.columns if 'pedido' in c.lower()), None)
                
                total_ingresos = 0
                if col_total:
                    # MAGIA ANTI-ERRORES: Borramos el '$' y las comas antes de sumar
                    df_pedidos[col_total] = df_pedidos[col_total].astype(str).str.replace(r'[\$,]', '', regex=True)
                    df_pedidos[col_total] = pd.to_numeric(df_pedidos[col_total], errors='coerce').fillna(0)
                    total_ingresos = df_pedidos[col_total].sum()
                    
                total_ordenes = len(df_pedidos)
                ticket_promedio = total_ingresos / total_ordenes if total_ordenes > 0 else 0
                
                st.markdown("<h3 style='color: var(--color-texto) !important; font-family: Oswald, sans-serif;'>MÉTRICAS EN TIEMPO REAL</h3>", unsafe_allow_html=True)
                
                # Cajas Gigantes de Métricas
                c1, c2, c3 = st.columns(3)
                c1.metric(label="💰 Ventas Totales", value=f"${total_ingresos:,.2f}")
                c2.metric(label="📦 Total de Pedidos", value=f"{total_ordenes}")
                c3.metric(label="🧾 Ticket Promedio", value=f"${ticket_promedio:,.2f}")
                
                st.divider()
                
                # Motor de lectura para "Cosas Más Vendidas"
                if col_pedido:
                    ventas_items = {}
                    for p in df_pedidos[col_pedido].dropna():
                        # Expresión regular que busca patrones como "2x Tacos"
                        matches = re.findall(r'(\d+)\s*[xX]\s*([^,\|]+)', str(p))
                        for cant, item in matches:
                            item_name = item.strip()
                            ventas_items[item_name] = ventas_items.get(item_name, 0) + int(cant)
                    
                    if ventas_items:
                        # Convertimos a formato tabla para la gráfica
                        df_top = pd.DataFrame(list(ventas_items.items()), columns=['Platillo', 'Vendidos'])
                        df_top = df_top.sort_values(by='Vendidos', ascending=False).head(7)
                        
                        # GRÁFICA ALTAIR: Fondo blanco, barras coloridas y redondeadas
                        grafica = alt.Chart(df_top).mark_bar(
                            cornerRadiusTopLeft=5, 
                            cornerRadiusTopRight=5,
                            size=40
                        ).encode(
                            x=alt.X('Platillo', sort='-y', axis=alt.Axis(labelAngle=-45, title=None, labelFontSize=13, labelColor='#1D1D1F')),
                            y=alt.Y('Vendidos', axis=alt.Axis(title='Cantidad Vendida', labelFontSize=13, labelColor='#1D1D1F', grid=True)),
                            color=alt.Color('Platillo', scale=alt.Scale(scheme='category20b'), legend=None),
                            tooltip=['Platillo', 'Vendidos']
                        ).properties(
                            background='white',
                            height=380
                        ).configure_axis(
                            labelColor='#1D1D1F',
                            titleColor='#1D1D1F'
                        ).configure_view(
                            strokeWidth=0
                        )
                        
                        st.markdown("#### 🏆 Los Productos Más Vendidos")
                        st.altair_chart(grafica, use_container_width=True)
                    else:
                        st.info("Aún no hay platillos registrados en el Excel de pedidos para hacer la gráfica.")
                else:
                    st.warning("No se encontró la columna de 'pedido' en tu Excel.")

            except Exception as e:
                st.info("Sube algunos pedidos a tu base de datos para generar las gráficas.")

        st.divider()
        if st.button("Cerrar Sesión", type="secondary", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()   


































