from flask import Blueprint, request, jsonify, send_file
from app.models.policy import Policy
from datetime import datetime
import io

browse_policyBP = Blueprint('browse_policy', __name__)

@browse_policyBP.route('/policies', methods=['GET'])
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

@browse_policyBP.route('/policy/<int:policy_id>/pdf', methods=['GET'])
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
