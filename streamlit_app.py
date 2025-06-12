import streamlit as st
import requests
import json
import base64

# ------------------------------------------------------
# CONFIGURACIÓN: ajusta según dónde esté corriendo tu API
# ------------------------------------------------------
API_BASE            = "http://localhost:8060"
LOGIN_ENDPOINT      = f"{API_BASE}/auth/token"
LOGOUT_ENDPOINT     = f"{API_BASE}/auth/logout"
PRODUCTS_ENDPOINT   = f"{API_BASE}/products"
ORDERS_ENDPOINT     = f"{API_BASE}/orders"
ALL_ORDERS_ENDPOINT = f"{API_BASE}/orders/all"
EXPORT_ENDPOINT     = f"{API_BASE}/exports"
# ------------------------------------------------------


def save_tokens(access_token: str, refresh_token: str):
    st.session_state["access_token"]  = access_token
    st.session_state["refresh_token"] = refresh_token


def get_auth_header() -> dict:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def get_user_role() -> str:
    """Decodifica el JWT y devuelve el campo 'role' correctamente."""
    token = st.session_state.get("access_token")
    if not token:
        return ""
    try:
        payload_enc = token.split(".")[1]
        padding     = "=" * ((4 - len(payload_enc) % 4) % 4)
        decoded     = base64.urlsafe_b64decode(payload_enc + padding)
        data        = json.loads(decoded)
        return data.get("role", "")
    except:
        return ""


def login_page() -> bool:
    """Muestra el formulario de login. Devuelve True si login correcto."""
    st.title("🔐 Iniciar sesión")
    with st.form("login_form", clear_on_submit=False):
        username  = st.text_input("Usuario")
        password  = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Entrar")

    if not submitted:
        return False

    if not username or not password:
        st.warning("Debes indicar usuario y contraseña.")
        return False

    try:
        resp = requests.post(
            LOGIN_ENDPOINT,
            data={"username": username, "password": password}
        )
    except requests.exceptions.RequestException as e:
        st.error(f"No se pudo conectar al servidor: {e}")
        return False

    if resp.status_code == 200:
        tokens = resp.json()
        save_tokens(tokens["access_token"], tokens["refresh_token"])
        st.success("✔️ Login correcto.")
        return True
    else:
        det = resp.json().get("detail", resp.text)
        st.error(f"❌ {resp.status_code} – {det}")
        return False


def logout():
    headers = get_auth_header()
    if not headers:
        st.info("No hay usuario autenticado.")
        return
    try:
        resp = requests.post(LOGOUT_ENDPOINT, headers=headers)
    except requests.exceptions.RequestException as e:
        st.error(f"No se pudo conectar: {e}")
        return

    if resp.status_code == 200:
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        st.success("✔️ Sesión cerrada.")
    else:
        det = resp.json().get("detail", resp.text)
        st.error(f"❌ {resp.status_code} – {det}")


