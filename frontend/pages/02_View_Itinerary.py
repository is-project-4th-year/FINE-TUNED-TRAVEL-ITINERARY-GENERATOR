import streamlit as st
from mock_api import list_itineraries, get_itinerary

def run():
    st.header("📅 View / Edit Itinerary")
    iters = list_itineraries()
    if not iters:
        st.info("No saved itineraries yet. Generate and save one from Create page.")
        return

    left, right = st.columns([0.6, 1.4])
    with left:
        st.subheader("Saved itineraries")
        for it in iters:
            if st.button(it["title"], key=f"open_{it['id']}"):
                st.session_state["_open_id"] = it["id"]
    with right:
        open_id = st.session_state.get("_open_id")
        if not open_id:
            st.info("Select a saved itinerary to view details.")
        else:
            data = get_itinerary(open_id)
            if not data:
                st.error("Selected itinerary not found.")
            else:
                st.subheader(data["title"])
                st.write(data["content"])
                if st.button("Export as text"):
                    st.download_button("Download TXT", data["content"], file_name=f"{data['title']}.txt")

run()
