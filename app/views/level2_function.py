from flask import Blueprint, jsonify, request, session
from app.models.service import Service
from app.models.api_config import ApiConfig
from app.models.dataUser import DataUser
from app.models.convener_data_user import ConvenerDataUser
from app.models.bank_account import BankAccount
from app.models.account_user import AccountUser
from app.models.base import db
import requests
import pandas as pd
import tempfile
import os
import decimal

level2_functionBP = Blueprint('level2_function', __name__)

@level2_functionBP.route('/api/level2_functions/<int:organization_id>', methods=['GET'])
def get_level2_functions(organization_id):
    # 查询本组织的Student Identity Authentication服务
    identity_service = Service.query.filter_by(organizationID=organization_id, serviceName='Student Identity Authentication').first()
    result = {
        'identity_auth': bool(identity_service and identity_service.use_status == 'available')
    }
    return jsonify({'status': 'success', 'data': result})

@level2_functionBP.route('/api/identity_input_config/<int:organization_id>', methods=['GET'])
def get_identity_input_config(organization_id):
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Student Identity Authentication').first()
    if not service:
        return jsonify({'status': 'error', 'message': 'Service not found'})
    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf or not api_conf.input:
        return jsonify({'status': 'error', 'message': 'No input config'})
    return jsonify({'status': 'success', 'input': api_conf.input})

@level2_functionBP.route('/api/identity_auth/<int:organization_id>', methods=['POST'])
def identity_auth(organization_id):
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

    # 4. 获取E-DBA平台账户
    edba_account = BankAccount.query.filter_by(bankAccountID=1).first()
    if not edba_account:
        return jsonify({'status': 'error', 'message': 'E-DBA account not found'}), 404

    # 5. 检查余额是否足够
    auth_fee = decimal.Decimal(str(data_user.quota))
    if bank_account.balance < auth_fee:
        return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

    # 6. 获取认证服务
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Student Identity Authentication').first()
    if not service or service.use_status != 'available':
        return jsonify({'status': 'error', 'message': 'Service not available'}), 400

    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf:
        return jsonify({'status': 'error', 'message': 'API not configured'}), 400

    base_url = api_conf.base_url
    path = api_conf.path
    method = api_conf.method
    input_keys = api_conf.input if isinstance(api_conf.input, dict) else {}
    output_keys = api_conf.output if isinstance(api_conf.output, dict) else None
    url = base_url.rstrip('/') + '/' + path.lstrip('/')

    # 处理表单和文件
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = {}
        files = {}
        for key in input_keys.keys():
            if key.lower() == 'photo':
                file = request.files.get(key)
                if file:
                    files[key] = (file.filename, file.read(), file.mimetype)
            else:
                data[key] = request.form.get(key, "")
    else:
        user_data = request.json or {}
        data = {key: user_data.get(key, "") for key in input_keys.keys() if key.lower() != 'photo'}
        files = {}
        if 'photo' in input_keys:
            pass

    try:
        # 7. 转账给E-DBA平台
        bank_account.balance -= auth_fee
        edba_account.balance += auth_fee
        db.session.commit()

        # 8. 调用认证API
        if method.lower() == 'post':
            if files:
                resp = requests.post(url, data=data, files=files, timeout=10)
            else:
                resp = requests.post(url, json=data, timeout=10)
        elif method.lower() == 'get':
            resp = requests.get(url, params=data, timeout=10)
        else:
            # 如果API调用失败，退还费用
            bank_account.balance += auth_fee
            edba_account.balance -= auth_fee
            db.session.commit()
            return jsonify({'status': 'error', 'message': f'Unsupported HTTP method: {method}'}), 400

        if resp.status_code != 200:
            # 如果API调用失败，退还费用
            bank_account.balance += auth_fee
            edba_account.balance -= auth_fee
            db.session.commit()
            return jsonify({'status': 'error', 'message': f'External API error: {resp.status_code}'}), 400

        result = resp.json()
        # 只返回y/n
        status = 'n'
        if isinstance(result, dict):
            if any(str(v).lower() == 'y' for v in result.values()):
                status = 'y'
        elif isinstance(result, str):
            if result.strip().lower() == 'y':
                status = 'y'

        return jsonify({'status': 'success', 'data': status})

    except Exception as e:
        # 如果发生错误，退还费用
        bank_account.balance += auth_fee
        edba_account.balance -= auth_fee
        db.session.commit()
        return jsonify({'status': 'error', 'message': f'API call failed: {str(e)}'}), 500

