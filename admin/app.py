import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.getenv("API_URL", "http://backend:8000")

st.set_page_config(page_title="Wellbeing Admin", page_icon="🌿", layout="wide")
st.title("🌿 WellBeing Tracker — Admin Dashboard")

# Admin login (simple token-based)
if "token" not in st.session_state:
    st.subheader("Admin Login")
    email = st.text_input("Email")
    pwd   = st.text_input("Password", type="password")
    if st.button("Login"):
        r = requests.post(f"{API_URL}/auth/login",
                          data={"username": email, "password": pwd}, timeout=10)
        if r.status_code == 200:
            st.session_state.token = r.json()["access_token"]
            st.rerun()
        else:
            st.error("Login gagal.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

def get(path):
    try:
        r = requests.get(f"{API_URL}{path}", headers=headers, timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []

if st.button("Logout"):
    del st.session_state.token
    st.rerun()

# ── Data ──────────────────────────────────────────────────
entries  = get("/entries")
journals = get("/journal")
todos    = get("/todos")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📖 Journal", "✅ To-Do", "🏃 Tracking"])

with tab1:
    if not entries:
        st.info("No wellbeing entries yet.")
    else:
        df = pd.DataFrame(entries)
        df["created_at"] = pd.to_datetime(df["created_at"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Logs",    len(df))
        c2.metric("Avg Mood",      f"{df['mood'].mean():.1f}/10")
        c3.metric("Avg Energy",    f"{df['energy'].mean():.1f}/10")
        c4.metric("Avg Stress",    f"{df['stress'].mean():.1f}/10")

        st.divider()
        st.subheader("Mood / Energy / Stress Over Time")
        chart = df.set_index("created_at")[["mood", "energy", "stress"]].sort_index()
        st.line_chart(chart)

        st.subheader("Sleep Hours")
        st.bar_chart(df.set_index("created_at")["sleep_hours"].sort_index())

        with st.expander("Raw Data"):
            st.dataframe(df, use_container_width=True)

with tab2:
    if not journals:
        st.info("No journal entries yet.")
    else:
        df_j = pd.DataFrame(journals)
        st.dataframe(df_j[["id", "title", "mood", "created_at"]], use_container_width=True)
        mood_counts = df_j["mood"].value_counts()
        st.subheader("Mood Distribution")
        st.bar_chart(mood_counts)

with tab3:
    if not todos:
        st.info("No todos yet.")
    else:
        df_t = pd.DataFrame(todos)
        done   = df_t[df_t["done"] == True]
        active = df_t[df_t["done"] == False]
        c1, c2 = st.columns(2)
        c1.metric("Active Tasks",    len(active))
        c2.metric("Completed Tasks", len(done))
        st.subheader("All Tasks")
        st.dataframe(df_t[["id", "title", "category", "priority", "done"]], use_container_width=True)

with tab4:
    tracking = get("/tracking/today")
    if tracking:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sleep",      f"{tracking.get('sleep', 0)}h")
        c2.metric("Exercise",   f"{tracking.get('exercise', 0)}min")
        c3.metric("Water",      f"{tracking.get('water', 0)} glasses")
        c4.metric("Heart Rate", f"{tracking.get('heart_rate', 0)} bpm")
        c5.metric("Meditation", f"{tracking.get('meditation', 0)}min")
    else:
        st.info("No tracking data for today.")
