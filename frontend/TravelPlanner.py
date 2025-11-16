import streamlit as st

st.set_page_config(page_title="Travel Planner", layout="wide")

# Load global CSS safely
import pathlib
css_path = pathlib.Path("assets/ui.css")
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

st.title("Travel Planner Dashboard")
st.write("Use the sidebar to navigate between pages.")
