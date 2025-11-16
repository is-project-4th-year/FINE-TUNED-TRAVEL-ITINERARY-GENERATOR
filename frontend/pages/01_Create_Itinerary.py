import streamlit as st
from mock_api import generate_itinerary, extract_itinerary, save_itinerary

def run():
    st.header("🧭 Create Itinerary")
    col_desc, col_form, col_preview = st.columns([1.1, 1.8, 1.0])

    # LEFT: description + examples
    with col_desc:
        with st.container():
            st.subheader("✏ Describe Your Trip")
            description = st.text_area("Trip brief",
                                      placeholder="E.g., 4-day food & culture trip to Nairobi focusing on museums and markets.",
                                      height=140)
            st.caption("Tip: Be specific — include interests, pace, and constraints.")
        with st.container():
            st.subheader("Quick examples")
            examples = [
                "Plan a 4-day food & culture trip focusing on museums and markets.",
                "Weekend getaway with romantic restaurants and art galleries.",
                "7-day adventure with hiking and wildlife.",
                "Family trip with kid-friendly activities."
            ]
            for i, ex in enumerate(examples):
                # tiled clickable example (safe)
                st.markdown(f'<div class="example-tile" onclick="window.location.href=\'?ex={i}\'">{ex}</div>', unsafe_allow_html=True)
            # handle query param click
            params = st.query_params
            if "ex" in params:
                idx = int(params["ex"][0])
                description = examples[idx]
                st.query_params.update(...)
                st.experimental_rerun()

    # CENTER: form inputs
    with col_form:
        with st.container():
            st.subheader("📍 Travel Details")
            origin = st.text_input("Origin", value="")
            destination = st.text_input("Destination", value="")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
        with st.container():
            st.subheader("👥 Travelers & Budget")
            travelers = st.number_input("Number of travelers", min_value=1, value=1)
            budget = st.number_input("Approx. budget (USD)", min_value=0, value=500)
        with st.container():
            st.subheader("🎯 Preferences & Constraints")
            interests = st.multiselect("Interests", ["Food", "Museums", "Markets", "Nature", "Nightlife", "Culture", "Shopping", "Adventure"])
            advanced = st.checkbox("Show advanced options")
            if advanced:
                st.text_input("Mobility or dietary constraints (optional)")
                st.selectbox("Preferred pace", ["Relaxed", "Moderate", "Active"])
        with st.container():
            generate = st.button("Generate Itinerary")
            save_title = st.text_input("Save as (optional)", placeholder="My Nairobi trip")
            save_click = st.button("Save itinerary")

    # RIGHT: preview + validation
    with col_preview:
        with st.container():
            st.subheader("📝 Prompt preview")
            st.write(f"**Description:** {description or '—'}")
            st.write(f"**Destination:** {destination or '—'}")
            st.write(f"**Dates:** {start_date} → {end_date}")
            st.write(f"**Travellers:** {travelers} | **Budget:** ${budget}")
            st.write(f"**Interests:** {', '.join(interests) if interests else '—'}")
        with st.container():
            st.subheader("Validation")
            if not destination:
                st.error("Destination is required")
            elif budget < 50:
                st.warning("Budget looks very low")
            else:
                st.success("Looks good — generate when ready")

    # Generation behavior
    if generate:
        with st.spinner("Calling generator..."):
            out = generate_itinerary(
                origin=origin, destination=destination,
                start_date=start_date, end_date=end_date,
                travelers=travelers, budget=budget,
                interests=interests, description=description
            )
        st.success("Itinerary generated")
        st.markdown(out)

    if save_click:
        # for demo we save mock text
        key = save_itinerary(save_title or f"Trip to {destination or 'Unknown'}", description or "Generated")
        st.success(f"Saved as {save_title or key}")

run()