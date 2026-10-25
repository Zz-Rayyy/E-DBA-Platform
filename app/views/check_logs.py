from flask import Blueprint, jsonify, request, session
from app.models.log import Log
from app.models.user import User
from app.models.organization import Organization
from app.models.base import db
from datetime import datetime
from sqlalchemy import and_
import traceback

check_logsBP = Blueprint('check_logs', __name__)

@check_logsBP.route('/api/all_logs', methods=['GET'])
def get_all_logs():
    try:
        # 检查用户是否是E-Admin
        user_id = session.get('userID')
        if not user_id:
            print("No user ID in session")
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
        user = User.query.get(user_id)
        if not user:
            print(f"User not found: {user_id}")
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        if user.userType != 'E-Admin':
            print(f"User is not E-Admin: {user.userType}")
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        # 获取查询参数
        organization_id = request.args.get('organization', '')
        user_email = request.args.get('user', '')
        action = request.args.get('action', '')
        date = request.args.get('date', '')
        
        print(f"Query parameters: org={organization_id}, user={user_email}, action={action}, date={date}")
        
        # 构建查询
        query = Log.query
        
        # 添加过滤条件
        if organization_id:
            query = query.filter(Log.organizationID == organization_id)
        if user_email:
            query = query.join(User).filter(User.email.ilike(f'%{user_email}%'))
        if action:
            query = query.filter(Log.action == action)
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                next_day = date_obj.replace(day=date_obj.day + 1)
                query = query.filter(and_(
                    Log.timestamp >= date_obj,
                    Log.timestamp < next_day
                ))
            except ValueError as e:
                print(f"Invalid date format: {date}, error: {str(e)}")
        
        # 获取日志并按时间倒序排序
        logs = query.order_by(Log.timestamp.desc()).all()
        print(f"Found {len(logs)} logs")
        
        # 格式化日志数据
        log_data = [{
            'logID': log.logID,
            'organization': {
                'organizationID': log.organization.organizationID,
                'name': log.organization.organizationNameInFull
            },
            'action': log.action,
            'details': log.details,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'user': {
                'userID': log.user.userID,
                'email': log.user.email
            }
        } for log in logs]
        
        return jsonify({
            'status': 'success',
            'data': log_data
        })
    except Exception as e:
        print(f"Error in get_all_logs: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

@check_logsBP.route('/api/organizations', methods=['GET'])
def get_organizations():
    try:
        # 检查用户是否是E-Admin
        user_id = session.get('userID')
        if not user_id:
            print("No user ID in session")
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
        user = User.query.get(user_id)
        if not user:
            print(f"User not found: {user_id}")
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        if user.userType != 'E-Admin':
            print(f"User is not E-Admin: {user.userType}")
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
        # 获取所有组织
        organizations = Organization.query.all()
        print(f"Found {len(organizations)} organizations")
        
        org_data = [{
            'organizationID': org.organizationID,
            'name': org.organizationNameInFull
        } for org in organizations]
        
        return jsonify({
            'status': 'success',
            'data': org_data
        })
    except Exception as e:
        print(f"Error in get_organizations: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500
