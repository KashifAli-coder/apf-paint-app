import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib.parse
from fpdf import FPDF

# ================= CONFIGURATION =================
SETTINGS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=1215788411&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyIVWmY0Cj8_S9W-fdwRFWnE6cg7TxTrKqxtvNjSS330krT-VuYtesLcdpD_n5tStXv/exec"
ADMIN_WHATSAPP = "923005508112"

# --- PDF GENERATOR ---
def generate_pdf(name, phone, items_text, total, format_type="A4"):
    pdf_size = 'A4' if format_type == "A4" else (80, 150)
    pdf = FPDF(orientation='P', unit='mm', format=pdf_size)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14 if format_type == "A4" else 10)
    pdf.cell(0, 10, "APF PAINT FACTORY INVOICE", ln=True, align='C')
    pdf.set_font("Arial", size=10 if format_type == "A4" else 8)
    pdf.cell(0, 7, f"Customer: {name}", ln=True)
    pdf.cell(0, 7, f"Phone: {phone}", ln=True)
    pdf.cell(0, 7, f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10 if format_type == "A4" else 8)
    pdf.cell(0, 7, "Order Details:", ln=True)
    pdf.set_font("Arial", size=10 if format_type == "A4" else 8)
    pdf.multi_cell(0, 7, items_text)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12 if format_type == "A4" else 9)
    pdf.cell(0, 10, f"TOTAL BILL: Rs. {total}", ln=True, border='T')
    return pdf.output(dest='S')

def send_wa(num, msg):
    num = "92" + num.replace("'","").lstrip('0')
    return f"https://wa.me/{num}?text={urllib.parse.quote(msg)}"

# --- APP START ---
st.set_page_config(page_title="APF Factory", layout="wide")

# Persistent Login Check
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_data" not in st.session_state: st.session_state.user_data = None
if "is_admin" not in st.session_state: st.session_state.is_admin = False

# Data Loading
try:
    orders_df = pd.read_csv(f"{ORDERS_URL}&cache={datetime.now().timestamp()}", dtype={'Phone': str}).fillna('')
    settings_df = pd.read_csv(f"{SETTINGS_URL}&cache={datetime.now().timestamp()}").fillna('')
    settings = settings_df.iloc[0].to_dict() if not settings_df.empty else {"Admin_Password": "123", "Company_Name": "APF Factory"}
except:
    st.error("Sheet loading error. URL check karein.")
    st.stop()

# ---------------- LOGIN SCREEN ----------------
if not st.session_state.logged_in:
    st.title(f"🔐 Welcome to {settings.get('Company_Name')}")
    phone_input = st.text_input("Mobile Number enter karein:")
    if st.button("Login ➡️"):
        clean_p = phone_input.lstrip('0')
        user = orders_df[orders_df['Phone'].str.contains(clean_p, na=False)]
        if not user.empty and "Approved" in user['Status'].values:
            st.session_state.logged_in = True
            st.session_state.user_data = user.iloc[0].to_dict()
            if phone_input == "03005508112": st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Number registered nahi hai ya approval pending hai.")
    
    with st.expander("Naya Account Register Karein"):
        reg_name = st.text_input("Naam:")
        reg_mail = st.text_input("Gmail:")
        if st.button("Submit Registration"):
            requests.post(SCRIPT_URL, json={"action": "register", "name": reg_name, "phone": "'" + phone_input, "email": reg_mail})
            st.success("Request bhej di gayi!")
            st.markdown(f"[Admin ko WhatsApp karein]({send_wa(ADMIN_WHATSAPP, 'Registration req: ' + reg_name)})")

