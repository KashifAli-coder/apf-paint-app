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

# Custom Global CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- Invoice Generator Function (Defined Early to avoid Line 182 error) ---
def get_next_invoice(df):
    if df is None or df.empty or 'Invoice_ID' not in df.columns:
        return "0001"
    try:
        # Convert to numeric, handle errors, find max
        last_val = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        if pd.isna(last_val): return "0001"
        return f"{int(last_val) + 1:04d}"
    except:
        return f"{len(df) + 1:04d}"

# ========================================================
# STEP 2: DATA LOADING
# ========================================================
@st.cache_data(ttl=0)
def load_all_data():
    try:
        t = int(time.time())
        base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&t={t}&sheet="
        u = pd.read_csv(base + "Users").fillna('')
        s = pd.read_csv(base + "Settings").fillna('')
        o = pd.read_csv(base + "Orders").fillna('')
        f = pd.read_csv(base + "Feedback").fillna('')
        return u, s, o, f
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

users_df, settings_df, orders_df, feedback_df = load_all_data()

def normalize_ph(n):
    s = str(n).strip().split('.')[0]
    if s and not s.startswith('0'): return '0' + s
    return s

# ========================================================
# STEP 3: SESSION STATE
# ========================================================
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_data': {}, 'cart': [], 'menu_choice': "🏠 Dashboard"})

def set_nav(target):
    st.session_state.menu_choice = target
    st.rerun()

