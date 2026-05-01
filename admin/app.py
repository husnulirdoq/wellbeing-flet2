import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.getenv("API_URL", "http://backend:8000")

st.set_page_config(page_title="WellBeing Admin", page_icon="🌿", layout="wide")
st.title("🌿 WellBeing Tracker — Admin Dashboard")

# ── Login ──────────────────────────────────────────────────
if "token" not in st.session_state:
    st.subheader("Admin Login")
    email = st.text_input("Email")
    pwd   = st.text_input("Password", type="password")
    if st.button("Login"):
        r = requests.post(f"{API_URL}/auth/login",
                          data={"username": email, "password": pwd}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("role") != "admin":
                st.error("Access denied. Admin only.")
            else:
                st.session_state.token = data["access_token"]
                st.rerun()
        else:
            st.error("Login gagal.")
    
    # Firebase login for admin
    st.divider()
    st.caption("Or login with Firebase credentials (email/password from app)")
    fb_email = st.text_input("Firebase Email", key="fb_email")
    fb_pwd   = st.text_input("Firebase Password", type="password", key="fb_pwd")
    if st.button("Login with Firebase"):
        FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "AIzaSyCTJ-9XV1DUQKFHPSRs5HYPLg8VW6DfoUM")
        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            json={"email": fb_email, "password": fb_pwd, "returnSecureToken": True}, timeout=15)
        if r.ok:
            id_token = r.json()["idToken"]
            r2 = requests.post(f"{API_URL}/auth/firebase",
                               json={"id_token": id_token, "email": fb_email}, timeout=20)
            if r2.ok:
                data = r2.json()
                if data.get("role") != "admin":
                    st.error("Access denied. Admin only.")
                else:
                    st.session_state.token = data["access_token"]
                    st.rerun()
            else:
                st.error("Server error.")
        else:
            st.error(r.json().get("error", {}).get("message", "Login gagal."))
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

def api_get(path):
    try:
        r = requests.get(f"{API_URL}{path}", headers=headers, timeout=10)
        return r.json() if r.ok else []
    except: return []

def api_post(path, data):
    try:
        r = requests.post(f"{API_URL}{path}", json=data, headers=headers, timeout=10)
        return r.json() if r.ok else None
    except: return None

def api_put(path, data):
    try:
        r = requests.put(f"{API_URL}{path}", json=data, headers=headers, timeout=10)
        return r.json() if r.ok else None
    except: return None

def api_delete(path):
    try:
        r = requests.delete(f"{API_URL}{path}", headers=headers, timeout=10)
        return r.ok
    except: return False

col1, col2 = st.columns([8,1])
with col2:
    if st.button("Logout"):
        del st.session_state.token
        st.rerun()

# ── Tabs ───────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview", "📖 Journal", "✅ To-Do", "🏃 Tracking", "🛍️ Products", "👥 Users"
])

