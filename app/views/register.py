import os
import time
import random
from flask import Blueprint, request, jsonify, render_template
from app.email_validation import is_valid_email
from app.models.registration import Registration
from app.models.base import db
from email.mime.text import MIMEText
import smtplib

registerBP = Blueprint('register', __name__)

# 临时存储验证码和发送时间（生产环境建议用数据库或 Redis）
verification_codes = {}

# 邮箱配置（以QQ邮箱为例）
EMAIL_ADDRESS = os.environ.get("SMTP_EMAIL", "")
EMAIL_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def send_verification_code(email, code):
    subject = "Your Verification Code"
    body = f"Your verification code is: {code}\nThis code is valid for 10 minutes."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

@registerBP.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('O-Convener_register.html')
    if request.method == 'POST':
        org_full = request.form.get('orgFullName')
        org_short = request.form.get('orgShortName')
        convener_email = request.form.get('convenerEmail')
        verification_code = request.form.get('verificationCode')
        proof_file = request.files.get('proofFile')

        # 校验字段
        if not all([org_full, org_short, convener_email, verification_code, proof_file]):
            return jsonify({'status': 'error', 'message': 'All fields are required.'})

        # 校验邮箱格式
        if not is_valid_email(convener_email):
            return jsonify({'status': 'error', 'message': 'Invalid email format.'})

        # 校验验证码
        if convener_email not in verification_codes:
            return jsonify({'status': 'error', 'message': 'No verification code sent for this email.'})
        stored_code, expiry_time = verification_codes[convener_email]["code"], verification_codes[convener_email]["expiry"]
        if time.time() > expiry_time:
            return jsonify({'status': 'error', 'message': 'Verification code expired.'})
        if verification_code != stored_code:
            return jsonify({'status': 'error', 'message': 'Invalid verification code.'})

        # 校验PDF
        if not proof_file or not proof_file.filename.lower().endswith('.pdf'):
            return jsonify({'status': 'error', 'message': 'Proof document must be a PDF file.'})
        pdf_data = proof_file.read()

        # 存入数据库
        try:
            registration = Registration(
                userID=None,  # 注册时还没有userID
                organizationNameInFull=org_full,
                organizationNameInShort=org_short,
                convenerEmail=convener_email,
                proofFile=pdf_data,
                status="Pending",
                organizationID=None
            )
            db.session.add(registration)
            db.session.commit()
            # 注册成功后清除验证码
            del verification_codes[convener_email]
            return jsonify({'status': 'success', 'message': 'Registration submitted for approval.'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Database error: {e}'})

@registerBP.route('/send-register-code', methods=['POST'])
def send_register_code():
    email = request.form.get('email')
    if not is_valid_email(email):
        return jsonify({'status': 'error', 'message': 'Invalid email format.'})

    # 检查是否可以重新发送（60秒冷却）
    if email in verification_codes:
        last_sent = verification_codes[email]["sent_time"]
        if time.time() - last_sent < 60:
            return jsonify({"status": "error", "message": "Please wait 60 seconds before resending"})

    # 生成6位验证码
    code = str(random.randint(100000, 999999))
    expiry = time.time() + 600  # 10分钟有效
    verification_codes[email] = {"code": code, "expiry": expiry, "sent_time": time.time()}

    if send_verification_code(email, code):
        return jsonify({"status": "success", "message": "Verification code sent"})
    else:
        return jsonify({"status": "error", "message": "Failed to send verification code"})
