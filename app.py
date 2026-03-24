import os
from flask import Flask, request, jsonify, send_from_directory
import requests
import urllib.parse
from datetime import datetime, timedelta
import json
import pdfkit # المكتبة المسؤولة عن تحويل HTML لـ PDF

app = Flask(__name__)

# إعدادات المسارات والروابط
BASE_URL = "https://mahjoub-bot.onrender.com"
TEXTMEBOT_API_KEY = "CWEMDRmhtq4e"

# دالة توليد الفاتورة PDF بناءً على تصميمك
def generate_pdf_invoice(order_data):
    # هنا نضع قالب الـ HTML الذي أرفقته مع استبدال البيانات بمتغيرات
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            /* نضع هنا كل الـ CSS الذي أرفقته في رسالتك */
            :root {{ --royal-purple: #4b0082; --gold-accent: #d4af37; }}
            body {{ font-family: 'Arial'; padding: 20px; }}
            .invoice-card {{ width: 100%; background: white; padding: 40px; border: 1px solid #eee; }}
            .status-bar {{ background: var(--royal-purple); color: white; padding: 10px; text-align: center; border-radius: 8px; }}
            /* ... بقية التنسيقات ... */
        </style>
    </head>
    <body>
        <div class="invoice-card">
            <h1>محجوب أونلاين</h1>
            <div class="status-bar">حالة الفاتورة: تم الإيداع والتسليم ✅</div>
            <p>اسم العميل: {order_data['customer_name']}</p>
            <p>رقم الطلب: {order_data['order_id']}</p>
            <p>الإجمالي: {order_data['total_price']} ريال</p>
        </div>
    </body>
    </html>
    """
    
    options = {{'enable-local-file-access': None}}
    filename = f"invoice_{order_data['order_id']}.pdf"
    
    # تحويل النص (HTML) إلى ملف PDF
    pdfkit.from_string(html_template, filename, options=options)
    return filename

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        order = data.get('data', {{}})
        customer = order.get('salesLead', {{}})
        
        # تجهيز بيانات الفاتورة من الـ Webhook
        invoice_info = {{
            'order_id': order.get('handel', '0000'),
            'customer_name': f"{{customer.get('firstName', '')}} {{customer.get('lastName', '')}}",
            'total_price': order.get('totalPrice', 0),
            'phone': str(customer.get('phone1', '')).replace('+', '')
        }}

        # 1. توليد الملف
        pdf_file = generate_pdf_invoice(invoice_info)

        # 2. إرسال الرابط للعميل عبر واتساب
        pdf_link = f"{{BASE_URL}}/download/{{pdf_file}}"
        whatsapp_url = f"https://api.textmebot.com/send.php?recipient={{invoice_info['phone']}}&apikey={{TEXTMEBOT_API_KEY}}&document={{urllib.parse.quote(pdf_link)}}"
        requests.get(whatsapp_url)

        return jsonify({{"status": "success"}}), 200
    except Exception as e:
        return jsonify({{"status": "error", "message": str(e)}}), 200

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
