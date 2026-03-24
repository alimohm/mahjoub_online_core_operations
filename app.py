import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import re
from fpdf import FPDF # تأكد من إضافة fpdf في ملف requirements.txt

app = Flask(__name__)

# --- إعدادات واتساب محجوب أونلاين ---
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com" # رابط سيرفرك في رندر

def smart_parse(data):
    if isinstance(data, dict): return data
    try: return json.loads(data)
    except: return {}

def get_real_text(val):
    txt = str(val).strip()
    if not txt or txt.lower() in ['none', 'null', '', 'false']: return None
    if len(txt) >= 20 and re.match(r'^[a-f0-9]+$', txt): return None
    return txt

# --- وظيفة صناعة الفاتورة PDF برقم الطلب ---
def create_invoice_pdf(order_id, customer_name, total, date_str):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 15, txt="MAHJOUB ONLINE", ln=True, align='C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="OFFICIAL INVOICE", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 12)
        pdf.cell(100, 10, txt=f"Order ID: #{order_id}")
        pdf.cell(100, 10, txt=f"Date: {date_str}", ln=True, align='R')
        pdf.cell(200, 10, txt=f"Customer: {customer_name}", ln=True)
        pdf.ln(5)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(140, 10, txt="Description", border=1, fill=True)
        pdf.cell(50, 10, txt="Total", border=1, ln=True, fill=True, align='C')
        pdf.cell(140, 15, txt="Items from Mahjoub Online Store", border=1)
        pdf.cell(50, 15, txt=f"{total} YER", border=1, ln=True, align='C')
        pdf.ln(20)
        pdf.cell(200, 10, txt="Thank you for shopping with us!", ln=True, align='C')
        
        file_path = f"invoice_{order_id}.pdf"
        pdf.output(file_path)
        return file_path
    except:
        return None

# --- رابط تحميل الفاتورة المخصص لكل عميل ---
@app.route('/download/invoice_<order_id>.pdf')
def download_custom_invoice(order_id):
    file_name = f"invoice_{order_id}.pdf"
    if not os.path.exists(file_name):
        # في حال لم يجد الملف يصنع واحد سريعاً ببيانات افتراضية
        create_invoice_pdf(order_id, "Valued Customer", "---", datetime.now().strftime("%Y-%m-%d"))
    return send_from_directory(os.getcwd(), file_name)

@app.route('/webhook', methods=['POST', 'GET', 'HEAD'])
def mahjoub_auto_receipt_v38():
    if request.method in ['GET', 'HEAD']: return "OK", 200
    try:
        raw_data = request.get_data(as_text=True)
        payload = smart_parse(raw_data)
        order = smart_parse(payload.get('data', payload))
        customer = smart_parse(order.get('salesLead', {}))
        
        event = payload.get('event', 'order.created')
        order_id = order.get('handel', '0000')
        phone = str(customer.get('phone1', '')).replace('+', '').replace(' ', '')
        tracking_link = f"https://mahjoub.online/customer/thank-you/{order_id}"
        
        # التوقيت اليمني
        yemen_time = datetime.utcnow() + timedelta(hours=3)
        full_time = yemen_time.strftime("%Y/%m/%d - %I:%M %p") 
        
        status_info = smart_parse(order.get('status', {}))
        status_title = status_info.get('title', 'قيد الإنتظار')
        is_paid = order.get('isPaid', False)
        pay_text = "✅ *مدفوع*" if is_paid else "❌ *غير مدفوع*"
        
        # تجهيز بيانات الفاتورة
        cust_full_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}"
        total_p = order.get('priceWithShipping', 0)
        create_invoice_pdf(order_id, cust_full_name, total_p, yemen_time.strftime("%Y-%m-%d"))

        divider = "╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼╼"
        footer = "⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n*نظام محجوب أونلاين | سوقك الذكي*"

        if event == "order.created":
            city = get_real_text(customer.get('cityName')) or "اليمن"
            pdf_link = f"{BASE_URL}/download/invoice_{order_id}.pdf"
            
            msg = (
                "✨ *إشعار نظام: تم إنشاء طلب جديد* ✨\n\n"
                f"🧾 *فاتورة رقم:* `{order_id}`\n"
                f"{divider}\n"
                f"👤 *العميل:* {cust_full_name}\n"
                f"📍 *الموقع:* {city}\n"
                f"{divider}\n"
                f"💵 *الإجمالي النهائي:* `{total_p}` ريال\n"
                f"{divider}\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"📝 *حالة الدفع:* {pay_text}\n"
                f"{divider}\n"
                f"🕒 *توقيت الطلب:* `{full_time}`\n"
                f"📄 *تحميل فاتورتك PDF:* \n{pdf_link}\n\n"
                f"{footer}"
            )
        else:
            msg = (
                "🔄 *إشعار نظام: تحديث الطلب*\n"
                f"{divider}\n"
                f"📦 *رقم المنتج:* `{order_id}`\n"
                f"🚚 *حالة المنتج:* 【 {status_title} 】\n"
                f"{divider}\n"
                f"🔗 *تتبع:* {tracking_link}\n\n"
                f"{footer}"
            )

        if phone and len(phone) > 5:
            api_url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTMEBOT_API_KEY}&text={urllib.parse.quote(msg)}"
            requests.get(api_url, timeout=10)

        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
