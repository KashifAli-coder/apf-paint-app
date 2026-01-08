import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# ================= CONFIGURATION (LATEST LINKS APPLIED) =================
SETTINGS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=1215788411&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyIVWmY0Cj8_S9W-fdwRFWnE6cg7TxTrKqxtvNjSS330krT-VuYtesLcdpD_n5tStXv/exec"

def load_data(url):
    try:
        # Nocache ensures fresh data on every load
        return pd.read_csv(f"{url}&nocache={datetime.now().timestamp()}")
    except Exception as e:
        return pd.DataFrame()

# --- DATA LOADING ---
settings_df = load_data(SETTINGS_URL)
orders_df = load_data(ORDERS_URL)

# Settings processing
if not settings_df.empty:
    # Taking row 2 (index 0) as settings
    settings = settings_df.iloc[0].fillna('').to_dict()
else:
    settings = {'Company_Name': 'APF Factory', 'Admin_Password': '123'}

if orders_df.empty:
    orders_df = pd.DataFrame(columns=['Date', 'Name', 'Phone', 'Product', 'Bill', 'Points', 'Status'])
else:
    orders_df = orders_df.dropna(how='all')

# --- UI CONFIG ---
st.set_page_config(page_title=settings.get('Company_Name', 'APF Factory'), layout="wide")

# --- SIDEBAR MENU ---
if settings.get('Logo_URL'):
    st.sidebar.image(settings.get('Logo_URL'), width=120)

menu = st.sidebar.radio("Main Menu", ["🛍️ Order Now", "📜 History", "🔐 Admin Dashboard"])

# ---------------- 🛍️ ORDER SECTION ----------------
if menu == "🛍️ Order Now":
    st.title(f"🎨 {settings.get('Company_Name', 'APF Paint Factory')}")
    phone_in = st.text_input("Apna Mobile Number Likhein:")

    if phone_in:
        # Check if user exists
        user = orders_df[orders_df['Phone'].astype(str).str.contains(phone_in)] if not orders_df.empty else pd.DataFrame()
        
        if user.empty:
            st.warning("Aap registered nahi hain!")
            reg_name = st.text_input("Apna Poora Naam Likhein:")
            if st.button("Registration Request Bhein"):
                requests.post(SCRIPT_URL, json={"action": "register", "name": reg_name, "phone": phone_in})
                st.info("Request bhej di gayi hai! Admin approval ka intezar karein.")
        
        elif user.iloc[-1]['Status'] == "Approved":
            st.success(f"Khush Amdeed {user.iloc[-1]['Name']}!")
            if 'cart' not in st.session_state: st.session_state.cart = []

            # Product Selection using your exact Column Names
            c1, c2 = st.columns(2)
            available_cats = settings_df['Category'].dropna().unique()
            
            if len(available_cats) > 0:
                cat = c1.selectbox("Category Chunein", available_cats)
                prod_list = settings_df[settings_df['Category'] == cat]
                prod = c2.selectbox("Product Chunein", prod_list['Product Name'].unique())
                
                # Fetching price from 'Price' column
                price_val = prod_list[prod_list['Product Name'] == prod]['Price'].values[0]
                qty = st.number_input("Quantity", min_value=1, value=1)
                
                if st.button("Cart mein Add Karein ➕"):
                    st.session_state.cart.append({"Product": prod, "Qty": qty, "Price": price_val, "Total": price_val * qty})
                    st.rerun()

            # Cart Display
            if st.session_state.cart:
                st.write("### 🛒 Aapka Cart")
                total_bill = 0
                for i, itm in enumerate(st.session_state.cart):
                    st.write(f"{itm['Product']} - {itm['Qty']} x {itm['Price']} = Rs. {itm['Total']}")
                    total_bill += itm['Total']
                
                method = st.radio("Payment Method", ["Cash on Delivery", "JazzCash", "EasyPaisa"])
                if st.button("Order Confirm Karein 🚀"):
                    summary = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                    requests.post(SCRIPT_URL, json={
                        "action": "order", 
                        "name": user.iloc[-1]['Name'], 
                        "phone": phone_in, 
                        "product": summary, 
                        "bill": float(total_bill), 
                        "points": float(total_bill/100)
                    })
                    st.success("Order kamyabi se record ho gaya!")
                    st.session_state.cart = []
                    st.rerun()
        else:
            st.info("Aapka account abhi 'Pending' hai. Admin approval ka intezar karein.")

# ---------------- 📜 HISTORY SECTION ----------------
elif menu == "📜 History":
    st.header("Order History")
    h_phone = st.text_input("Mobile Number Likhein:")
    if h_phone:
        history = orders_df[orders_df['Phone'].astype(str).str.contains(h_phone)]
        if not history.empty:
            st.metric("Aapke Total Points", f"{history['Points'].sum():.1f}")
            st.dataframe(history[['Date', 'Product', 'Bill', 'Status']].iloc[::-1])
        else:
            st.error("Is number par koi record nahi mila.")

# ---------------- 🔐 ADMIN SECTION ----------------
elif menu == "🔐 Admin Dashboard":
    pw = st.sidebar.text_input("Password", type="password")
    if pw == str(settings.get('Admin_Password')):
        tab1, tab2 = st.tabs(["⚙️ Settings", "📊 Orders & Approval"])
        
        with tab1:
            with st.form("admin_settings"):
                n_name = st.text_input("Factory Name", settings.get('Company_Name'))
                n_addr = st.text_input("Address", settings.get('Address'))
                n_logo = st.text_input("Logo URL", settings.get('Logo_URL'))
                n_terms = st.text_area("Terms", settings.get('Terms'))
                if st.form_submit_button("Save All Settings"):
                    requests.post(SCRIPT_URL, json={
                        "action": "update_settings", 
                        "company_name": n_name, 
                        "address": n_addr, 
                        "contact": settings.get('Contact', ''), 
                        "logo": n_logo, 
                        "password": pw, 
                        "terms": n_terms
                    })
                    st.success("Settings Update ho gayi hain!")
        
        with tab2:
            pending = orders_df[orders_df['Status'] == "Pending"]
            if not pending.empty:
                st.write("### Pending Approvals")
                to_app = st.selectbox("Select Number", pending['Phone'].unique())
                if st.button("Approve Kar Dein ✅"):
                    requests.post(SCRIPT_URL, json={"action": "approve", "phone": to_app})
                    st.success(f"Number {to_app} Approved!")
                    st.rerun()
            st.write("### All Orders Data")
            st.dataframe(orders_df)
    else:
        st.error("Ghalat Password!")
