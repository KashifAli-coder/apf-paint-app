import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib.parse

# ================= CONFIGURATION =================
SETTINGS_URL = "APKI_SETTINGS_SHEET_CSV_URL"
ORDERS_URL = "APKI_ORDERS_SHEET_CSV_URL"
SCRIPT_URL = "APKI_GOOGLE_APPS_SCRIPT_WEB_APP_URL"

def load_data(url):
    try:
        return pd.read_csv(f"{url}&nocache={datetime.now().timestamp()}")
    except:
        return pd.DataFrame()

# Data Load
settings_df = load_data(SETTINGS_URL)
settings = settings_df.iloc[0] if not settings_df.empty else {}
orders_df = load_data(ORDERS_URL)

# UI Config
st.set_page_config(page_title=settings.get('Company_Name', 'APF Factory'), layout="wide")
if settings.get('Logo_URL'):
    st.sidebar.image(settings.get('Logo_URL'), width=120)

# --- INVOICE GENERATOR ---
def get_invoice(inv_id, name, phone, cart, total, method, type="thermal"):
    c_name = str(settings.get('Company_Name')).upper()
    addr = str(settings.get('Address'))
    terms = str(settings.get('Terms'))
    dt = datetime.now().strftime('%d-%m-%Y %H:%M')
    
    if type == "thermal":
        res = f"{c_name}\n{addr[:30]}\n{'-'*30}\nINV: #ID-{inv_id}\nDATE: {dt}\nCUST: {name}\nPH: {phone}\n{'-'*30}\nITEM           QTY      TOTAL\n"
        for i in cart: res += f"{i['Product'][:15]:<15} {i['Qty']:>3} {i['Total']:>10}\n"
        res += f"{'-'*30}\nTOTAL: Rs. {total}\nPAYMENT: {method}\n{'-'*30}\n{terms[:30]}"
        return res
    else:
        res = f"{'='*60}\n{c_name.center(60)}\n{'='*60}\nAddress: {addr}\nInvoice: #INV-{inv_id} | Date: {dt}\nCustomer: {name} | Phone: {phone}\n{'-'*60}\nSR  PRODUCT                  QTY    PRICE     TOTAL\n{'-'*60}\n"
        for i, itm in enumerate(cart, 1):
            res += f"{i:<3} {itm['Product']:25} {itm['Qty']:>3} {itm['Price']:>9} {itm['Total']:>9}\n"
        res += f"{'-'*60}\nGRAND TOTAL: Rs. {total}\n{'-'*60}\nTerms: {terms}\n{'='*60}"
        return res

# --- SIDEBAR NAVIGATION ---
menu = st.sidebar.radio("Menu", ["🛍️ Order Now", "📜 History", "🔐 Admin Dashboard"])

# ---------------- 🛍️ ORDER SECTION ----------------
if menu == "🛍️ Order Now":
    st.title(f"🎨 {settings.get('Company_Name')}")
    phone_in = st.text_input("Enter Mobile Number:")

    if phone_in:
        user = orders_df[orders_df['Phone'].astype(str) == phone_in] if not orders_df.empty else pd.DataFrame()
        
        if user.empty:
            st.warning("Registeration Required!")
            reg_name = st.text_input("Full Name:")
            if st.button("Request Registration"):
                requests.post(SCRIPT_URL, json={"action": "register", "name": reg_name, "phone": phone_in})
                st.info("Request Sent! Admin approval ka intezar karein.")
        
        elif user.iloc[-1]['Status'] == "Approved":
            st.success(f"Khush Amdeed {user.iloc[-1]['Name']}!")
            if 'cart' not in st.session_state: st.session_state.cart = []

            # Categories from Sheet
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox("Category", settings_df['Category'].dropna().unique())
            sub = c2.selectbox("Sub-Category", settings_df[settings_df['Category']==cat]['Sub-Category'].unique())
            prods = settings_df[(settings_df['Category']==cat) & (settings_df['Sub-Category']==sub)]
            prod = c3.selectbox("Product", prods['Product Name'].unique())
            
            price = prods[prods['Product Name']==prod]['Price'].values[0]
            qty = st.number_input("Quantity", min_value=1)
            
            if st.button("Add to Cart ➕"):
                st.session_state.cart.append({"Product": prod, "Qty": qty, "Price": price, "Total": price*qty})
                st.rerun()

            if st.session_state.cart:
                st.write("### 🛒 Your Cart")
                for i, itm in enumerate(st.session_state.cart):
                    col_a, col_b = st.columns([4, 1])
                    col_a.write(f"{itm['Product']} x{itm['Qty']} = Rs.{itm['Total']}")
                    if col_b.button("🗑️", key=f"del_{i}"):
                        st.session_state.cart.pop(i)
                        st.rerun()
                
                method = st.radio("Payment", ["COD", "JazzCash", "EasyPaisa"])
                total = sum(i['Total'] for i in st.session_state.cart)
                
                if st.button("Confirm Order & Invoice 🚀"):
                    inv_id = len(orders_df) + 1
                    summary = ", ".join([f"{i['Qty']}x {i['Product']}" for i in st.session_state.cart])
                    requests.post(SCRIPT_URL, json={"action": "order", "name": user.iloc[-1]['Name'], "phone": phone_in, "product": summary, "bill": float(total), "points": float(total/100)})
                    
                    t_inv = get_invoice(inv_id, user.iloc[-1]['Name'], phone_in, st.session_state.cart, total, method, "thermal")
                    a_inv = get_invoice(inv_id, user.iloc[-1]['Name'], phone_in, st.session_state.cart, total, method, "a4")
                    
                    st.code(t_inv)
                    st.download_button("Download Thermal Receipt", t_inv)
                    st.download_button("Download A4 Invoice", a_inv)
                    st.session_state.cart = []
        else:
            st.info("Aapka account abhi 'Pending' hai.")

# ---------------- 📜 HISTORY SECTION ----------------
elif menu == "📜 History":
    st.header("Search Order History")
    h_phone = st.text_input("Enter Registered Number:")
    if h_phone:
        history = orders_df[orders_df['Phone'].astype(str) == h_phone]
        if not history.empty:
            st.metric("Total Points", f"{history['Points'].sum():.1f}")
            st.dataframe(history[['Date', 'Product', 'Bill', 'Status']].iloc[::-1])
        else:
            st.error("No record found.")

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
                    requests.post(SCRIPT_URL, json={"action": "update_settings", "company_name": n_name, "address": n_addr, "contact": settings.get('JazzCash_No'), "logo": n_logo, "password": settings.get('Admin_Password'), "terms": n_terms})
                    st.success("Settings Updated!")
        
        with tab2:
            pending = orders_df[orders_df['Status'] == "Pending"]
            if not pending.empty:
                st.write("### Pending Approvals")
                to_app = st.selectbox("Select Phone", pending['Phone'].unique())
                if st.button("Approve Now ✅"):
                    resp = requests.post(SCRIPT_URL, json={"action": "approve", "phone": to_app})
                    st.success(f"Approved! WhatsApp Link ready.")
                    msg = f"Salam {resp.text}! Aapka account approve ho gaya hai."
                    st.markdown(f'[Send WhatsApp Notification](https://wa.me/92{to_app.lstrip("0")}?text={urllib.parse.quote(msg)})')
            st.write("### All Data")
            st.dataframe(orders_df)
