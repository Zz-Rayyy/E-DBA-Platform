from flask import Blueprint, request, jsonify, session
from app.models.fee import Fee
from app.models.user import User
from app.models.base import db

manage_member_feesBP = Blueprint('manage_member_fees', __name__)

@manage_member_feesBP.route('/api/save_membership_fees', methods=['POST'])
def save_membership_fees():
    # 获取当前登录的E-Admin用户ID
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    # 验证用户是否为E-Admin
    user = User.query.get(user_id)
    if not user or user.userType != 'E-Admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    # 获取表单数据
    level1_fee = request.form.get('level1Fee')
    level2_fee = request.form.get('level2Fee')
    level3_fee = request.form.get('level3Fee')

    if not all([level1_fee, level2_fee, level3_fee]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'})

    try:
        # 创建新的费用记录
        fee = Fee(
            level1Fee=int(float(level1_fee)),  # 转换为分存储
            level2Fee=int(float(level2_fee)),
            level3Fee=int(float(level3_fee))
        )
        db.session.add(fee)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Membership fees saved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to save membership fees: {str(e)}'
        })

@manage_member_feesBP.route('/api/membership_fees', methods=['GET'])
def get_membership_fees():
    # 获取当前登录的E-Admin用户ID
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    # 验证用户是否为E-Admin
    user = User.query.get(user_id)
    if not user or user.userType != 'E-Admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    try:
        # 获取最新的费用记录
        latest_fee = Fee.query.order_by(Fee.feeID.desc()).first()
        
        if latest_fee:
            return jsonify({
                'status': 'success',
                'data': {
                    'level1Fee': latest_fee.level1Fee / 100,  # 转换回元
                    'level2Fee': latest_fee.level2Fee / 100,
                    'level3Fee': latest_fee.level3Fee / 100
                }
            })
        else:
            return jsonify({
                'status': 'success',
                'data': {
                    'level1Fee': '',
                    'level2Fee': '',
                    'level3Fee': ''
                }
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get membership fees: {str(e)}'
        })