@level2_functionBP.route('/api/identity_auth_batch/<int:organization_id>', methods=['POST'])
def identity_auth_batch(organization_id):
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

    # 4. 获取E-DBA平台账户
    edba_account = BankAccount.query.filter_by(bankAccountID=1).first()
    if not edba_account:
        return jsonify({'status': 'error', 'message': 'E-DBA account not found'}), 404

    # 5. 获取认证服务
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Student Identity Authentication').first()
    if not service or service.use_status != 'available':
        return jsonify({'status': 'error', 'message': 'Service not available'}), 400

    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf:
        return jsonify({'status': 'error', 'message': 'API not configured'}), 400

    # 6. 处理Excel文件
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        file.save(tmp.name)
        df = pd.read_excel(tmp.name)
    os.unlink(tmp.name)

    # 7. 计算总费用
    total_records = len(df)
    auth_fee = decimal.Decimal(str(data_user.quota))
    total_fee = auth_fee * total_records

    # 8. 检查余额是否足够
    if bank_account.balance < total_fee:
        return jsonify({
            'status': 'error', 
            'message': 'Insufficient balance',
            'data': {
                'balance': float(bank_account.balance),
                'total_fee': float(total_fee),
                'records_count': total_records
            }
        }), 400

    # 9. 扣除费用
    bank_account.balance -= total_fee
    edba_account.balance += total_fee
    db.session.commit()

    # 10. 逐行认证
    results = []
    y_count = 0
    n_count = 0
    base_url = api_conf.base_url
    path = api_conf.path
    method = api_conf.method
    input_keys = api_conf.input if isinstance(api_conf.input, dict) else {}
    output_keys = api_conf.output if isinstance(api_conf.output, dict) else None
    url = base_url.rstrip('/') + '/' + path.lstrip('/')

    try:
        for idx, row in df.iterrows():
            data = {}
            files = {}
            for key in input_keys.keys():
                if key.lower() == 'photo':
                    photo_path = row.get(key)
                    if photo_path and os.path.exists(photo_path):
                        with open(photo_path, 'rb') as f:
                            files[key] = (os.path.basename(photo_path), f.read(), 'image/jpeg')
                else:
                    data[key] = row.get(key, "")
            try:
                if method.lower() == 'post':
                    if files:
                        resp = requests.post(url, data=data, files=files, timeout=10)
                    else:
                        resp = requests.post(url, json=data, timeout=10)
                elif method.lower() == 'get':
                    resp = requests.get(url, params=data, timeout=10)
                else:
                    continue
                if resp.status_code != 200:
                    results.append({'row': idx+2, 'status': 'n'})
                    n_count += 1
                    continue
                result = resp.json()
                status = 'n'
                if isinstance(result, dict):
                    if any(str(v).lower() == 'y' for v in result.values()):
                        status = 'y'
                elif isinstance(result, str):
                    if result.strip().lower() == 'y':
                        status = 'y'
                if status == 'y':
                    y_count += 1
                else:
                    n_count += 1
                results.append({'row': idx+2, 'status': status})
            except Exception as e:
                results.append({'row': idx+2, 'status': 'n'})
                n_count += 1

        return jsonify({
            'status': 'success',
            'data': {
                'y_count': y_count,
                'n_count': n_count,
                'results': results,
                'total_fee': float(total_fee),
                'balance': float(bank_account.balance)
            }
        })

    except Exception as e:
        # 如果发生错误，退还费用
        bank_account.balance += total_fee
        edba_account.balance -= total_fee
        db.session.commit()
        return jsonify({'status': 'error', 'message': f'Batch authentication failed: {str(e)}'}), 500

@level2_functionBP.route('/api/gpa_input_config/<int:organization_id>', methods=['GET'])
def get_gpa_input_config(organization_id):
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Student GPA Record Access').first()
    if not service:
        return jsonify({'status': 'error', 'message': 'Service not found'})
    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf or not api_conf.input:
        return jsonify({'status': 'error', 'message': 'No input config'})
    return jsonify({'status': 'success', 'input': api_conf.input})

