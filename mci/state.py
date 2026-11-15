"""Estado de sesión: navegación y lista de seguimiento (se guarda en la URL, sin base de datos)."""
import streamlit as st

VIEWS = ["Mercado", "Radar", "Activo", "Comparar", "Guía"]


def init():
    ss = st.session_state
    ss.setdefault("view", "Mercado")
    ss.setdefault("asset_id", None)
    ss.setdefault("radar_nonce", 0)
    if "watch" not in ss:
        try:
            raw = st.query_params.get("w", "")
        except Exception:
            raw = ""
        ss["watch"] = [w for w in str(raw).split(",") if w][:50]


def open_asset(coin_id):
    st.session_state["asset_id"] = coin_id
    st.session_state["view"] = "Activo"


def go(view):
    st.session_state["view"] = view


def toggle_watch(coin_id):
    w = list(st.session_state.get("watch", []))
    if coin_id in w:
        w.remove(coin_id)
    else:
        w.append(coin_id)
    st.session_state["watch"] = w
    try:
        if w:
            st.query_params["w"] = ",".join(w)
        elif "w" in st.query_params:
            del st.query_params["w"]
    except Exception:
        pass
