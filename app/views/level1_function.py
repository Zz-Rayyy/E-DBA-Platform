from flask import Blueprint, jsonify, request, send_file, session
from app.models.service import Service
from app.models.course import Course
from app.models.api_config import ApiConfig
from app.models.dataUser import DataUser
from app.models.convener_data_user import ConvenerDataUser
from app.models.bank_account import BankAccount
from app.models.account_user import AccountUser
from app.models.base import db
from app.views.log import add_log
import requests
import io
import decimal

level1_functionBP = Blueprint('level1_function', __name__)

@level1_functionBP.route('/api/level1_functions/<int:organization_id>/<int:user_id>', methods=['GET'])
def get_level1_functions(organization_id, user_id):
    course_service = Service.query.filter_by(organizationID=organization_id, serviceName='Course Information Sharing').first()
    search_thesis_service = Service.query.filter_by(organizationID=organization_id, serviceName='Search Thesis').first()
    result = {
        'access_course_info': bool(course_service and course_service.use_status == 'available'),
        'view_thesis': bool(search_thesis_service and search_thesis_service.use_status == 'available')
    }
    return jsonify({'status': 'success', 'data': result})

@level1_functionBP.route('/api/courses/<int:organization_id>', methods=['GET'])
def get_courses_for_level1(organization_id):
    courses = Course.query.filter_by(organizationID=organization_id).all()
    data = [{
        'cid': c.cid,
        'title': c.title,
        'units': c.units,
        'description': c.description
    } for c in courses]
    return jsonify({'status': 'success', 'data': data})

@level1_functionBP.route('/api/service_input_config/<int:organization_id>/<service_name>', methods=['GET'])
def get_service_input_config(organization_id, service_name):
    service = Service.query.filter_by(organizationID=organization_id, serviceName=service_name).first()
    if not service:
        return jsonify({'status': 'error', 'message': 'Service not found'})
    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf or not api_conf.input:
        return jsonify({'status': 'error', 'message': 'No input config'})
    return jsonify({'status': 'success', 'input': api_conf.input})

@level1_functionBP.route('/api/search_thesis/<int:organization_id>', methods=['POST'])
def search_thesis(organization_id):
    # 1. Get Search Thesis service
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Search Thesis').first()
    if not service or service.use_status != 'available':
        return jsonify({'status': 'error', 'message': 'Service not available'})
    
    # 2. Get API configuration
    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf:
        return jsonify({'status': 'error', 'message': 'API not configured'})
    
    # 3. Prepare request
    base_url = api_conf.base_url
    path = api_conf.path
    method = api_conf.method
    input_keys = api_conf.input if isinstance(api_conf.input, dict) else {}
    output_keys = api_conf.output if isinstance(api_conf.output, dict) else None
    
    # Construct URL
    url = base_url.rstrip('/') + '/' + path.lstrip('/')
    
    # Get user input data
    user_data = request.json or {}
    
    # Prepare payload
    payload = {key: user_data.get(key, "") for key in input_keys.keys()}
    
    # 4. Make external API request
    try:
        if method.lower() == 'post':
            resp = requests.post(url, json=payload, timeout=5)
        elif method.lower() == 'get':
            resp = requests.get(url, params=payload, timeout=5)
        else:
            return jsonify({'status': 'error', 'message': f'Unsupported HTTP method: {method}'})
        
        if resp.status_code != 200:
            return jsonify({'status': 'error', 'message': f'External API error: {resp.status_code}'})
        
        result = resp.json()
        
        # 5. Filter output if configured
        if output_keys:
            if isinstance(result, list):
                filtered = [
                    {k: item.get(k, "") for k in output_keys.keys()} if isinstance(item, dict) else item
                    for item in result
                ]
            elif isinstance(result, dict):
                filtered = {k: result.get(k, "") for k in output_keys.keys()}
            else:
                filtered = result
            return jsonify({'status': 'success', 'data': filtered})
        
        return jsonify({'status': 'success', 'data': result})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'API call failed: {str(e)}'})