# ---------------- DASHBOARD AREA ----------------
else:
    # Sidebar Role-Based Menu
    options = ["👤 My Profile", "🛍️ Order Now", "📜 History"]
    if st.session_state.is_admin: options.append("🔐 Admin Dashboard")
    
    menu = st.sidebar.radio("Main Menu", options)
    if st.sidebar.button("🚪 Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    # --- 👤 ENHANCED PROFILE ---
    if menu == "👤 My Profile":
        st.markdown(f"### ✨ Welcome Back, {st.session_state.user_data['Name']}!")
        u_p = st.session_state.user_data['Phone'].replace("'","").lstrip('0')
        u_orders = orders_df[orders_df['Phone'].str.contains(u_p, na=False)]
        pts = u_orders['Points'].astype(float).sum() if not u_orders.empty else 0.0
        
        st.markdown("""<style>.p-block { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 10px; }</style>""", unsafe_allow_html=True)
        st.markdown(f"""<div class="p-block" style="background-color: #e3f2fd; border-left-color: #2196f3;"><b>👤 User Details</b><br>Name: {st.session_state.user_data['Name']}<br>Phone: {st.session_state.user_data['Phone']}<br>Email: {st.session_state.user_data.get('Email', 'N/A')}</div>""", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="p-block" style="background-color: #fff9c4; border-left-color: #fbc02d;">🪙 <b>Points</b><br>{pts:.1f}</div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="p-block" style="background-color: #c8e6c9; border-left-color: #4caf50;">📦 <b>Total Orders</b><br>{len(u_orders)}</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="p-block" style="background-color: #ffccbc; border-left-color: #ff5722;">⏳ <b>Unpaid</b><br>{len(u_orders[u_orders['Status'].str.contains("Order", na=False)])}</div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="p-block" style="background-color: #e1f5fe; border-left-color: #03a9f4;">🏆 <b>Status</b><br>Verified Dealer</div>""", unsafe_allow_html=True)

    # --- 🛍️ ORDER NOW ---
    elif menu == "🛍️ Order Now":
        st.header("🛍️ Place Order")
        if 'cart' not in st.session_state: st.session_state.cart = []
        cats = settings_df['Category'].dropna().unique()
        col1, col2 = st.columns(2)
        sel_cat = col1.selectbox("Category", cats)
        prods = settings_df[settings_df['Category'] == sel_cat]
        sel_prod = col2.selectbox("Product", prods['Product Name'].unique())
        price = prods[prods['Product Name'] == sel_prod]['Price'].values[0]
        qty = st.number_input("Qty", min_value=1, step=1)
        if st.button("Add to Cart 🛒"):
            st.session_state.cart.append({"Product": sel_prod, "Qty": qty, "Price": price, "Total": price*qty})
            st.rerun()

        if st.session_state.cart:
            bill = sum(i['Total'] for i in st.session_state.cart)
            items_str = "\n".join([f"{i['Qty']}x {i['Product']} = {i['Total']}" for i in st.session_state.cart])
            st.text(items_str)
            if st.button(f"Confirm Order (Rs. {bill})"):
                requests.post(SCRIPT_URL, json={"action": "order", "name": st.session_state.user_data['Name'], "phone": "'" + st.session_state.user_data['Phone'], "product": items_str.replace("\n", ", "), "bill": float(bill), "points": float(bill/100)})
                st.success("Order Placed!")
                pdf_bytes = generate_pdf(st.session_state.user_data['Name'], st.session_state.user_data['Phone'], items_str, bill, "Thermal")
                st.download_button("Download Receipt 📄", pdf_bytes, "receipt.pdf", "application/pdf")
                st.session_state.cart = []

    # --- 📜 HISTORY ---
    elif menu == "📜 History":
        st.header("Your History")
        u_p = st.session_state.user_data['Phone'].replace("'","").lstrip('0')
        hist = orders_df[orders_df['Phone'].str.contains(u_p, na=False)]
        st.dataframe(hist[['Date', 'Product', 'Bill', 'Status']].iloc[::-1], use_container_width=True)

    # --- 🔐 ADMIN DASHBOARD ---
    elif menu == "🔐 Admin Dashboard":
        st.header("Admin Management")
        unpaid = orders_df[orders_df['Status'].str.contains("Order", na=False)]
        for idx, row in unpaid.iterrows():
            with st.expander(f"{row['Name']} - {row['Bill']}"):
                c1, c2, c3 = st.columns(3)
                if c1.button("Mark Paid ✅", key=f"pay_{idx}"):
                    requests.post(SCRIPT_URL, json={"action": "mark_paid", "phone": row['Phone'], "product": row['Product']})
                    st.rerun()
                a4 = generate_pdf(row['Name'], row['Phone'], row['Product'], row['Bill'], "A4")
                c2.download_button("Download A4", a4, f"A4_{idx}.pdf")
                th = generate_pdf(row['Name'], row['Phone'], row['Product'], row['Bill'], "Thermal")
                c3.download_button("Thermal", th, f"TH_{idx}.pdf")