def products_page():
    st.title("🛍️ Lista de productos")
    headers = get_auth_header()
    if not headers:
        st.warning("🔒 Debes iniciar sesión para ver productos.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        limit = st.number_input("Items/página:", min_value=1, max_value=100, value=10)
    with col2:
        skip = st.number_input("Omitir (skip):", min_value=0, value=0)
    with col3:
        sort = st.text_input("Orden (e.g. price o -price):", "")
    cat       = st.text_input("Filtrar categoría:", "")
    min_price = st.number_input("Precio mínimo:", min_value=0.0, value=0.0, format="%.2f")
    max_price = st.number_input("Precio máximo:", min_value=0.0, value=0.0, format="%.2f")

    if st.button("🔄 Refrescar listado"):
        params = {
            "limit": limit,
            "skip": skip,
            "sort": sort or None,
            "category": cat or None,
            "min_price": min_price if min_price > 0 else None,
            "max_price": max_price if max_price > 0 else None,
        }
        params = {k: v for k, v in params.items() if v is not None}
        try:
            resp = requests.get(PRODUCTS_ENDPOINT, params=params, headers=headers)
        except requests.exceptions.RequestException:
            st.error("No se pudo conectar al servidor.")
            return

        if resp.status_code != 200:
            st.error(f"Error {resp.status_code} – {resp.text}")
            return

        data = resp.json()
        st.write(f"**Total de productos:** {data.get('total', 0)}")
        for p in data.get("products", []):
            st.subheader(f"{p['title']} – ${p['price']}")
            st.write(f"ID {p['id']} | Cat: {p['category']} | Stock: {p['stock']}")
            st.write(p["description"])
            st.markdown("---")


def create_order_page():
    headers = get_auth_header()
    if not headers:
        st.warning("🔒 Debes iniciar sesión para crear pedidos.")
        return

    st.title("📝 Crear nuevo pedido")
    if "order_items" not in st.session_state:
        st.session_state.order_items = []

    with st.form("add_item_form", clear_on_submit=True):
        pid = st.number_input("Product ID:", min_value=1, value=1)
        qty = st.number_input("Cantidad:",    min_value=1, value=1)
        add = st.form_submit_button("➕ Agregar ítem")
    if add:
        st.session_state.order_items.append({"product_id": pid, "quantity": qty})

    if st.session_state.order_items:
        st.write("**Ítems en el pedido:**")
        for idx, it in enumerate(st.session_state.order_items, 1):
            st.write(f"{idx}. {it['product_id']} × {it['quantity']}")
        if st.button("📤 Enviar pedido"):
            try:
                resp = requests.post(ORDERS_ENDPOINT,
                                     json={"items": st.session_state.order_items},
                                     headers=headers)
            except requests.exceptions.RequestException:
                st.error("No se pudo conectar")
                return
            if resp.status_code == 201:
                st.success("✔️ Pedido creado con éxito.")
                st.session_state.order_items = []
            else:
                det = resp.json().get("detail", resp.text)
                st.error(f"❌ {resp.status_code} – {det}")


def list_orders_page():
    headers = get_auth_header()
    if not headers:
        st.warning("🔒 Debes iniciar sesión para ver tus pedidos.")
        return

    st.title("📦 Mis pedidos")
    try:
        resp = requests.get(ORDERS_ENDPOINT, headers=headers)
    except:
        st.error("No se pudo conectar")
        return

    if resp.status_code == 200:
        for o in resp.json():
            st.write(f"Pedido #{o['id']} – {o['state']} ({o['created_at'][:10]})")
            with st.expander("Ver ítems"):
                for it in o["items"]:
                    p = it["product"]
                    st.write(f"- {p['title']} × {it['quantity']} – ${p['price']}")
            st.markdown("---")
    else:
        det = resp.json().get("detail", resp.text)
        st.error(f"❌ {resp.status_code} – {det}")


def list_all_orders_page():
    headers = get_auth_header()
    role    = get_user_role()
    if not headers or role != "admin":
        st.warning("🔒 Solo admin puede ver todos los pedidos.")
        return

    st.title("📋 Todos los pedidos (ADMIN)")
    try:
        resp = requests.get(ALL_ORDERS_ENDPOINT, headers=headers)
    except:
        st.error("No se pudo conectar")
        return

    if resp.status_code == 200:
        for o in resp.json():
            st.write(f"#{o['id']} – Usuario {o['user_id']} – {o['state']}")
    else:
        st.error(f"❌ {resp.status_code} – {resp.text}")


def export_page():
    headers = get_auth_header()
    if not headers:
        st.warning("🔒 Debes iniciar sesión para exportar pedidos.")
        return

    st.title("📤 Exportar pedidos")
    fmt     = st.selectbox("Formato:", ["csv", "excel", "pdf"])
    role    = get_user_role()
    user_id = None
    if role == "admin":
        u = st.number_input("User ID (0 = todos):", min_value=0, value=0, step=1)
        if u > 0:
            user_id = u

    if st.button("📥 Exportar"):
        body = {"format": fmt}
        if user_id is not None:
            body["user_id"] = user_id
        try:
            resp = requests.post(EXPORT_ENDPOINT, json=body, headers=headers)
        except:
            st.error("No se pudo conectar")
            return

        if resp.status_code == 200:
            disp = resp.headers.get("Content-Disposition", "")
            fn   = disp.split("filename=")[-1].strip('"') if "filename=" in disp else "export"
            st.success(f"✔️ Export generado: {fn}")
            st.download_button("Descargar", data=resp.content, file_name=fn,
                               mime=resp.headers.get("content-type"))
        else:
            det = resp.json().get("detail", resp.text)
            st.error(f"❌ {resp.status_code} – {det}")


def main():
    st.set_page_config(page_title="Tienda Online Front", layout="wide")

    # 1) Si no hay token, intento login. Si falla, salgo.
    if not st.session_state.get("access_token"):
        if not login_page():
            return

    # 2) Ya hay token: construyo menú según rol
    role    = get_user_role()
    options = ["Listar Productos", "Crear Pedido", "Ver Mis Pedidos", "Exportar Pedidos", "Cerrar Sesión"]
    if role == "admin":
        options.insert(4, "Listar Todos Pedidos")

    choice = st.sidebar.radio("📋 Menú", options)

    if   choice == "Listar Productos":     products_page()
    elif choice == "Crear Pedido":         create_order_page()
    elif choice == "Ver Mis Pedidos":      list_orders_page()
    elif choice == "Exportar Pedidos":     export_page()
    elif choice == "Listar Todos Pedidos": list_all_orders_page()
    elif choice == "Cerrar Sesión":        logout()


if __name__ == "__main__":
    main()