# ========================================================
# STEP 4: LOGIN & REGISTER
# ========================================================
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center;'>🎨 Paint Factory Store</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
        with t1:
            l_ph = st.text_input("Phone", key="login_ph")
            l_pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login 🚀", use_container_width=True):
                u_ph = normalize_ph(l_ph)
                match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
                if not match.empty:
                    user_row = match.iloc[0]
                    if str(user_row['Role']).lower() == 'pending': st.warning("Awaiting Approval")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_row.to_dict()
                        st.rerun()
                else: st.error("Invalid Credentials")
        with t2:
            r_name = st.text_input("Full Name", key="reg_name")
            r_ph = st.text_input("Phone Number", key="reg_ph")
            r_pw = st.text_input("Set Password", type="password", key="reg_pw")
            if st.button("Create Account ✨", use_container_width=True):
                requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
                st.success("Registration Sent! Wait for Admin Approval.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR
# ========================================================
u_data = st.session_state.get('user_data', {})
u_name = u_data.get('Name', 'User')
raw_ph = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', '')
sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan' and u_photo != '') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"

st.sidebar.markdown(f'<div style="text-align:center; padding: 20px;"><img src="{sidebar_img}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:3px solid #3b82f6; box-shadow: 0 4px 10px rgba(0,0,0,0.1);"></div>', unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align:center;'>{u_name}</h3>", unsafe_allow_html=True)

nav_options = {"🏠 Dashboard": "🏠 Dashboard", "👤 Profile": "👤 Profile", "🛍️ New Order": "🛍️ New Order", "📜 History": "📜 History", "💬 Feedback": "💬 Feedback"}
for label, target in nav_options.items():
    if st.sidebar.button(label, use_container_width=True): set_nav(target)

if raw_ph == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin Panel", use_container_width=True): set_nav("🔐 Admin")

st.sidebar.divider()
if st.sidebar.button("Logout 🚪", use_container_width=True):
    st.session_state.clear()
    st.rerun()

menu = st.session_state.menu_choice

# ========================================================
# STEP 6: MODULES
# ========================================================

if menu == "🏠 Dashboard":
    st.markdown(f"## 🏠 Welcome back, {u_name}!")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    total_spent = u_ords['Bill'].sum() if not u_ords.empty else 0
    st.markdown(f"""
        <div style="display: flex; gap: 15px; margin-bottom: 25px;">
            <div style="flex:1; background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 20px; border-radius: 15px; text-align: center;">
                <h4 style="margin:0; opacity: 0.8; font-size: 14px;">TOTAL ORDERS</h4>
                <p style="font-size: 28px; font-weight: bold; margin: 5px 0;">{len(u_ords)}</p>
            </div>
            <div style="flex:1; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 20px; border-radius: 15px; text-align: center;">
                <h4 style="margin:0; opacity: 0.8; font-size: 14px;">TOTAL SPENT</h4>
                <p style="font-size: 28px; font-weight: bold; margin: 5px 0;">Rs. {total_spent}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

elif menu == "🛍️ New Order":
    st.header("🛍️ Create New Order")
    if not settings_df.empty:
        col_sel, col_cart = st.columns([1.5, 1])
        with col_sel:
            scat = st.selectbox("Category", settings_df['Category'].unique())
            cat_items = settings_df[settings_df['Category'] == scat]
            sprod = st.selectbox("Product Name", cat_items['Product Name'].unique())
            p_data = cat_items[cat_items['Product Name'] == sprod].iloc[0]
            
            # Special Rate Color Logic
            all_colors_raw = [c.strip() for c in str(p_data['Colors']).split(',')]
            oos_colors = [c.strip() for c in str(p_data.get('Out_of_Stock_Colors', '')).split(',')]
            available_colors = [c for c in all_colors_raw if c.split(':')[0] not in oos_colors and c != '']
            color_options = [c.split(':')[0] for c in available_colors]
            selected_color_name = st.selectbox("Select Shade", color_options)
            
            extra_charge = 0
            for c in available_colors:
                if c.startswith(selected_color_name) and ":" in c:
                    extra_charge = float(c.split(':')[-1].replace('+', ''))

            # Packing
            valid_packs = []
            for p in ["20kg", "Gallon", "Quarter"]:
                if float(p_data.get(f"Price_{p}", 0)) > 0: valid_packs.append(p)
            
            packing = st.radio("Select Size", valid_packs, horizontal=True)
            base_price = float(p_data.get(f"Price_{packing}", 0))
            final_unit_price = base_price + extra_charge
            
            st.info(f"Unit Rate: Rs. {final_unit_price}")
            qty = st.number_input("Quantity", 1, 500, 1)
            
            if st.button("Add to List 🛒", use_container_width=True):
                st.session_state.cart.append({"Product": f"{sprod} ({packing})", "Shade": selected_color_name, "Qty": qty, "Price": final_unit_price, "Total": final_unit_price * qty})
                st.rerun()

        with col_cart:
            st.markdown("<div style='background:white; padding:20px; border-radius:15px; border:1px solid #ddd;'>", unsafe_allow_html=True)
            st.subheader("📋 Review Order")
            if not st.session_state.cart: st.info("Cart is empty.")
            else:
                total_bill = 0
                for i, itm in enumerate(st.session_state.cart):
                    total_bill += itm['Total']
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{itm['Product']}**\n{itm['Shade']} | {itm['Qty']}x")
                    if c2.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                st.divider()
                st.subheader(f"Total: Rs. {total_bill}")
                if st.button("Clear All"):
                    st.session_state.cart = []
                    st.rerun()
                
                pay_type = st.selectbox("Payment", ["COD", "JazzCash", "EasyPaisa", "Bank Transfer"])
                receipt_b64 = ""
                if pay_type != "COD":
                    r_file = st.file_uploader("Receipt", type=['jpg','png'])
                    if r_file: receipt_b64 = f"data:image/png;base64,{base64.b64encode(r_file.read()).decode()}"

                if st.button("Finalize Order ✅", use_container_width=True, type="primary"):
                    if pay_type != "COD" and not receipt_b64: st.error("Upload receipt!")
                    else:
                        inv_no = get_next_invoice(orders_df)
                        all_prods = ", ".join([f"{x['Qty']}x {x['Product']} ({x['Shade']})" for x in st.session_state.cart])
                        requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv_no, "name":u_name, "phone":raw_ph, "product":all_prods, "bill":total_bill, "payment_method":pay_type, "receipt": receipt_b64})
                        st.session_state.cart = []
                        st.success(f"Order #{inv_no} Successful!")
                        time.sleep(1); set_nav("🏠 Dashboard")
            st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📜 History":
    st.header("📜 Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    if not u_ords.empty:
        for _, row in u_ords.iloc[::-1].iterrows():
            st.markdown(f"""<div style="background:white; padding:15px; border-radius:12px; margin-bottom:10px; border-left:5px solid #3b82f6;">
                <b>Invoice: {row['Invoice_ID']}</b> | Status: {row['Status']}<br>
                {row['Product']}<br><b>Rs. {row['Bill']}</b></div>""", unsafe_allow_html=True)

elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    t1, t2 = st.tabs(["Orders", "Users"])
    with t1: st.dataframe(orders_df)
    with t2: st.dataframe(users_df)

elif menu == "👤 Profile":
    st.header("👤 Profile")
    st.write(f"Name: {u_name}")
    st.write(f"Phone: {raw_ph}")

elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Your Message")
    if st.button("Submit"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Feedback Sent!")
