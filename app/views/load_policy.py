from flask import Blueprint, request, jsonify, send_file, render_template
from app.models.policy import Policy
from app.models.base import db
import io
from datetime import datetime

load_policyBP = Blueprint('load_policy', __name__)

@load_policyBP.route('/policies', methods=['GET'])
def get_policies():
    policies = Policy.query.order_by(Policy.create_time.desc()).all()
    data = []
    for policy in policies:
        data.append({
            "policyID": policy.policyID,
            "title": policy.title,
            "uploadedAt": datetime.fromtimestamp(policy.create_time).strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify({"status": "success", "data": data})

@load_policyBP.route('/policy', methods=['POST'])
def add_policy():
    title = request.form.get('title')
    pdf_file = request.files.get('pdfFile')
    
    if not title or not pdf_file:
        return jsonify({"status": "error", "message": "Title and PDF file are required"})
    
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({"status": "error", "message": "Only PDF files are allowed"})
    
    try:
        pdf_data = pdf_file.read()
        print(f"PDF file size: {len(pdf_data)} bytes")
        policy = Policy(title=title, file_data=pdf_data)
        db.session.add(policy)
        db.session.commit()
        return jsonify({"status": "success", "message": "Policy added successfully"})
    except Exception as e:
        db.session.rollback()
        print(f"Error adding policy: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to add policy: {str(e)}"})

@load_policyBP.route('/policy/<int:policy_id>/pdf', methods=['GET'])
def get_policy_pdf(policy_id):
    policy = Policy.query.get(policy_id)
    if not policy or not policy.file_data:
        return "Policy not found", 404
    return send_file(
        io.BytesIO(policy.file_data),
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'policy_{policy_id}.pdf'
    )

@load_policyBP.route('/policy/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    policy = Policy.query.get(policy_id)
    if not policy:
        return jsonify({"status": "error", "message": "Policy not found"})
    
    try:
        db.session.delete(policy)
        db.session.commit()
        return jsonify({"status": "success", "message": "Policy deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to delete policy: {str(e)}"})
