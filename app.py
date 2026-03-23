from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# إعدادات البوت من TextMeBot
TEXTME_BOT_KEY = "CWEMDRmhtq4e" 

def send_whatsapp(phone, message):
    url = f"https://api.textmebot.com/send.php?recipient={phone}&apikey={TEXTME_BOT_KEY}&text={message}"
    try:
        response = requests.get(url)
        return response.status_code
    except:
        return 500

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # استخراج نوع الحدث (نبحث عن الكلمة سواء كانت بـ topic أو بدون)
    event = data.get('event', '')
    order_data = data.get('data', {})
    
    # استخراج بيانات العميل والطلب
    lead = order_data.get('salesLead', {})
    phone = lead.get('phone1', '').replace('+', '')
    name = lead.get('firstName', 'عميلنا العزيز')
    order_no = order_data.get('handel', 'غير معروف')
    total = order_data.get('totalPriceWithTax', 0)
    status_title = order_data.get('status', {}).get('title', 'قيد المعالجة')

    # رسالة عند إنشاء طلب جديد (الفاتورة المبسطة)
    if "order.created" in event or "order.placed" in event:
        msg = f"مرحباً {name} 👋\nشكراً لطلبك من *محجوب أونلاين* 🛍️\n\nرقم طلبك: #{order_no}\nالإجمالي: {total} ريال\nالحالة: {status_title}\n\nسيتم إشعارك فور تحديث حالة الطلب. شكراً لثقتك بنا! ✨"
        send_whatsapp(phone, msg)
        
    # رسالة عند تحديث الحالة من الإدارة
    elif "order.updated" in event:
        msg = f"عزيزي {name} 👋\nتم تحديث حالة طلبك رقم #{order_no}\n\nالحالة الجديدة: *{status_title}* ✅\n\nشكراً لتسوقك من سوقك الذكي."
        send_whatsapp(phone, msg)

    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
