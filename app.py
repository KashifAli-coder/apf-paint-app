import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib.parse
from fpdf import FPDF
import io

# --- CONFIG ---
SETTINGS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=1215788411&single=true&output=csv"
ORDERS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRtyPndRTxFA2DFEiAe7GYsXm16HskK7a40oc02xfwGNuRWTtMgHNrA2aSLZb3K6tTA5sM9Lt_nDc3q/pub?gid=0&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyIVWmY0Cj8_S9W-fdwRFWnE6cg7TxTrKqxtvNjSS330krT-VuYtesLcdpD_n5tStXv/exec"
ADMIN_WHATSAPP = "923005508112"

# --- PDF GENERATOR ---
def generate_pdf(name, phone, items_text, total, format_type="A4"):
    # A4 size ya Thermal (80mm) size
    pdf = FPDF(orientation='P', unit='mm', format='A4' if format_type=="A4" else (80, 150))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14 if format_type=="A4" else 10)
    pdf.cell(0, 10, "APF PAINT FACTORY INVOICE", ln=True, align='C')
    pdf.set_font("Arial", size=10 if format_type=="A4" else 8)
    pdf.cell(0, 7, f"Customer: {name}", ln=True)
    pdf.cell(0, 7, f"Phone: {phone}", ln=True)
    pdf.cell(0, 7, f"Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True)
    pdf.ln(5)
    pdf.multi_cell(0, 7, f"Order Details:\n{items_text}")
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12 if format_type=="A4" else 9)
    pdf.cell(0, 10, f"TOTAL BILL: Rs. {total}", ln=True)
    return pdf.output()

def send_wa(num, msg):
    num = "92" + num.replace("'","").lstrip('0')
    return f"https://wa.me/{num}?text={urllib.parse.quote(msg)}"

# --- APP START ---
st.set_page_config(page_title="APF Factory", layout="wide")
orders_df = pd.read_csv(f"{ORDERS_URL}&cache={datetime.now().timestamp()}", dtype={'Phone': str}).fillna('')
settings_df = pd.read_csv(f"{SETTINGS_URL}&cache={datetime.now().timestamp()}").fillna('')
settings = settings_df.iloc[0].to_dict() if not settings_df.empty else {"Admin_Password": "123"}

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 APF Login")
    phone_input = st.text_input("Mobile Number:")
    if st.button("Login"):
        clean_p = phone_input.lstrip('0')
        user = orders_df[orders_df['Phone'].str.contains(clean_p, na=False)]
        if not user.empty and "Approved" in user['Status'].values:
            st.session_state.logged_in, st.session_state.user_data = True, user.iloc[0].to_dict()
            st.rerun()
        else: st.error("Account Pending ya Not Found.")

# --- DASHBOARD ---
else:
    menu = st.sidebar.radio("Menu", ["👤 My Profile", "🛍️ Order Now", "🔐 Admin Dashboard"])
    
    if menu == "👤 My Profile":
        st.header(f"Welcome, {st.session_state.user_data['Name']}")
        u_p = st.session_state.user_data['Phone'].replace("'","").lstrip('0')
        u_orders = orders_df[orders_df['Phone'].str.contains(u_p, na=False)]
        c1, c2 = st.columns(2)
        c1.metric("Points", f"{u_orders['Points'].astype(float).sum():.1f}")
        c2.metric("Total Orders", len(u_orders))
        if st.sidebar.button("Logout"): 
            st.session_state.logged_in = False
            st.rerun()

    elif menu == "🛍️ Order Now":
        st.header("Place New Order")
        if 'cart' not in st.session_state: st.session_state.cart = []
        
        cats = settings_df['Category'].dropna().unique()
        if len(cats) > 0:
            col1, col2 = st.columns(2)
            sel_cat = col1.selectbox("Category", cats)
            prods = settings_df[settings_df['Category'] == sel_cat]
            sel_prod = col2.selectbox("Product", prods['Product Name'].unique())
            price = prods[prods['Product Name'] == sel_prod]['Price'].values[0]
            qty = st.number_input("Quantity", min_value=1, step=1)
            
            if st.button("Add to Cart ➕"):
                st.session_state.cart.append({"Product": sel_prod, "Qty": qty, "Price": price, "Total": price*qty})
                st.rerun()

        if st.session_state.cart:
            st.write("### Cart Summary")
            bill = sum(i['Total'] for i in st.session_state.cart)
            items_str = "\n".join([f"{i['Qty']}x {i['Product']} = {i['Total']}" for i in st.session_state.cart])
            st.text(items_str)
            st.write(f"*Total: Rs. {bill}*")
            
            if st.button("Confirm Order & Get Receipt"):
                requests.post(SCRIPT_URL, json={"action": "order", "name": st.session_state.user_data['Name'], "phone": "'" + st.session_state.user_data['Phone'], "product": items_str.replace("\n", ", "), "bill": float(bill), "points": float(bill/100)})
                st.success("Order Saved!")
                # Customer Receipt
                pdf_bytes = generate_pdf(st.session_state.user_data['Name'], st.session_state.user_data['Phone'], items_str, bill, "Thermal")
                st.download_button("Download Receipt (Thermal) 📄", pdf_bytes, "receipt.pdf", "application/pdf")
                st.session_state.cart = []

    elif menu == "🔐 Admin Dashboard":
        pw = st.sidebar.text_input("Master Password", type="password")
        if pw == str(settings.get('Admin_Password')):
            st.header("Admin Control Panel")
            unpaid = orders_df[orders_df['Status'].str.contains("Order")]
            if not unpaid.empty:
                for idx, row in unpaid.iterrows():
                    with st.expander(f"Order: {row['Name']} - Rs.{row['Bill']}"):
                        c1, c2, c3 = st.columns(3)
                        if c1.button("Mark Paid ✅", key=f"p_{idx}"):
                            requests.post(SCRIPT_URL, json={"action": "mark_paid", "phone": row['Phone'], "product": row['Product']})
                            wa_m = f"Assalam-o-Alaikum {row['Name']}! Aapki payment Rs.{row['Bill']} receive ho gayi hai. Shukria!"
                            st.markdown(f"[Send WA Receipt]({send_wa(row['Phone'], wa_m)})")
                            st.rerun()
                        # Admin options for both formats
                        pdf_a4 = generate_pdf(row['Name'], row['Phone'], row['Product'], row['Bill'], "A4")
                        c2.download_button("Download A4", pdf_a4, f"A4_{idx}.pdf", key=f"a4_{idx}")
                        pdf_th = generate_pdf(row['Name'], row['Phone'], row['Product'], row['Bill'], "Thermal")
                        c3.download_button("Download Thermal", pdf_th, f"TH_{idx}.pdf", key=f"th_{idx}")
            else: st.info("No pending payments.")
        else: st.warning("Admin password required.")
