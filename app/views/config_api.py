from flask import Blueprint, request, jsonify
from app.models.service import Service
from app.models.api_config import ApiConfig
from app.models.registration import Registration
from app.models.base import db

config_apiBP = Blueprint('config_api', __name__)

# 获取当前 DataProvider 可配置的服务
@config_apiBP.route('/api/configurable_services/<int:organization_id>', methods=['GET'])
def get_configurable_services(organization_id):
    services = Service.query.filter(Service.organizationID == organization_id, Service.use_status.in_(['unavailable', 'available'])).all()
    data = []
    for s in services:
        if s.serviceName == 'Course Information Sharing':
            # course服务不需要API配置，available即为可用
            if s.use_status != 'available':
                s.use_status = 'available'
                db.session.commit()
            data.append({
                'serviceID': s.serviceID,
                'serviceName': s.serviceName,
                'use_status': 'available',
                'api_config': None
            })
        elif s.serviceName in ['Search Thesis', 'Get Thesis PDF', 'Student Identity Authentication', 'Student GPA Record Access']:
            api_conf = ApiConfig.query.filter_by(serviceID=s.serviceID).first()
            data.append({
                'serviceID': s.serviceID,
                'serviceName': s.serviceName,
                'use_status': s.use_status,
                'api_config': {
                    'base_url': api_conf.base_url if api_conf else '',
                    'path': api_conf.path if api_conf else '',
                    'method': api_conf.method if api_conf else '',
                    'input': api_conf.input if api_conf else '',
                    'output': api_conf.output if api_conf else ''
                } if api_conf else None
            })
    return jsonify({'status': 'success', 'data': data})

# 配置API（新增或更新）
@config_apiBP.route('/api/config_api/<int:organization_id>', methods=['POST'])
def config_api(organization_id):
    data = request.json
    serviceID = data.get('serviceID')
    base_url = data.get('base_url')
    path = data.get('path')
    method = data.get('method')
    input_json = data.get('input')
    output_json = data.get('output')

    service = Service.query.filter_by(serviceID=serviceID, organizationID=organization_id).first()
    if not service:
        return jsonify({'status': 'error', 'message': 'Service not found'})
    try:
        api_conf = ApiConfig.query.filter_by(serviceID=serviceID).first()
        if not api_conf:
            api_conf = ApiConfig(
                serviceID=serviceID,
                base_url=base_url,
                path=path,
                method=method,
                input=input_json,
                output=output_json
            )
            db.session.add(api_conf)
        else:
            api_conf.base_url = base_url
            api_conf.path = path
            api_conf.method = method
            api_conf.input = input_json
            api_conf.output = output_json
        # 配置成功后，服务状态变为 available
        service.use_status = 'available'
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'API configuration saved and service is now available'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Fail to save: {e}'})
