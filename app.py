import streamlit as st
import pandas as pd
import requests
import time
import base64
from datetime import datetime

# ========================================================
# STEP 1: CONFIGURATION
# ========================================================
SHEET_ID = "1fIOaGMR3-M_t2dtYYuloFH7rSiFha_HDxfO6qaiEmDk"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxnAPNsjMMdi9NZ1_TSv6O7XS-SAx2dXnOCNJr-WE0Z4eeY9xfurGg3zUMhWJbTvSCf/exec"
JAZZCASH_NO = "03005508112"
EASYPAISA_NO = "03005508112"

st.set_page_config(page_title="Paint Pro Store", layout="wide")

# Dashboard Style CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .metric-card { flex:1; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .metric-card-green { flex:1; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .metric-card-orange { flex:1; background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 20px; border-radius: 15px; text-align: center; }
    .activity-row { background: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; border: 1px solid #e5e7eb; display: flex; justify-content: space-between; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# STEP 2: DATA LOADING
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    try:
        t = int(time.time())
        base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        return pd.read_csv(base + "Users").fillna(''), pd.read_csv(base + "Settings").fillna(''), pd.read_csv(base + "Orders").fillna(''), pd.read_csv(base + "Feedback").fillna('')
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_df, settings_df, orders_df, feedback_df = load_all_data()

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    return '0' + s if s and not s.startswith('0') else s

def get_next_invoice(df):
    try:
        valid_ids = pd.to_numeric(df['Invoice_ID'], errors='coerce').dropna()
        return f"{int(valid_ids.max()) + 1:04d}" if not valid_ids.empty else "0001"
    except: return "0001"

# ========================================================
# STEP 3: SESSION STATE (WIZARD LOGIC)
# ========================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = {}
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "🏠 Dashboard"
# Wizard states
if 'show_order_wizard' not in st.session_state: st.session_state.show_order_wizard = False
if 'wizard_step' not in st.session_state: st.session_state.wizard_step = 1
if 'temp_order' not in st.session_state: st.session_state.temp_order = {}

def set_nav(target):
    st.session_state.menu_choice = target
    st.rerun()

# ========================================================
# STEP 4: LOGIN (Keeping Original)
# ========================================================
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center;'>🎨 Paint Factory</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
        with t1:
            l_ph = st.text_input("Phone")
            l_pw = st.text_input("Password", type="password")
            if st.button("Login 🚀", use_container_width=True):
                u_ph = normalize_ph(l_ph)
                match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Login")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR & NAV
# ========================================================
u_data = st.session_state.user_data
u_name, u_phone = u_data.get('Name', 'User'), normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', "https://cdn-icons-png.flaticon.com/512/149/149071.png")

st.sidebar.image(u_photo if str(u_photo) != 'nan' else "https://cdn-icons-png.flaticon.com/512/149/149071.png", width=100)
st.sidebar.markdown(f"### {u_name}")

if st.sidebar.button("🏠 Dashboard", use_container_width=True): set_nav("🏠 Dashboard")
# Special "New Order" Button that triggers Popup
if st.sidebar.button("🛍️ New Order", use_container_width=True, type="primary"):
    st.session_state.show_order_wizard = True
    st.session_state.wizard_step = 1
    st.rerun()

if st.sidebar.button("📜 History", use_container_width=True): set_nav("📜 History")
if st.sidebar.button("👤 Profile", use_container_width=True): set_nav("👤 Profile")
if u_phone == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin Panel", use_container_width=True): set_nav("🔐 Admin")
if st.sidebar.button("Logout 🚪", use_container_width=True):
    st.session_state.clear(); st.rerun()

# ========================================================
# STEP 6: ORDER WIZARD DIALOG (THE POPUP)
# ========================================================
if st.session_state.show_order_wizard:
    @st.dialog("🎯 Create New Order")
    def order_wizard():
        step = st.session_state.wizard_step
        
        # PROGRESS BAR
        st.progress(step / 4)
        
        if step == 1:
            st.subheader("Step 1: Select Product")
            cats = list(settings_df['Category'].unique())
            scat = st.selectbox("Category", cats)
            prods = list(settings_df[settings_df['Category'] == scat]['Product Name'].unique())
            sprod = st.selectbox("Product", prods)
            
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.temp_order.update({"cat": scat, "prod": sprod})
                st.session_state.wizard_step = 2
                st.rerun()

        elif step == 2:
            st.subheader("Step 2: Customization")
            p_data = settings_df[settings_df['Product Name'] == st.session_state.temp_order['prod']].iloc[0]
            
            colors = [c.split(':')[0] for c in str(p_data['Colors']).split(',') if c.strip()]
            shade = st.selectbox("Select Shade", colors)
            
            packs = [p for p in ["20kg", "Gallon", "Quarter"] if float(p_data.get(f"Price_{p}", 0)) > 0]
            size = st.radio("Select Size", packs, horizontal=True)
            qty = st.number_input("Quantity", 1, 500, 1)
            
            u_price = float(p_data.get(f"Price_{size}", 0))
            st.info(f"Unit Price: Rs. {u_price} | Total: Rs. {u_price * qty}")
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.wizard_step = 1; st.rerun()
            if c2.button("Next ➡️"):
                st.session_state.temp_order.update({"shade": shade, "size": size, "qty": qty, "price": u_price, "total": u_price * qty})
                st.session_state.wizard_step = 3
                st.rerun()

        elif step == 3:
            st.subheader("Step 3: Payment")
            method = st.selectbox("Method", ["COD", "JazzCash", "EasyPaisa"])
            receipt_b64 = ""
            if method != "COD":
                img = st.file_uploader("Upload Receipt", type=['jpg','png'])
                if img: receipt_b64 = f"data:image/png;base64,{base64.b64encode(img.read()).decode()}"
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.wizard_step = 2; st.rerun()
            if c2.button("Review Order 🔍"):
                st.session_state.temp_order.update({"method": method, "receipt": receipt_b64})
                st.session_state.wizard_step = 4
                st.rerun()

        elif step == 4:
            st.subheader("Step 4: Final Review")
            o = st.session_state.temp_order
            st.markdown(f"""
                **Items:** {o['qty']}x {o['prod']} ({o['size']})  
                **Shade:** {o['shade']}  
                **Total Bill:** Rs. {o['total']}  
                **Payment:** {o['method']}
            """)
            
            c1, c2 = st.columns(2)
            if c1.button("⬅️ Back"): st.session_state.wizard_step = 3; st.rerun()
            if c2.button("Confirm & Submit ✅", type="primary"):
                inv = get_next_invoice(orders_df)
                prod_str = f"{o['qty']}x {o['prod']} ({o['size']}) [{o['shade']}]"
                requests.post(SCRIPT_URL, json={
                    "action":"order", "invoice_id":inv, "name":u_name, "phone":u_phone, 
                    "product":prod_str, "bill":o['total'], "payment_method":o['method'], "receipt": o['receipt']
                })
                st.session_state.show_order_wizard = False
                st.success("Order Placed!"); time.sleep(1); set_nav("🏠 Dashboard")

    order_wizard()

# ========================================================
# STEP 7: MAIN CONTENT (DASHBOARD & OTHERS)
# ========================================================
menu = st.session_state.menu_choice

if menu == "🏠 Dashboard":
    st.markdown(f"## 🏠 Dashboard Overview")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == u_phone]
    total_spent = u_ords['Bill'].sum() if not u_ords.empty else 0
    
    st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 25px;">
            <div class="metric-card"><h4>ORDERS</h4><p style="font-size:28px;">{len(u_ords)}</p></div>
            <div class="metric-card-green"><h4>SPENT</h4><p style="font-size:28px;">Rs. {total_spent}</p></div>
            <div class="metric-card-orange"><h4>STATUS</h4><p style="font-size:20px;">Active ✅</p></div>
        </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Recent Activity")
    for _, row in u_ords.tail(5).iloc[::-1].iterrows():
        st.markdown(f'<div class="activity-row"><div><b>{row["Product"]}</b></div><div>Rs. {row["Bill"]}</div></div>', unsafe_allow_html=True)

elif menu == "📜 History":
    st.header("📜 Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == u_phone]
    st.dataframe(u_ords.iloc[::-1], use_container_width=True)

elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    st.dataframe(orders_df.iloc[::-1], use_container_width=True)

elif menu == "👤 Profile":
    st.header("👤 Profile")
    st.write(f"Name: {u_name}")
    st.write(f"Phone: {u_phone}")
