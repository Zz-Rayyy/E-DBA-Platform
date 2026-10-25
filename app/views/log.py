from flask import Blueprint, jsonify, session, request
from app.models.log import Log
from app.models.organization import Organization
from app.models.user import User
from app.models.base import db
from datetime import datetime
from sqlalchemy import and_
import traceback

logBP = Blueprint('log', __name__)

@logBP.route('/api/logs/<int:organization_id>', methods=['GET'])
def get_organization_logs(organization_id):
    try:
        # 检查用户是否登录
        user_id = session.get('userID')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
        # 检查组织是否存在
        organization = Organization.query.get(organization_id)
        if not organization:
            return jsonify({'status': 'error', 'message': 'Organization not found'}), 404
        
        # 获取查询参数
        user_email = request.args.get('user', '')
        action = request.args.get('action', '')
        date = request.args.get('date', '')
        
        # 构建查询
        query = Log.query.filter_by(organizationID=organization_id)
        
        # 添加过滤条件
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
            except ValueError:
                pass
        
        # 获取日志并按时间倒序排序
        logs = query.order_by(Log.timestamp.desc()).all()
        
        # 格式化日志数据
        log_data = [{
            'logID': log.logID,
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
        print(f"Error in get_organization_logs: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

# 添加日志的辅助函数
def add_log(organization_id, user_id, action, details=None):
    try:
        log = Log(
            organizationID=organization_id,
            userID=user_id,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"Error adding log: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback() 