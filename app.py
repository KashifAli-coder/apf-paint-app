import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib.parse

# ================= CONFIGURATION =================
# Yahan apne Google Sheet ke CSV links aur Apps Script ka URL dalein
SETTINGS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=1215788411&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyIVWmY0Cj8_S9W-fdwRFWnE6cg7TxTrKqxtvNjSS330krT-VuYtesLcdpD_n5tStXv/exec"

def load_data(url):
    try:
        # Nocache taake har dafa naya data load ho
        return pd.read_csv(f"{url}&nocache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame()

# --- DATA LOADING ---
settings_df = load_data(SETTINGS_URL)
orders_df = load_data(ORDERS_URL)

# Settings ko dictionary mein convert karna
if not settings_df.empty:
    settings = settings_df.iloc[0].fillna('').to_dict()
else:
    settings = {'Company_Name': 'APF Factory', 'Admin_Password': '123'}

if orders_df.empty:
    orders_df = pd.DataFrame(columns=['Date', 'Name', 'Phone', 'Product', 'Bill', 'Points', 'Status'])

# --- UI CONFIG ---
st.set_page_config(page_title=settings.get('Company_Name'), layout="wide")

# --- SIDEBAR MENU ---
if settings.get('Logo_URL'):
    st.sidebar.image(settings.get('Logo_URL'), width=120)

menu = st.sidebar.radio("Main Menu", ["🛍️ Order Now", "📜 History", "🔐 Admin Dashboard"])

# ---------------- 🛍️ ORDER SECTION ----------------
if menu == "🛍️ Order Now":
    st.title(f"🎨 {settings.get('Company_Name')}")
    phone_in = st.text_input("Apna Mobile Number Likhein:")

    if phone_in:
        user = orders_df[orders_df['Phone'].astype(str).str.contains(phone_in)] if not orders_df.empty else pd.DataFrame()
        
        if user.empty:
            st.warning("Registration Required!")
            reg_name = st.text_input("Apna Poora Naam Likhein:")
            if st.button("Register Hone ki Request Bhein"):
                requests.post(SCRIPT_URL, json={"action": "register", "name": reg_name, "phone": phone_in})
                st.info("Request bhej di gayi hai! Admin approval ka intezar karein.")
        
        elif user.iloc[-1]['Status'] == "Approved":
            st.success(f"Khush Amdeed {user.iloc[-1]['Name']}!")
            if 'cart' not in st.session_state: st.session_state.cart = []

            # Category selection
            available_cats = settings_df['Category'].dropna().unique()
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Category", available_cats)
            
            # Product selection
            prods = settings_df[settings_df['Category']==cat]
            prod = c2.selectbox("Product", prods['Product Name'].unique())
            
            price = prods[prods['Product Name']==prod]['Price'].values[0]
            qty = st.number_input("Quantity", min_value=1, value=1)
            
            if st.button("Cart mein Add Karein ➕"):
                st.session_state.cart.append({"Product": prod, "Qty": qty, "Price": price, "Total": price*qty})
                st.rerun()

            if st.session_state.cart:
                st.write("### 🛒 Aapka Cart")
                total = 0
                for i, itm in enumerate(st.session_state.cart):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"{itm['Product']} x{itm['Qty']} = Rs.{itm['Total']}")
                    total += itm['Total']
                    if col_b.button("🗑️", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                
                method = st.radio("Payment", ["COD", "JazzCash", "EasyPaisa"])
                if st.button("Confirm Order 🚀"):
                    summary = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                    requests.post(SCRIPT_URL, json={
                        "action": "order", 
                        "name": user.iloc[-1]['Name'], 
                        "phone": phone_in, 
                        "product": summary, 
                        "bill": float(total), 
                        "points": float(total/100)
                    })
                    st.success("Order kamyabi se record ho gaya!")
                    st.session_state.cart = []
                    st.rerun()
        else:
            st.info("Aapka account abhi 'Pending' hai.")

# ---------------- 📜 HISTORY SECTION ----------------
elif menu == "📜 History":
    st.header("Order History")
    h_phone = st.text_input("Apna Mobile Number Likhein:")
    if h_phone:
        history = orders_df[orders_df['Phone'].astype(str).str.contains(h_phone)]
        if not history.empty:
            st.metric("Total Points", f"{history['Points'].sum():.1f}")
            st.dataframe(history[['Date', 'Product', 'Bill', 'Status']].iloc[::-1])
        else:
            st.error("Koi record nahi mila.")

# ---------------- 🔐 ADMIN SECTION ----------------
elif menu == "🔐 Admin Dashboard":
    pw = st.sidebar.text_input("Password", type="password")
    if pw == str(settings.get('Admin_Password')):
        tab1, tab2 = st.tabs(["⚙️ Settings", "📊 Orders & Approval"])
        
        with tab1:
            with st.form("settings"):
                n_name = st.text_input("Factory Name", settings.get('Company_Name'))
                n_addr = st.text_input("Address", settings.get('Address'))
                n_logo = st.text_input("Logo URL", settings.get('Logo_URL'))
                n_terms = st.text_area("Terms", settings.get('Terms'))
                if st.form_submit_button("Save Settings"):
                    requests.post(SCRIPT_URL, json={
                        "action": "update_settings", 
                        "company_name": n_name, 
                        "address": n_addr, 
                        "contact": settings.get('Contact'), 
                        "logo": n_logo, 
                        "password": pw, 
                        "terms": n_terms
                    })
                    st.success("Settings Updated!")
        
        with tab2:
            pending = orders_df[orders_df['Status'] == "Pending"]
            if not pending.empty:
                st.write("### Pending Approvals")
                to_app = st.selectbox("Select Phone", pending['Phone'].unique())
                if st.button("Approve Now ✅"):
                    requests.post(SCRIPT_URL, json={"action": "approve", "phone": to_app})
                    st.success(f"Approved!")
                    st.rerun()
            st.write("### All Data")
            st.dataframe(orders_df)
    else:
        st.error("Admin Password darust nahi hai.")
