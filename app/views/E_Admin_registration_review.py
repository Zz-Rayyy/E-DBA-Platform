from flask import Blueprint, request, jsonify, send_file, render_template
from app.models.registration import Registration
from app.models.base import db
import io
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

admin_registrationBP = Blueprint('admin_registration', __name__)

# 配置（请替换为实际邮箱）
SENIOR_ADMIN_EMAIL = os.environ.get("SENIOR_ADMIN_EMAIL", "")
EMAIL_ADDRESS = os.environ.get("SMTP_EMAIL", "")
EMAIL_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

@admin_registrationBP.route('/admin', methods=['GET'])
def admin_panel():
    return render_template('E-Admin.html', admin_name="E-Admin")

def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    try:
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# 获取所有注册申请
@admin_registrationBP.route('/admin/registrations', methods=['GET'])
def get_registrations():
    regs = Registration.query.order_by(Registration.registrationID.desc()).all()
    data = []
    for reg in regs:
        # 转换时间戳为字符串
        if reg.create_time:
            submitted_at = datetime.fromtimestamp(reg.create_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            submitted_at = ""
        data.append({
            "registrationID": reg.registrationID,
            "organizationNameInFull": reg.organizationNameInFull,
            "organizationNameInShort": reg.organizationNameInShort,
            "convenerEmail": reg.convenerEmail,
            "status": reg.status,
            "submittedAt": submitted_at,
        })
    return jsonify({"status": "success", "data": data})

# 查看PDF
@admin_registrationBP.route('/admin/registration/<int:reg_id>/proof', methods=['GET'])
def get_proof_pdf(reg_id):
    reg = Registration.query.get(reg_id)
    if not reg or not reg.proofFile:
        return "Not found", 404
    return send_file(
        io.BytesIO(reg.proofFile),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'proof_{reg_id}.pdf'
    )

# 审批
@admin_registrationBP.route('/admin/registration/<int:reg_id>/approve', methods=['POST'])
def approve_registration(reg_id):
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({"status": "error", "message": "Registration not found"})
    if reg.status != "Pending":
        return jsonify({"status": "error", "message": "Already reviewed"})
    reg.status = "Approved"
    db.session.commit()
    # 通知 Senior E-Admin
    send_email(SENIOR_ADMIN_EMAIL, "Registration Approved",
               f"Registration {reg_id} has been approved. Please review.")
    return jsonify({"status": "success", "message": "Application approved and notice sent to Senior E-Admin"})

# 拒绝
@admin_registrationBP.route('/admin/registration/<int:reg_id>/reject', methods=['POST'])
def reject_registration(reg_id):
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({"status": "error", "message": "Registration not found"})
    if reg.status != "Pending":
        return jsonify({"status": "error", "message": "Already reviewed"})
    reg.status = "Rejected"
    db.session.commit()
    # 通知申请人
    send_email(reg.convenerEmail, "Registration Rejected",
               f"Your registration application (ID: {reg_id}) has been rejected.")
    return jsonify({"status": "success", "message": "Application rejected and notice sent to applicant"})
