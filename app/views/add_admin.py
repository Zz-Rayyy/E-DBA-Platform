from flask import Blueprint, request, jsonify, session, render_template
from app.models.user import User
from app.models.base import db
from app.email_validation import is_valid_email
from datetime import datetime

t_adminBP = Blueprint('t_admin', __name__)

@t_adminBP.route('/t_admin', methods=['GET'])
def t_admin_panel():
    return render_template('T-Admin.html')

# 获取所有管理员
@t_adminBP.route('/api/admins', methods=['GET'])
def get_admins():
    admins = User.query.filter(User.userType.in_(['E-Admin', 'Senior-E-Admin'])).all()
    data = []
    for admin in admins:
        data.append({
            'adminID': admin.userID,
            'email': admin.email,
            'adminType': admin.userType,
            'createdAt': datetime.fromtimestamp(admin.create_time).strftime('%Y-%m-%d %H:%M:%S') if admin.create_time else ''
        })
    return jsonify({'status': 'success', 'data': data})

# 添加新管理员
@t_adminBP.route('/api/admin', methods=['POST'])
def add_admin():
    email = request.form.get('email')
    admin_type = request.form.get('adminType')

    # 验证邮箱格式
    if not is_valid_email(email):
        return jsonify({'status': 'error', 'message': 'Invalid email format.'})

    # 检查邮箱是否已存在
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'status': 'error', 'message': 'Email already registered.'})

    try:
        # 创建新管理员用户
        new_admin = User(
            email=email,
            userType=admin_type
        )
        db.session.add(new_admin)
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'{admin_type} added successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to add admin: {str(e)}'})

# 删除管理员
@t_adminBP.route('/api/admin/<int:admin_id>', methods=['DELETE'])
def delete_admin(admin_id):
    admin = User.query.get(admin_id)
    if not admin:
        return jsonify({'status': 'error', 'message': 'Admin not found.'})

    try:
        db.session.delete(admin)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Admin deleted successfully.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to delete admin: {str(e)}'})
