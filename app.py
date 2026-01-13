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

# Custom Global CSS for modern look
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# STEP 2: DATA LOADING & FUNCTIONS
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

def get_next_invoice(df):
    if df.empty or 'Invoice_ID' not in df.columns:
        return "0001"
    try:
        last_inv = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        if pd.isna(last_inv): return "0001"
        return f"{int(last_inv) + 1:04d}"
    except:
        return f"{len(df) + 1:04d}"

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
            <div style="flex:1; background: linear-gradient(135deg, #f59e0b, #d97706); color: white; padding: 20px; border-radius: 15px; text-align: center;">
                <h4 style="margin:0; opacity: 0.8; font-size: 14px;">STATUS</h4>
                <p style="font-size: 20px; font-weight: bold; margin: 12px 0;">Verified ✅</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("🆕 Recent Activity")
    if not u_ords.empty:
        for _, row in u_ords.tail(3).iloc[::-1].iterrows():
            st.markdown(f"""
                <div style="background: white; padding: 15px; border-radius: 12px; margin-bottom: 10px; border: 1px solid #e5e7eb; display: flex; justify-content: space-between;">
                    <div><b>{row['Product']}</b><br><small style='color:gray;'>Invoice: {row['Invoice_ID']}</small></div>
                    <div style='text-align:right;'><b>Rs. {row['Bill']}</b><br><span style='color:#3b82f6; font-size:12px;'>● {row['Status']}</span></div>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("No recent orders.")

elif menu == "🛍️ New Order":
    st.header("🛍️ Create New Order")
    if not settings_df.empty:
        col_sel, col_cart = st.columns([1.5, 1])
        with col_sel:
            st.subheader("🎯 Selection")
            scat = st.selectbox("Category", settings_df['Category'].unique())
            cat_items = settings_df[settings_df['Category'] == scat]
            sprod = st.selectbox("Product Name", cat_items['Product Name'].unique())
            p_data = cat_items[cat_items['Product Name'] == sprod].iloc[0]
            
            all_colors_raw = [c.strip() for c in str(p_data['Colors']).split(',')]
            oos_colors = [c.strip() for c in str(p_data.get('Out_of_Stock_Colors', '')).split(',')]
            available_colors = [c for c in all_colors_raw if c.split(':')[0] not in oos_colors and c != '']
            color_options = [c.split(':')[0] for c in available_colors]
            selected_color_name = st.selectbox("Select Shade", color_options)
            
            extra_charge = 0
            for c in available_colors:
                if c.startswith(selected_color_name) and ":" in c:
                    extra_charge = float(c.split(':')[-1].replace('+', ''))

            valid_packs = []
            for p in ["20kg", "Gallon", "Quarter"]:
                if float(p_data.get(f"Price_{p}", 0)) > 0: valid_packs.append(p)
            
            packing = st.radio("Select Size", valid_packs, horizontal=True)
            base_price = float(p_data.get(f"Price_{packing}", 0))
            final_unit_price = base_price + extra_charge
            
            st.markdown(f"""<div style="background:#e1effe; padding:15px; border-radius:10px; border-left:5px solid #3b82f6;">
                <h3 style="margin:0; color:#1e40af;">Rate: Rs. {final_unit_price}</h3>
                {"<small style='color:red;'>+ Special Color Rate Applied</small>" if extra_charge > 0 else ""}
            </div>""", unsafe_allow_html=True)
            
            qty = st.number_input("Quantity", 1, 500, 1)
            if st.button("Add to List 🛒", use_container_width=True):
                st.session_state.cart.append({"Product": f"{sprod} ({packing})", "Shade": selected_color_name, "Qty": qty, "Price": final_unit_price, "Total": final_unit_price * qty})
                st.rerun()

        with col_cart:
            st.markdown("<div style='background:white; padding:20px; border-radius:15px; border:1px solid #ddd;'>", unsafe_allow_html=True)
            st.subheader("📋 Order Review")
            if not st.session_state.cart: st.info("Cart is empty.")
            else:
                total_bill = 0
                for i, itm in enumerate(st.session_state.cart):
                    total_bill += itm['Total']
                    c_det, c_del = st.columns([4, 1])
                    c_det.markdown(f"**{itm['Product']}**\n{itm['Shade']} | {itm['Qty']}x")
                    if c_del.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                st.divider()
                st.write(f"### Total: Rs. {total_bill}")
                if st.button("Clear All"):
                    st.session_state.cart = []
                    st.rerun()
                
                pay_type = st.selectbox("Payment", ["COD", "JazzCash", "EasyPaisa", "Bank Transfer"])
                receipt_b64 = ""
                if pay_type != "COD":
                    r_file = st.file_uploader("Receipt Screenshot", type=['jpg','png','jpeg'])
                    if r_file: receipt_b64 = f"data:image/png;base64,{base64.b64encode(r_file.read()).decode()}"

                if st.button("Finalize Order ✅", use_container_width=True, type="primary"):
                    if pay_type != "COD" and not receipt_b64: st.error("Please upload receipt!")
                    else:
                        inv_no = get_next_invoice(orders_df)
                        all_prods = ", ".join([f"{x['Qty']}x {x['Product']} ({x['Shade']})" for x in st.session_state.cart])
                        requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv_no, "name":u_name, "phone":raw_ph, "product":all_prods, "bill":total_bill, "payment_method":pay_type, "receipt": receipt_b64})
                        st.session_state.cart = []
                        st.success(f"Order #{inv_no} Successful!"); time.sleep(1); set_nav("🏠 Dashboard")
            st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📜 History":
    st.header("📜 My Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    if not u_ords.empty:
        for _, row in u_ords.iloc[::-1].iterrows():
            status = str(row['Status'])
            st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 15px; margin-bottom: 12px; border-left: 6px solid {'#10b981' if 'Paid' in status else '#f59e0b'}; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: gray; font-size: 12px;">#{row['Invoice_ID']}</span>
                        <span style="background: {'#dcfce7' if 'Paid' in status else '#fef3c7'}; color: {'#166534' if 'Paid' in status else '#92400e'}; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: bold;">{status}</span>
                    </div>
                    <h4 style="margin: 10px 0;">{row['Product']}</h4>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <b style="color: #3b82f6; font-size: 18px;">Rs. {row['Bill']}</b>
                        <span style="color: gray; font-size: 12px;">📅 {str(row['Timestamp'])[:16]}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("No orders yet.")

elif menu == "🔐 Admin":
    st.header("🛡️ Admin Panel")
    t1, t2, t3 = st.tabs(["📦 Orders", "👥 Users", "💬 Feedback"])
    with t1:
        for idx, row in orders_df.iterrows():
            with st.expander(f"{row['Invoice_ID']} - {row['Name']} (Rs. {row['Bill']})"):
                st.write(f"Items: {row['Product']}")
                if 'Receipt' in row and row['Receipt'] and str(row['Receipt']).startswith("data:image"):
                    st.image(row['Receipt'], caption="Payment Proof", width=300)
                if "Paid" not in str(row['Status']):
                    if st.button("Mark Paid", key=f"adm_p_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                        st.rerun()
    with t2:
        st.dataframe(users_df, use_container_width=True)
    with t3:
        st.dataframe(feedback_df, use_container_width=True)

elif menu == "👤 Profile":
    st.markdown("### 👤 Profile Settings")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""<div style="background: white; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #ddd;">
                <img src="{sidebar_img}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 10px;">
                <h4>{u_name}</h4><p style="color: gray;">{raw_ph}</p></div>""", unsafe_allow_html=True)
    with c2:
        img_file = st.file_uploader("Change Avatar", type=['jpg','png'])
        if img_file and st.button("Save New Photo"):
            b64 = base64.b64encode(img_file.read()).decode()
            requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":f"data:image/png;base64,{b64}"})
            st.success("Photo Updated!"); time.sleep(1); st.rerun()

elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("How was your experience?")
    if st.button("Submit Review"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Feedback Sent!")