@level2_functionBP.route('/api/gpa_query/<int:organization_id>', methods=['POST'])
def gpa_query(organization_id):
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

    # 4. 获取E-DBA平台账户
    edba_account = BankAccount.query.filter_by(bankAccountID=1).first()
    if not edba_account:
        return jsonify({'status': 'error', 'message': 'E-DBA account not found'}), 404

    # 5. 检查余额是否足够
    query_fee = decimal.Decimal(str(data_user.quota))
    if bank_account.balance < query_fee:
        return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

    # 6. 获取GPA查询服务
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Student GPA Record Access').first()
    if not service or service.use_status != 'available':
        return jsonify({'status': 'error', 'message': 'Service not available'}), 400

    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf:
        return jsonify({'status': 'error', 'message': 'API not configured'}), 400

    base_url = api_conf.base_url
    path = api_conf.path
    method = api_conf.method
    input_keys = api_conf.input if isinstance(api_conf.input, dict) else {}
    output_keys = api_conf.output if isinstance(api_conf.output, dict) else None
    url = base_url.rstrip('/') + '/' + path.lstrip('/')

    user_data = request.json or {}
    payload = {key: user_data.get(key, "") for key in input_keys.keys()}

    try:
        # 7. 转账给E-DBA平台
        bank_account.balance -= query_fee
        edba_account.balance += query_fee
        db.session.commit()

        # 8. 调用GPA查询API
        if method.lower() == 'post':
            resp = requests.post(url, json=payload, timeout=10)
        elif method.lower() == 'get':
            resp = requests.get(url, params=payload, timeout=10)
        else:
            # 如果API调用失败，退还费用
            bank_account.balance += query_fee
            edba_account.balance -= query_fee
            db.session.commit()
            return jsonify({'status': 'error', 'message': f'Unsupported HTTP method: {method}'}), 400

        if resp.status_code != 200:
            # 如果API调用失败，退还费用
            bank_account.balance += query_fee
            edba_account.balance -= query_fee
            db.session.commit()
            return jsonify({'status': 'error', 'message': f'External API error: {resp.status_code}'}), 400

        result = resp.json()
        # 只返回output字段内容
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
        # 如果发生错误，退还费用
        bank_account.balance += query_fee
        edba_account.balance -= query_fee
        db.session.commit()
        return jsonify({'status': 'error', 'message': f'API call failed: {str(e)}'}), 500

@level2_functionBP.route('/api/gpa_query_batch/<int:organization_id>', methods=['POST'])
def gpa_query_batch(organization_id):
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

    # 4. 获取E-DBA平台账户
    edba_account = BankAccount.query.filter_by(bankAccountID=1).first()
    if not edba_account:
        return jsonify({'status': 'error', 'message': 'E-DBA account not found'}), 404

    # 5. 获取GPA查询服务
    service = Service.query.filter_by(organizationID=organization_id, serviceName='Student GPA Record Access').first()
    if not service or service.use_status != 'available':
        return jsonify({'status': 'error', 'message': 'Service not available'}), 400

    api_conf = ApiConfig.query.filter_by(serviceID=service.serviceID).first()
    if not api_conf:
        return jsonify({'status': 'error', 'message': 'API not configured'}), 400

    # 6. 处理Excel文件
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
    file = request.files['file']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        file.save(tmp.name)
        df = pd.read_excel(tmp.name)
    os.unlink(tmp.name)

    # 7. 计算总费用
    total_records = len(df)
    query_fee = decimal.Decimal(str(data_user.quota))
    total_fee = query_fee * total_records

    # 8. 检查余额是否足够
    if bank_account.balance < total_fee:
        return jsonify({
            'status': 'error', 
            'message': 'Insufficient balance',
            'data': {
                'balance': float(bank_account.balance),
                'total_fee': float(total_fee),
                'records_count': total_records
            }
        }), 400

    # 9. 扣除费用
    bank_account.balance -= total_fee
    edba_account.balance += total_fee
    db.session.commit()

    # 10. 逐行查询
    results = []
    base_url = api_conf.base_url
    path = api_conf.path
    method = api_conf.method
    input_keys = api_conf.input if isinstance(api_conf.input, dict) else {}
    output_keys = api_conf.output if isinstance(api_conf.output, dict) else None
    url = base_url.rstrip('/') + '/' + path.lstrip('/')

    try:
        for idx, row in df.iterrows():
            data = {key: row.get(key, "") for key in input_keys.keys()}
            try:
                if method.lower() == 'post':
                    resp = requests.post(url, json=data, timeout=10)
                elif method.lower() == 'get':
                    resp = requests.get(url, params=data, timeout=10)
                else:
                    continue
                if resp.status_code != 200:
                    results.append({'row': idx+2, 'status': 'fail', 'data': None})
                    continue
                result = resp.json()
                # 只返回output字段内容
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
                    results.append({'row': idx+2, 'status': 'success', 'data': filtered})
                else:
                    results.append({'row': idx+2, 'status': 'success', 'data': result})
            except Exception as e:
                results.append({'row': idx+2, 'status': 'fail', 'data': None})

        return jsonify({
            'status': 'success',
            'data': {
                'results': results,
                'total_fee': float(total_fee),
                'balance': float(bank_account.balance)
            }
        })

    except Exception as e:
        # 如果发生错误，退还费用
        bank_account.balance += total_fee
        edba_account.balance -= total_fee
        db.session.commit()
        return jsonify({'status': 'error', 'message': f'Batch query failed: {str(e)}'}), 500

@level2_functionBP.route('/api/check_balance/<int:organization_id>', methods=['GET'])
def check_balance(organization_id):
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data_user = DataUser.query.get(user_id)
    if not data_user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

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
            'auth_fee': data_user.quota,
            'query_fee': data_user.quota
        }
    })
