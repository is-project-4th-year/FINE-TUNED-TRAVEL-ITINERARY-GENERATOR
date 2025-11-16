import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.title("TravelPlanner – Demo")

prompt = st.text_area("Describe your itinerary request:")
if st.button("Generate"):
    r = requests.post(f"{BASE_URL}/generate", json={"context":{"prompt":prompt},"length":800})
    st.write(r.json()["itinerary"])