@level1_functionBP.route('/api/get_thesis_pdf/<int:organization_id>', methods=['POST'])
def get_thesis_pdf(organization_id):
    try:
        # 1. 获取当前用户ID
        user_id = session.get('userID')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

        # 2. 检查用户配额
        data_user = DataUser.query.get(user_id)
        if not data_user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        # 3. 获取O-Convener的银行账户信息
        convener_data_user = ConvenerDataUser.query.filter_by(dataUserID=user_id).first()
        if not convener_data_user:
            return jsonify({'status': 'error', 'message': 'No convener found for this user'}), 404

        account_user = AccountUser.query.filter_by(userID=convener_data_user.userID).first()
        if not account_user:
            return jsonify({'status': 'error', 'message': 'No account user found'}), 404

        bank_account = BankAccount.query.filter_by(bankAccountID=account_user.bankAccountID).first()
        if not bank_account:
            return jsonify({'status': 'error', 'message': 'No bank account found'}), 404

        # 4. 检查余额是否足够
        download_fee = decimal.Decimal(str(data_user.quota))
        if bank_account.balance < download_fee:
            add_log(organization_id, user_id, "Thesis Download Failed", "Insufficient balance")
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

        # 5. 获取Get Thesis PDF服务
        service = Service.query.filter_by(organizationID=organization_id, serviceName='Get Thesis PDF').first()
        if not service or service.use_status != 'available':
            add_log(organization_id, user_id, "Thesis Download Failed", "Service not available")
            return jsonify({'status': 'error', 'message': 'Service not available'}), 400

        api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
        if not api_conf:
            add_log(organization_id, user_id, "Thesis Download Failed", "API not configured")
            return jsonify({'status': 'error', 'message': 'API not configured'}), 400

        base_url = api_conf.base_url
        path = api_conf.path
        method = api_conf.method
        input_keys = api_conf.input if isinstance(api_conf.input, dict) else {}

        url = base_url.rstrip('/') + '/' + path.lstrip('/')

        user_data = request.json or {}
        payload = {key: user_data.get(key, "") for key in input_keys.keys()}

        # 6. 扣除费用
        bank_account.balance -= download_fee
        db.session.commit()

        try:
            # 7. 获取PDF文件
            if method.lower() == 'post':
                resp = requests.post(url, json=payload, timeout=10)
            elif method.lower() == 'get':
                resp = requests.get(url, params=payload, timeout=10)
            else:
                raise ValueError(f'Unsupported HTTP method: {method}')

            if resp.status_code != 200:
                # 如果获取PDF失败，退还费用
                bank_account.balance += download_fee
                db.session.commit()
                add_log(organization_id, user_id, "Thesis Download Failed", f"External API error: {resp.status_code}")
                return jsonify({'status': 'error', 'message': f'External API error: {resp.status_code} - {resp.text}'}), 400

            # 8. 返回PDF文件
            pdf_bytes = resp.content
            filename = user_data.get('title') or 'file'
            
            # 记录成功的下载
            add_log(organization_id, user_id, "Thesis Download Success", f"Downloaded thesis: {filename}")
            
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{filename}.pdf"
            )

        except requests.exceptions.RequestException as e:
            # 如果发生网络错误，退还费用
            bank_account.balance += download_fee
            db.session.commit()
            add_log(organization_id, user_id, "Thesis Download Failed", f"Network error: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Network error: {str(e)}'}), 500

    except Exception as e:
        # 如果发生其他错误，退还费用
        if 'bank_account' in locals() and 'download_fee' in locals():
            bank_account.balance += download_fee
            db.session.commit()
        add_log(organization_id, user_id, "Thesis Download Failed", f"Server error: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

@level1_functionBP.route('/api/check_balance/<int:organization_id>', methods=['GET'])
def check_balance(organization_id):
    # 1. 获取当前用户ID
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    # 2. 检查用户配额
    data_user = DataUser.query.get(user_id)
    if not data_user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    # 3. 获取O-Convener的银行账户信息
    convener_data_user = ConvenerDataUser.query.filter_by(dataUserID=user_id).first()
    if not convener_data_user:
        return jsonify({'status': 'error', 'message': 'No convener found for this user'}), 404

    account_user = AccountUser.query.filter_by(userID=convener_data_user.userID).first()
    if not account_user:
        return jsonify({'status': 'error', 'message': 'No account user found'}), 404

    bank_account = BankAccount.query.filter_by(bankAccountID=account_user.bankAccountID).first()
    if not bank_account:
        return jsonify({'status': 'error', 'message': 'No bank account found'}), 404

    return jsonify({
        'status': 'success',
        'data': {
            'balance': float(bank_account.balance),
            'download_fee': float(data_user.quota)
        }
    })
