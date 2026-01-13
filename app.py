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
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzuMMPIoME0v7ZUAu_EzWK1oDjqB_YaRtejtO3_a7clBCl3Yjr69_sZQA6JykLo5Kuj/exec"
JAZZCASH_NO = "03005508112"

st.set_page_config(page_title="Paint Pro Manufacturing", layout="wide")

# Custom UI Styling
st.markdown("""
    <style>
    .product-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 10px; }
    .cart-box { background: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #3b82f6; position: sticky; top: 20px; }
    .stButton>button { border-radius: 5px; }
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
# STEP 4: AUTHENTICATION (Login/Register)
# ========================================================
if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<h2 style='text-align: center;'>🎨 Paint Factory Portal</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
        with t1:
            l_ph = st.text_input("Phone")
            l_pw = st.text_input("Password", type="password")
            if st.button("Login 🚀", use_container_width=True):
                u_ph = normalize_ph(l_ph)
                match = users_df[(users_df['Phone'].apply(normalize_ph) == u_ph) & (users_df['Password'].astype(str) == l_pw)]
                if not match.empty:
                    user_row = match.iloc[0]
                    if str(user_row['Role']).lower() == 'pending': st.warning("Approval Pending...")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_data = user_row.to_dict()
                        st.rerun()
                else: st.error("Login Failed")
        with t2:
            r_name = st.text_input("Factory/Dealer Name")
            r_ph = st.text_input("Contact Number")
            r_pw = st.text_input("Set Password", type="password")
            if st.button("Submit Registration", use_container_width=True):
                requests.post(SCRIPT_URL, json={"action":"register", "name":r_name, "phone":normalize_ph(r_ph), "password":r_pw})
                st.success("Registered! Waiting for Admin Approval.")
    st.stop()

# ========================================================
# STEP 5: SIDEBAR
# ========================================================
u_data = st.session_state.user_data
u_name = u_data.get('Name', 'User')
raw_ph = normalize_ph(u_data.get('Phone', ''))

st.sidebar.title("Menu")
for btn in ["🏠 Dashboard", "👤 Profile", "🛍️ New Order", "📜 History", "💬 Feedback"]:
    if st.sidebar.button(btn, use_container_width=True): set_nav(btn)

if raw_ph == normalize_ph(JAZZCASH_NO):
    if st.sidebar.button("🔐 Admin Control", use_container_width=True): set_nav("🔐 Admin")

if st.sidebar.button("Logout 🚪", use_container_width=True):
    st.session_state.clear()
    st.rerun()

menu = st.session_state.menu_choice

# ========================================================
# STEP 6: PAINT BUSINESS MODULES
# ========================================================

# --- DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title(f"Welcome, {u_name}")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    col1, col2 = st.columns(2)
    col1.metric("Total Orders", len(u_ords))
    col2.metric("Balance Spent", f"Rs. {u_ords['Bill'].sum()}")
    st.divider()
    st.subheader("Recent Order Summary")
    st.dataframe(u_ords.tail(5), use_container_width=True)

# --- NEW ORDER (Paint Specific) ---
elif menu == "🛍️ New Order":
    st.header("🎨 Order Manufacturing Items")
    
    if settings_df.empty:
        st.error("Products not loaded. Check Settings sheet.")
    else:
        col_main, col_cart = st.columns([1.8, 1])

        with col_main:
            # Filters for Paint Products
            f1, f2 = st.columns(2)
            cat = f1.selectbox("Product Category", settings_df['Category'].unique())
            
            # Sub-category logic (e.g. Interior, Exterior, Industrial)
            sub_df = settings_df[settings_df['Category'] == cat]
            sub_cat = f2.selectbox("Sub-Category", sub_df['Sub-Category'].unique() if 'Sub-Category' in sub_df.columns else ["Standard"])
            
            final_list = sub_df[sub_df['Sub-Category'] == sub_cat] if 'Sub-Category' in sub_df.columns else sub_df

            st.markdown("---")
            for _, row in final_list.iterrows():
                with st.expander(f"📦 {row['Product Name']} - Rs. {row['Price']}"):
                    c_qty, c_shade, c_add = st.columns([1, 1.5, 1])
                    q = c_qty.number_input("Quantity", 1, 1000, 1, key=f"qty_{row['Product Name']}")
                    shade = c_shade.text_input("Shade Code / Note", "Standard White", key=f"sh_{row['Product Name']}")
                    
                    if c_add.button("Add ➕", key=f"btn_{row['Product Name']}", use_container_width=True):
                        # Update logic: If already in cart, update quantity
                        found = False
                        for item in st.session_state.cart:
                            if item['Product'] == row['Product Name'] and item['Shade'] == shade:
                                item['Qty'] += q
                                item['Total'] = item['Qty'] * item['Price']
                                found = True
                                break
                        if not found:
                            st.session_state.cart.append({
                                "Product": row['Product Name'], "Shade": shade,
                                "Qty": q, "Price": float(row['Price']), "Total": float(row['Price']) * q
                            })
                        st.toast(f"Updated Cart: {row['Product Name']}")
                        st.rerun()

        with col_cart:
            st.markdown('<div class="cart-box">', unsafe_allow_html=True)
            st.subheader("🛒 Current Cart")
            if not st.session_state.cart:
                st.write("Cart is empty.")
            else:
                net_total = 0
                for i, itm in enumerate(st.session_state.cart):
                    net_total += itm['Total']
                    st.markdown(f"**{itm['Product']}** ({itm['Shade']})")
                    st.write(f"{itm['Qty']} x {itm['Price']} = Rs. {itm['Total']}")
                    if st.button("Remove 🗑️", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                
                st.divider()
                st.write(f"### Total: Rs. {net_total}")
                
                method = st.selectbox("Payment", ["COD", "JazzCash", "Bank Transfer"])
                receipt_b64 = ""
                if method != "COD":
                    file = st.file_uploader("Upload Payment Receipt", type=['jpg','png','pdf'])
                    if file:
                        receipt_b64 = f"data:image/png;base64,{base64.b64encode(file.read()).decode()}"

                if st.button("Confirm Order ✅", use_container_width=True, type="primary"):
                    if method != "COD" and not receipt_b64:
                        st.error("Please upload receipt.")
                    else:
                        inv = f"PNT-{int(time.time())}"
                        summary = ", ".join([f"{x['Qty']}x {x['Product']}({x['Shade']})" for x in st.session_state.cart])
                        requests.post(SCRIPT_URL, json={
                            "action":"order", "invoice_id":inv, "name":u_name, "phone":raw_ph,
                            "product":summary, "bill":net_total, "payment_method":method, "receipt":receipt_b64
                        })
                        st.session_state.cart = []
                        st.success("Order Placed Successfully!")
                        time.sleep(1); set_nav("🏠 Dashboard")
            st.markdown('</div>', unsafe_allow_html=True)

# --- HISTORY ---
elif menu == "📜 History":
    st.header("📜 Order History")
    u_ords = orders_df[orders_df['Phone'].apply(normalize_ph) == raw_ph]
    for _, row in u_ords.iloc[::-1].iterrows():
        with st.container():
            st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:10px; border-left:5px solid #3b82f6; margin-bottom:10px;">
                    <b>Invoice: {row['Invoice_ID']}</b> | Status: {row['Status']}<br>
                    Items: {row['Product']}<br>
                    <b>Bill: Rs. {row['Bill']}</b> | Method: {row['Payment_Method']}
                </div>
            """, unsafe_allow_html=True)

# --- ADMIN ---
elif menu == "🔐 Admin":
    st.header("🛡️ Factory Admin")
    t1, t2 = st.tabs(["Orders Management", "User Approvals"])
    with t1:
        for idx, row in orders_df.iterrows():
            with st.expander(f"Order {row['Invoice_ID']} - {row['Name']}"):
                st.write(f"Products: {row['Product']}")
                if 'Receipt' in row and row['Receipt']:
                    st.image(row['Receipt'], width=300)
                if st.button("Mark as Completed / Paid", key=f"adm_{idx}"):
                    requests.post(SCRIPT_URL, json={"action":"mark_paid", "invoice_id":row['Invoice_ID']})
                    st.rerun()
    with t2:
        p_u = users_df[users_df['Role'].str.lower() == 'pending']
        for idx, u in p_u.iterrows():
            st.write(f"New Dealer: {u['Name']} ({u['Phone']})")
            if st.button("Approve Dealer", key=f"app_{idx}"):
                requests.post(SCRIPT_URL, json={"action":"approve_user", "phone":normalize_ph(u['Phone'])})
                st.rerun()
