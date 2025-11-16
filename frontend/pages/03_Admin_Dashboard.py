import streamlit as st
from mock_api import list_itineraries

def run():
    st.header("🗂 Trip History")
    items = list_itineraries()
    if not items:
        st.info("No history yet.")
        return
    for it in items:
        with st.expander(it["title"]):
            st.write("Preview content not available in demo.")
            st.markdown(f"- id: `{it['id']}`")

run()
