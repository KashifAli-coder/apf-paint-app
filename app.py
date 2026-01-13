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

# Custom Global CSS for better UI
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
    .review-card { background: #ffffff; padding: 15px; border-radius: 12px; border-left: 5px solid #3b82f6; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .price-tag { background: #e1effe; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; margin: 15px 0; }
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
        # Filter only numeric invoice IDs to find max
        valid_ids = pd.to_numeric(df['Invoice_ID'], errors='coerce').dropna()
        if valid_ids.empty: return "0001"
        return f"{int(valid_ids.max()) + 1:04d}"
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
# STEP 4: LOGIN & REGISTER MODULE
# ========================================================
if not st.session_state.logged_in:
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("<h1 style='text-align: center;'>🎨 Paint Factory Store</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
        with t1:
            l_ph = st.text_input("Phone Number", key="login_ph")
            l_pw = st.text_input("Password", type="password", key="login_pw")
            if st.button("Login 🚀", use_container_width=True):
                u_ph = normalize_ph(l_ph)
                match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
                if not match.empty:
                    user_row = match.iloc[0]
                    if str(user_row['Role']).lower() == 'pending':
                        st.warning("Your account is awaiting Admin approval.")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_row.to_dict()
                        st.rerun()
                else: st.error("Invalid Phone or Password")
        with t2:
            r_name = st.text_input("Full Name", key="reg_name")
            r_ph = st.text_input("Phone", key="reg_ph")
            r_pw = st.text_input("Set Password", type="password", key="reg_pw")
            if st.button("Create Account ✨", use_container_width=True):
                if r_name and r_ph and r_pw:
                    requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
                    st.success("Registration request sent! Please wait for approval.")
                else: st.error("Please fill all fields.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR & NAVIGATION
# ========================================================
u_data = st.session_state.user_data
u_name = u_data.get('Name', 'User')
u_phone = normalize_ph(u_data.get('Phone', ''))
u_photo = u_data.get('Photo', '')

sidebar_img = u_photo if (u_photo and str(u_photo) != 'nan' and u_photo != '') else "https://cdn-icons-png.flaticon.com/512/149/149071.png"

st.sidebar.markdown(f'''
    <div style="text-align:center; padding: 20px;">
        <img src="{sidebar_img}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:3px solid #3b82f6;">
        <h3 style="margin-top:10px;">{u_name}</h3>
        <p style="color:gray;">{u_phone}</p>
    </div>
''', unsafe_allow_html=True)

nav_btns = {
    "🏠 Dashboard": "🏠 Dashboard",
    "🛍️ New Order": "🛍️ New Order",
    "📜 History": "📜 History",
    "👤 Profile": "👤 Profile",
    "💬 Feedback": "💬 Feedback"
}

for label, target in nav_btns.items():
    if st.sidebar.button(label, use_container_width=True):
        set_nav(target)

if u_phone == normalize_ph(JAZZCASH_NO):
    st.sidebar.divider()
    if st.sidebar.button("🔐 Admin Panel", use_container_width=True, type="primary"):
        set_nav("🔐 Admin")

st.sidebar.divider()
if st.sidebar.button("Logout 🚪", use_container_width=True):
    st.session_state.clear()
    st.rerun()

menu = st.session_state.menu_choice

# ========================================================
# STEP 6: MODULES LOGIC
# ========================================================

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title(f"Welcome, {u_name}!")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == u_phone]
    total_spent = u_ords['Bill'].sum() if not u_ords.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Orders", len(u_ords))
    c2.metric("Total Spent", f"Rs. {total_spent}")
    c3.metric("Account Status", "Verified ✅")
    
    st.subheader("Recent Orders")
    if not u_ords.empty:
        for _, row in u_ords.tail(5).iloc[::-1].iterrows():
            st.markdown(f"""
                <div class='review-card'>
                    <div style='display:flex; justify-content:space-between;'>
                        <b>Order #{row['Invoice_ID']}</b>
                        <span style='color:#3b82f6;'>{row['Status']}</span>
                    </div>
                    <p style='margin:5px 0;'>{row['Product']}</p>
                    <b>Rs. {row['Bill']}</b>
                </div>
            """, unsafe_allow_html=True)
    else: st.info("No orders found yet.")

# --- NEW ORDER (WITH EDIT & REVIEW LOGIC) ---
elif menu == "🛍️ New Order":
    st.title("Create New Order")
    if settings_df.empty:
        st.error("Store settings not loaded. Contact Admin.")
    else:
        col_sel, col_cart = st.columns([1.5, 1])
        
        with col_sel:
            st.subheader("🎯 Selection Area")
            cats = list(settings_df['Category'].unique())
            def_cat = st.session_state.edit_vals.get('cat', cats[0])
            scat = st.selectbox("Select Category", cats, index=cats.index(def_cat) if def_cat in cats else 0)
            
            cat_items = settings_df[settings_df['Category'] == scat]
            prods = list(cat_items['Product Name'].unique())
            def_prod = st.session_state.edit_vals.get('prod', prods[0])
            sprod = st.selectbox("Select Product", prods, index=prods.index(def_prod) if def_prod in prods else 0)
            
            p_data = cat_items[cat_items['Product Name'] == sprod].iloc[0]
            
            all_colors = [c.strip() for c in str(p_data['Colors']).split(',') if c.strip()]
            color_names = [c.split(':')[0] for c in all_colors]
            def_shade = st.session_state.edit_vals.get('shade', color_names[0] if color_names else "")
            selected_shade = st.selectbox("Select Shade", color_names, index=color_names.index(def_shade) if def_shade in color_names else 0)
            
            valid_packs = [p for p in ["20kg", "Gallon", "Quarter"] if float(p_data.get(f"Price_{p}", 0)) > 0]
            def_pack = st.session_state.edit_vals.get('pack', valid_packs[0] if valid_packs else "")
            packing = st.radio("Select Size", valid_packs, index=valid_packs.index(def_pack) if def_pack in valid_packs else 0, horizontal=True)
            
            u_price = float(p_data.get(f"Price_{packing}", 0))
            st.markdown(f"<div class='price-tag'><h3>Unit Price: Rs. {u_price}</h3></div>", unsafe_allow_html=True)
            
            def_qty = st.session_state.edit_vals.get('qty', 1)
            qty = st.number_input("Quantity", 1, 500, int(def_qty))
            
            if st.button("Update Item 🔄" if st.session_state.edit_mode else "Add to List 🛒", use_container_width=True):
                st.session_state.cart.append({
                    "Product": f"{sprod} ({packing})", "Shade": selected_shade, "Qty": qty, 
                    "Price": u_price, "Total": u_price * qty, "raw_prod": sprod, "raw_pack": packing, "raw_cat": scat
                })
                st.session_state.edit_mode = False; st.session_state.edit_vals = {}; st.rerun()

        with col_cart:
            st.subheader("📋 Your Cart")
            if not st.session_state.cart:
                st.info("Your cart is empty. Add products to proceed.")
            else:
                total_bill = 0
                for i, itm in enumerate(st.session_state.cart):
                    total_bill += itm['Total']
                    c_det, c_edit, c_del = st.columns([3, 1, 1])
                    c_det.markdown(f"**{itm['Product']}**\n{itm['Shade']} | {itm['Qty']}x")
                    
                    if c_edit.button("✏️", key=f"ed_{i}"):
                        st.session_state.edit_mode = True
                        st.session_state.edit_vals = {'cat': itm['raw_cat'], 'prod': itm['raw_prod'], 'pack': itm['raw_pack'], 'shade': itm['Shade'], 'qty': itm['Qty']}
                        st.session_state.cart.pop(i); st.rerun()
                        
                    if c_del.button("❌", key=f"del_{i}"):
                        st.session_state.cart.pop(i); st.rerun()
                
                st.divider()
                st.write(f"### Grand Total: Rs. {total_bill}")
                
                if st.button("Clear All Cart 🗑️", use_container_width=True):
                    st.session_state.cart = []; st.rerun()
                
                st.divider()
                pay_type = st.selectbox("Payment Method", ["COD", "JazzCash", "EasyPaisa"])
                receipt_img = ""
                if pay_type != "COD":
                    r_file = st.file_uploader("Upload Receipt Proof", type=['jpg','png'])
                    if r_file: receipt_img = f"data:image/png;base64,{base64.b64encode(r_file.read()).decode()}"

                if st.button("Finalize Order ✅", use_container_width=True, type="primary"):
                    if pay_type != "COD" and not receipt_img:
                        st.error("Please upload payment receipt first!")
                    else: st.session_state.show_review = True

    # --- REVIEW DIALOG (FINAL STEP) ---
    if st.session_state.show_review:
        @st.dialog("Final Confirmation")
        def confirm_order():
            st.warning("Please review your items carefully.")
            for itm in st.session_state.cart:
                st.write(f"🔹 {itm['Qty']}x {itm['Product']} - {itm['Shade']}")
            st.markdown(f"**Total Bill: Rs. {total_bill}**")
            st.write(f"Payment Method: {pay_type}")
            
            col1, col2 = st.columns(2)
            if col1.button("Cancel", use_container_width=True):
                st.session_state.show_review = False; st.rerun()
            if col2.button("Confirm & Order", use_container_width=True, type="primary"):
                inv_no = get_next_invoice(orders_df)
                all_items_str = ", ".join([f"{x['Qty']}x {x['Product']} ({x['Shade']})" for x in st.session_state.cart])
                requests.post(SCRIPT_URL, json={
                    "action":"order", "invoice_id":inv_no, "name":u_name, "phone":u_phone, 
                    "product":all_items_str, "bill":total_bill, "payment_method":pay_type, "receipt": receipt_img
                })
                st.session_state.cart = []; st.session_state.show_review = False
                st.success(f"Order #{inv_no} Placed Successfully!"); time.sleep(1); set_nav("🏠 Dashboard")
        confirm_order()

# --- HISTORY ---
elif menu == "📜 History":
    st.title("Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == u_phone]
    if u_ords.empty:
        st.info("You haven't placed any orders yet.")
    else:
        for _, row in u_ords.iloc[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                    <div class='review-card'>
                        <small>{row['Timestamp']}</small>
                        <h4>Invoice #{row['Invoice_ID']}</h4>
                        <p>{row['Product']}</p>
                        <div style='display:flex; justify-content:space-between;'>
                            <b>Rs. {row['Bill']}</b>
                            <span style='background:#dcfce7; color:#166534; padding:2px 10px; border-radius:10px;'>{row['Status']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# --- ADMIN PANEL ---
elif menu == "🔐 Admin":
    st.title("🛡️ Administrative Control")
    t1, t2, t3 = st.tabs(["Manage Orders", "User Approvals", "Feedback Logs"])
    
    with t1:
        st.subheader("Pending & Recent Orders")
        for idx, row in orders_df.iloc[::-1].iterrows():
            with st.expander(f"Order #{row['Invoice_ID']} - {row['Name']}"):
                st.write(f"Items: {row['Product']}")
                st.write(f"Bill: Rs. {row['Bill']}")
                st.write(f"Payment: {row['Payment_Method']}")
                if 'Receipt' in row and row['Receipt'] and str(row['Receipt']).startswith("data:image"):
                    st.image(row['Receipt'], width=300, caption="User's Payment Receipt")
                if "Paid" not in str(row['Status']):
                    if st.button("Mark as Paid ✅", key=f"paid_{idx}"):
                        requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                        st.success("Order Updated!"); time.sleep(0.5); st.rerun()
    
    with t2:
        st.subheader("All Registered Users")
        st.dataframe(users_df, use_container_width=True)
    
    with t3:
        st.subheader("Customer Reviews")
        st.dataframe(feedback_df, use_container_width=True)

# --- PROFILE ---
elif menu == "👤 Profile":
    st.title("My Profile Settings")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.image(sidebar_img, width=200)
    with c2:
        st.write(f"**Name:** {u_name}")
        st.write(f"**Phone:** {u_phone}")
        new_photo = st.file_uploader("Change Profile Picture", type=['png','jpg'])
        if new_photo and st.button("Update Photo"):
            b64_img = f"data:image/png;base64,{base64.b64encode(new_photo.read()).decode()}"
            requests.post(SCRIPT_URL, json={"action":"update_photo", "phone":u_phone, "photo":b64_img})
            st.success("Photo Updated! Refreshing..."); time.sleep(1); st.rerun()

# --- FEEDBACK ---
elif menu == "💬 Feedback":
    st.title("Customer Feedback")
    msg = st.text_area("Share your experience with us...")
    if st.button("Submit Feedback"):
        if msg:
            requests.post(SCRIPT_URL, json={"action":"feedback", "name":u_name, "phone":u_phone, "message":msg})
            st.success("Thank you for your feedback!")
        else: st.error("Please write something.")
