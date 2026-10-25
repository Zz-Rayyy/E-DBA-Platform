import os
import time
import random
import smtplib
from email.mime.text import MIMEText
from flask import request, jsonify, render_template, Blueprint, session, redirect, url_for, current_app
from app.email_validation import is_valid_email
from app.models.user import User
from app.models.paidUser import PaidUser
from app.models.base import db

userBP = Blueprint('user', __name__)

verification_codes = {}

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

@userBP.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    if request.method == "POST":
        email = request.form.get("email")
        code = request.form.get("code")
        user_type = request.form.get("userType")
        # 邮箱格式校验
        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format"}), 400

        # 验证验证码
        if email in verification_codes:
            stored_code, expiry_time = verification_codes[email]["code"], verification_codes[email]["expiry"]
            if time.time() > expiry_time:
                return jsonify({"status": "error", "message": "Verification code expired"}), 400
            if code != stored_code:
                return jsonify({"status": "error", "message": "Invalid verification code"}), 400

            # 验证码正确，检查用户是否存在且类型匹配
            user = User.query.filter_by(email=email, userType=user_type).first()
            if user:
                # 如果是DataUser，检查是否已付费
                if user_type == "DataUser":
                    paid_user = PaidUser.query.filter_by(userID=user.userID).first()
                    if not paid_user:
                        return jsonify({"status": "error", "message": "You need to pay membership fee first"}), 403

                # 登录成功，清除验证码
                del verification_codes[email]
                session['userID'] = user.userID
                session['userType'] = user.userType
                # 跳转页面
                if user.userType == "E-Admin":
                    return jsonify({"status": "success", "message": "Login successful", "redirect": url_for('admin_registration.admin_panel'), "userID": user.userID})
                elif user.userType == "Senior-E-Admin":
                    return jsonify({"status": "success", "message": "Login successful", "redirect": url_for('senior_admin.senior_admin_panel'), "userID": user.userID})
                elif user.userType == "O-Convener":
                    return jsonify({"status": "success", "message": "Login successful", "redirect": url_for('manage.o_convener_workspace'), "userID": user.userID})
                elif user.userType == "DataUser":
                    return jsonify({"status": "success", "message": "Login successful", "redirect": url_for('choose_org.datauser_organizations_page'), "userID": user.userID})
                else:
                    return jsonify({"status": "success", "message": "Login successful", "redirect": url_for('t_admin.t_admin_panel'), "userID": user.userID})
            else:
                return jsonify({"status": "error", "message": "Email or user type not found"}), 404
        else:
            return jsonify({"status": "error", "message": "No verification code sent for this email"}), 400

@userBP.route("/send-verification", methods=["POST"])
def send_verification():
    email = request.form.get("email")
    if not is_valid_email(email):
        return jsonify({"status": "error", "message": "Invalid email format"}), 400

    # 检查是否可以重新发送（60秒冷却）
    if email in verification_codes:
        last_sent = verification_codes[email]["sent_time"]
        if time.time() - last_sent < 60:
            return jsonify({"status": "error", "message": "Please wait 60 seconds before resending"}), 429

    # 生成6位验证码
    code = str(random.randint(100000, 999999))
    expiry = time.time() + 600  # 验证码有效期10分钟
    verification_codes[email] = {"code": code, "expiry": expiry, "sent_time": time.time()}

    # 发送验证码
    if send_verification_code(email, code):
        return jsonify({"status": "success", "message": "Verification code sent"}), 200
    elif current_app.debug:
        print(f"[DEV] Verification code for {email}: {code}")
        return jsonify({"status": "success", "message": "Verification code printed in terminal"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send verification code"}), 500
