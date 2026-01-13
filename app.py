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
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    .review-card { background: #f8fafc; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin-bottom: 10px; }
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
    if df.empty or 'Invoice_ID' not in df.columns: return "0001"
    try:
        last_inv = pd.to_numeric(df['Invoice_ID'], errors='coerce').max()
        return f"{int(last_inv) + 1:04d}" if not pd.isna(last_inv) else "0001"
    except: return f"{len(df) + 1:04d}"

# ========================================================
# STEP 3: SESSION STATE INITIALIZATION
# ========================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = {}
if 'cart' not in st.session_state: st.session_state.cart = []
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "🏠 Dashboard"
if 'edit_mode' not in st.session_state: st.session_state.edit_mode = False
if 'edit_vals' not in st.session_state: st.session_state.edit_vals = {}
if 'show_review' not in st.session_state: st.session_state.show_review = False

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
u_data = st.session_state.user_data
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
    st.session_state.clear(); st.rerun()

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
            st.subheader("🎯 Selection")
            cats = list(settings_df['Category'].unique())
            def_cat = st.session_state.edit_vals.get('cat', cats[0])
            scat = st.selectbox("Category", cats, index=cats.index(def_cat) if def_cat in cats else 0)
            
            cat_items = settings_df[settings_df['Category'] == scat]
            prods = list(cat_items['Product Name'].unique())
            def_prod = st.session_state.edit_vals.get('prod', prods[0])
            sprod = st.selectbox("Product Name", prods, index=prods.index(def_prod) if def_prod in prods else 0)
            
            p_data = cat_items[cat_items['Product Name'] == sprod].iloc[0]
            all_colors = [c.strip() for c in str(p_data['Colors']).split(',') if c.strip()]
            color_options = [c.split(':')[0] for c in all_colors]
            def_shade = st.session_state.edit_vals.get('shade', color_options[0] if color_options else "")
            selected_color = st.selectbox("Select Shade", color_options, index=color_options.index(def_shade) if def_shade in color_options else 0)
            
            valid_packs = [p for p in ["20kg", "Gallon", "Quarter"] if float(p_data.get(f"Price_{p}", 0)) > 0]
            def_pack = st.session_state.edit_vals.get('pack', valid_packs[0] if valid_packs else "")
            packing = st.radio("Select Size", valid_packs, index=valid_packs.index(def_pack) if def_pack in valid_packs else 0, horizontal=True)
            
            price = float(p_data.get(f"Price_{packing}", 0))
            st.info(f"Rate: Rs. {price}")
            qty = st.number_input("Quantity", 1, 500, int(st.session_state.edit_vals.get('qty', 1)))
            
            if st.button("Update Item 🔄" if st.session_state.edit_mode else "Add to List 🛒", use_container_width=True):
                st.session_state.cart.append({
                    "Product": f"{sprod} ({packing})", "Shade": selected_color, "Qty": qty, 
                    "Price": price, "Total": price * qty, "raw_prod": sprod, "raw_pack": packing, "raw_cat": scat
                })
                st.session_state.edit_mode = False; st.session_state.edit_vals = {}; st.rerun()

        with col_cart:
            st.subheader("📋 Order Review")
            if not st.session_state.cart: st.info("Cart is empty.")
            else:
                total_bill = 0
                for i, itm in enumerate(st.session_state.cart):
                    total_bill += itm['Total']
                    c_det, c_edit, c_del = st.columns([3, 1, 1])
                    c_det.write(f"**{itm['Product']}**\n{itm['Shade']} | {itm['Qty']}x")
                    if c_edit.button("✏️", key=f"ed_{i}"):
                        st.session_state.edit_mode = True
                        st.session_state.edit_vals = {'cat': itm['raw_cat'], 'prod': itm['raw_prod'], 'pack': itm['raw_pack'], 'shade': itm['Shade'], 'qty': itm['Qty']}
                        st.session_state.cart.pop(i); st.rerun()
                    if c_del.button("❌", key=f"del_{i}"): st.session_state.cart.pop(i); st.rerun()
                
                st.divider(); st.markdown(f"### Total: Rs. {total_bill}")
                pay_type = st.selectbox("Payment", ["COD", "JazzCash", "EasyPaisa"])
                receipt_b64 = ""
                if pay_type != "COD":
                    r_file = st.file_uploader("Receipt", type=['jpg','png'])
                    if r_file: receipt_b64 = f"data:image/png;base64,{base64.b64encode(r_file.read()).decode()}"

                if st.button("Finalize Order ✅", use_container_width=True, type="primary"):
                    if pay_type != "COD" and not receipt_b64: st.error("Upload Receipt!")
                    else: st.session_state.show_review = True

    # --- THE REVIEW DIALOG ---
    if st.session_state.show_review:
        @st.dialog("📋 Confirm Order")
        def review_dialog():
            st.write("Summary:")
            for itm in st.session_state.cart:
                st.write(f"- {itm['Qty']}x {itm['Product']} ({itm['Shade']})")
            st.write(f"**Total Bill: Rs. {total_bill}**")
            st.write(f"Payment: {pay_type}")
            if st.button("Confirm & Submit ✅", use_container_width=True, type="primary"):
                inv_no = get_next_invoice(orders_df)
                all_p = ", ".join([f"{x['Qty']}x {x['Product']} ({x['Shade']})" for x in st.session_state.cart])
                requests.post(SCRIPT_URL, json={"action":"order", "invoice_id":inv_no, "name":u_name, "phone":raw_ph, "product":all_p, "bill":total_bill, "payment_method":pay_type, "receipt": receipt_b64})
                st.session_state.cart = []; st.session_state.show_review = False; st.success("Success!"); time.sleep(1); set_nav("🏠 Dashboard")
        review_dialog()

elif menu == "📜 History":
    st.header("📜 History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    if not u_ords.empty:
        for _, row in u_ords.iloc[::-1].iterrows():
            st.markdown(f"<div class='review-card'><b>#{row['Invoice_ID']}</b><br>{row['Product']}<br>Rs. {row['Bill']} - {row['Status']}</div>", unsafe_allow_html=True)

elif menu == "🔐 Admin":
    st.header("🛡️ Admin")
    t1, t2, t3 = st.tabs(["Orders", "Users", "Feedback"])
    with t1:
        for idx, row in orders_df.iterrows():
            with st.expander(f"{row['Invoice_ID']} - {row['Name']}"):
                st.write(f"Details: {row['Product']}"); st.write(f"Bill: {row['Bill']}")
                if st.button("Mark Paid", key=f"adm_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']}); st.rerun()
    with t2: st.dataframe(users_df)
    with t3: st.dataframe(feedback_df)

elif menu == "👤 Profile":
    st.header("👤 Profile")
    st.write(f"Name: {u_name}"); st.write(f"Phone: {raw_ph}")
    up_file = st.file_uploader("Photo", type=['jpg','png'])
    if up_file and st.button("Save"):
        b64 = base64.b64encode(up_file.read()).decode()
        requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":raw_ph, "photo":f"data:image/png;base64,{b64}"})
        st.success("Updated!"); time.sleep(1); st.rerun()

elif menu == "💬 Feedback":
    st.header("💬 Feedback")
    f_msg = st.text_area("Message")
    if st.button("Submit"):
        requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":raw_ph, "message":f_msg})
        st.success("Sent!")
