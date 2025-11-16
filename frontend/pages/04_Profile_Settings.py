import streamlit as st

def run():
    st.header("👤 Profile & Settings")
    with st.container():
        st.subheader("Profile")
        name = st.text_input("Full name")
        email = st.text_input("Email")
        bio = st.text_area("Bio", max_chars=240)
        if st.button("Save profile"):
            st.success("Profile saved (mock).")
    with st.container():
        st.subheader("App settings")
        st.checkbox("Enable safe-mode (demo)", value=True)
        st.selectbox("Theme (demo)", ["Dark (default)", "Light"])
        if st.button("Reset demo data"):
            st.success("Demo data cleared (mock).")

run()

