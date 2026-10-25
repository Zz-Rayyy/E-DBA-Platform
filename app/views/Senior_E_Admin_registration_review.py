from flask import Blueprint, request, jsonify, render_template, send_file
from app.models.registration import Registration
from app.models.user import User
from app.models.organization import Organization
from app.models.base import db
import io
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

senior_adminBP = Blueprint('senior_admin', __name__)

# 邮箱配置
EMAIL_ADDRESS = os.environ.get("SMTP_EMAIL", "")
EMAIL_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

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

@senior_adminBP.route('/senior_admin', methods=['GET'])
def senior_admin_panel():
    return render_template('Senior-E-Admin.html', admin_name="Senior E-Admin")

# 获取所有已由E-Admin批准的注册申请
@senior_adminBP.route('/senior_admin/final-approvals', methods=['GET'])
def get_final_approvals():
    regs = Registration.query.filter_by(status='Approved').order_by(Registration.registrationID.desc()).all()
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
@senior_adminBP.route('/senior_admin/registration/<int:reg_id>/proof', methods=['GET'])
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

# 最终批准
@senior_adminBP.route('/senior_admin/registration/<int:reg_id>/final-approve', methods=['POST'])
def final_approve_registration(reg_id):
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({"status": "error", "message": "Registration not found"})
    if reg.status != "Approved":
        return jsonify({"status": "error", "message": "Only approved applications can be finally approved"})
    
    try:
        # Create O-Convener user
        user = User(
            email=reg.convenerEmail,
            userType="O-Convener"
        )
        db.session.add(user)
        db.session.flush()  # Get new userID

        # Update registration's userID and status
        reg.userID = user.userID
        reg.status = "Final_approved"

        # Add: Insert into organization table and update registration's organizationID
        organization = Organization(
            organizationNameInFull=reg.organizationNameInFull,
            organizationNameInShort=reg.organizationNameInShort,
            bankName="",
            accountNo="",
            accountName="",
            password=""
        )
        db.session.add(organization)
        db.session.flush()  # Get new organizationID

        reg.organizationID = organization.organizationID

        db.session.commit()
        
        # Send notification email
        send_email(reg.convenerEmail, "Registration Finally Approved",
                  f"Your registration application (ID: {reg_id}) has been finally approved. You can now login to the system as an O-Convener.")
        
        return jsonify({"status": "success", "message": "Application finally approved, organization created, and O-Convener account created"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {e}"})

# 最终拒绝
@senior_adminBP.route('/senior_admin/registration/<int:reg_id>/final-reject', methods=['POST'])
def final_reject_registration(reg_id):
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({"status": "error", "message": "Registration not found"})
    if reg.status != "Approved":
        return jsonify({"status": "error", "message": "Only approved applications can be finally rejected"})
    
    try:
        reg.status = "Rejected"
        db.session.commit()
        
        # Send notification email
        send_email(reg.convenerEmail, "Registration Finally Rejected",
                  f"Your registration application (ID: {reg_id}) has been finally rejected.")
        
        return jsonify({"status": "success", "message": "Application finally rejected"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Database error: {e}"})