# ── Overview ───────────────────────────────────────────────
with tab1:
    entries = api_get("/entries")
    if not entries:
        st.info("No wellbeing entries yet.")
    else:
        df = pd.DataFrame(entries)
        df["created_at"] = pd.to_datetime(df["created_at"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Logs",  len(df))
        c2.metric("Avg Mood",    f"{df['mood'].mean():.1f}/10")
        c3.metric("Avg Energy",  f"{df['energy'].mean():.1f}/10")
        c4.metric("Avg Stress",  f"{df['stress'].mean():.1f}/10")
        st.divider()
        st.subheader("Mood / Energy / Stress Over Time")
        st.line_chart(df.set_index("created_at")[["mood","energy","stress"]].sort_index())
        st.subheader("Sleep Hours")
        st.bar_chart(df.set_index("created_at")["sleep_hours"].sort_index())
        with st.expander("Raw Data"):
            st.dataframe(df, use_container_width=True)

# ── Journal ────────────────────────────────────────────────
with tab2:
    journals = api_get("/journal")
    if not journals:
        st.info("No journal entries yet.")
    else:
        df_j = pd.DataFrame(journals)
        st.dataframe(df_j[["id","title","mood","created_at"]], use_container_width=True)
        st.subheader("Mood Distribution")
        st.bar_chart(df_j["mood"].value_counts())

# ── To-Do ──────────────────────────────────────────────────
with tab3:
    todos = api_get("/todos")
    if not todos:
        st.info("No todos yet.")
    else:
        df_t = pd.DataFrame(todos)
        done   = df_t[df_t["done"] == True]
        active = df_t[df_t["done"] == False]
        c1, c2 = st.columns(2)
        c1.metric("Active Tasks",    len(active))
        c2.metric("Completed Tasks", len(done))
        st.dataframe(df_t[["id","title","category","priority","done"]], use_container_width=True)

# ── Tracking ───────────────────────────────────────────────
with tab4:
    tracking = api_get("/tracking/today")
    if tracking and isinstance(tracking, dict):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Sleep",      f"{tracking.get('sleep',0)}h")
        c2.metric("Exercise",   f"{tracking.get('exercise',0)}min")
        c3.metric("Water",      f"{tracking.get('water',0)} glasses")
        c4.metric("Heart Rate", f"{tracking.get('heart_rate',0)} bpm")
        c5.metric("Meditation", f"{tracking.get('meditation',0)}min")
    else:
        st.info("No tracking data for today.")

# ── Products ───────────────────────────────────────────────
with tab5:
    st.subheader("🛍️ Product Management")

    products = api_get("/products/all")

    # Add new product
    with st.expander("➕ Add New Product", expanded=False):
        with st.form("add_product"):
            c1, c2 = st.columns(2)
            name     = c1.text_input("Product Name *")
            emoji    = c2.text_input("Emoji", value="🛍️")
            desc     = st.text_area("Description")
            c3, c4, c5 = st.columns(3)
            price    = c3.number_input("Price ($)", min_value=0.0, step=0.01)
            orig     = c4.number_input("Original Price ($)", min_value=0.0, step=0.01)
            discount = c5.number_input("Discount (%)", min_value=0, max_value=100, step=1)
            c6, c7, c8 = st.columns(3)
            category = c6.selectbox("Category", ["Wellness","Fitness","Health","Technology","Nutrition"])
            rating   = c7.number_input("Rating", min_value=0.0, max_value=5.0, value=5.0, step=0.1)
            stock    = c8.number_input("Stock", min_value=0, value=100)
            active   = st.checkbox("Active", value=True)

            if st.form_submit_button("Add Product"):
                if not name:
                    st.error("Product name is required.")
                else:
                    result = api_post("/products", {
                        "name": name, "description": desc, "price": price,
                        "orig_price": orig if orig > 0 else None,
                        "discount": discount, "emoji": emoji,
                        "category": category, "rating": rating,
                        "stock": stock, "active": active,
                    })
                    if result:
                        st.success(f"✅ Product '{name}' added!")
                        st.rerun()
                    else:
                        st.error("Failed to add product.")

    # Product list
    if not products:
        st.info("No products yet. Add one above.")
    else:
        df_p = pd.DataFrame(products)
        st.write(f"**{len(df_p)} products total** ({df_p['active'].sum()} active)")

        for _, row in df_p.iterrows():
            with st.container():
                c1, c2, c3, c4, c5, c6 = st.columns([1,3,2,2,1,1])
                c1.write(row.get("emoji","🛍️"))
                c2.write(f"**{row['name']}**\n{row.get('description','')[:50]}")
                c3.write(f"${row['price']:.2f}" + (f" ~~${row['orig_price']:.2f}~~" if row.get('orig_price') else ""))
                c4.write(f"{row.get('category','')} | ⭐{row.get('rating',0)}")
                c5.write("✅" if row.get("active") else "❌")

                with c6:
                    col_edit, col_del = st.columns(2)
                    if col_del.button("🗑️", key=f"del_{row['id']}"):
                        if api_delete(f"/products/{row['id']}"):
                            st.success("Deleted!")
                            st.rerun()

                # Edit form
                with st.expander(f"✏️ Edit {row['name']}", expanded=False):
                    with st.form(f"edit_{row['id']}"):
                        ec1, ec2 = st.columns(2)
                        e_name  = ec1.text_input("Name", value=row["name"])
                        e_emoji = ec2.text_input("Emoji", value=row.get("emoji","🛍️"))
                        e_desc  = st.text_area("Description", value=row.get("description",""))
                        ec3, ec4, ec5 = st.columns(3)
                        e_price = ec3.number_input("Price", value=float(row["price"]), step=0.01)
                        e_orig  = ec4.number_input("Orig Price", value=float(row.get("orig_price") or 0), step=0.01)
                        e_disc  = ec5.number_input("Discount %", value=int(row.get("discount",0)))
                        ec6, ec7, ec8 = st.columns(3)
                        e_cat   = ec6.selectbox("Category", ["Wellness","Fitness","Health","Technology","Nutrition"],
                                                index=["Wellness","Fitness","Health","Technology","Nutrition"].index(row.get("category","Wellness")))
                        e_rate  = ec7.number_input("Rating", value=float(row.get("rating",5.0)), step=0.1)
                        e_stock = ec8.number_input("Stock", value=int(row.get("stock",100)))
                        e_active = st.checkbox("Active", value=bool(row.get("active",True)))

                        if st.form_submit_button("Save Changes"):
                            result = api_put(f"/products/{row['id']}", {
                                "name": e_name, "description": e_desc, "price": e_price,
                                "orig_price": e_orig if e_orig > 0 else None,
                                "discount": e_disc, "emoji": e_emoji,
                                "category": e_cat, "rating": e_rate,
                                "stock": e_stock, "active": e_active,
                            })
                            if result:
                                st.success("✅ Updated!")
                                st.rerun()

                st.divider()

# ── Users ──────────────────────────────────────────────────
with tab6:
    st.subheader("👥 User Management")
    users = api_get("/users")
    if not users:
        st.info("No users yet.")
    else:
        df_u = pd.DataFrame(users)
        st.write(f"**{len(df_u)} users total**")
        st.dataframe(df_u[["id","email","username","role","created_at"]], use_container_width=True)
