import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from fpdf import FPDF

app = Flask(__name__)

API_KEY = "CWEMDRmhtq4e"
BASE_URL = "https://mahjoub-bot.onrender.com"

@app.route('/')
def home():
    return "Mahjoub Bot is Running!", 200

@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(os.getcwd(), filename)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        order = data.get('data', {})
        customer = order.get('salesLead', {})
        
        order_id = order.get('handel', '0000')
        phone = str(customer.get('phone1', '')).replace('+', '').strip()
        total = order.get('totalPrice', 0)

        if phone:
            # إنشاء فاتورة بسيطة جداً بالإنجليزية لتجنب أخطاء الخطوط العربية
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="MAHJOUB ONLINE INVOICE", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Order ID: {order_id}", ln=2, align='L')
            pdf.cell(200, 10, txt=f"Total: {total} SAR", ln=3, align='L')
            
            invoice_name = "invoice.pdf"
            pdf.output(invoice_name)

            # إرسال النص
            msg = f"✨ تم تأكيد طلبك رقم {order_id}. الفاتورة مرفقة."
            requests.get(f"https://api.textmebot.com/send.php?recipient={phone}&apikey={API_KEY}&text={urllib.parse.quote(msg)}")
            
            # إرسال الملف
            file_url = f"{BASE_URL}/download/{invoice_name}"
            requests.get(f"https://api.textmebot.com/send.php?recipient={phone}&apikey={API_KEY}&document={urllib.parse.quote(file_url)}")

        return jsonify({"status": "success"}), 200
    except Exception as e:
        # طباعة الخطأ في سجلات Render لمعرفته
        print(f"Error occurred: {e}")
        return jsonify({"status": "error"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
