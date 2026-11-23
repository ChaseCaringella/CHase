import streamlit as st


sleep_coach_page = st.Page(
    "pages/1_Sleep_Coach.py",
    title="Sleep Coach",
    icon="🌙",
    default=True,
)
gym_tracker_page = st.Page(
    "pages/2_Gym_Tracker.py",
    title="Gym Tracker",
    icon="🏋️",
)

page = st.navigation([sleep_coach_page, gym_tracker_page])
page.run()
