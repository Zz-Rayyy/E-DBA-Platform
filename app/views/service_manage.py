from flask import Blueprint, request, jsonify, session
from app.models.organization import Organization
from app.models.service import Service
from app.models.registration import Registration
from app.models.base import db
from app.models.api_config import ApiConfig

service_manageBP = Blueprint('service_manage', __name__)

# 获取所有可选组织（用于"部分公开"下拉框）
@service_manageBP.route('/api/organizations', methods=['GET'])
def get_organizations():
    convener_id = session.get('userID')
    org_id_to_exclude = None
    if convener_id:
        reg = Registration.query.filter_by(userID=convener_id, status='Final_approved').first()
        if reg and reg.organizationID:
            org_id_to_exclude = reg.organizationID

    query = Organization.query
    if org_id_to_exclude:
        organizations = query.filter(Organization.organizationID != org_id_to_exclude).all()
    else:
        organizations = query.all()
    return jsonify({
        'status': 'success',
        'data': [{
            'organizationID': org.organizationID,
            'organizationNameInFull': org.organizationNameInFull
        } for org in organizations]
    })

# 获取当前组织已配置的服务
@service_manageBP.route('/api/services', methods=['GET'])
def get_services():
    convener_id = session.get('userID')
    reg = Registration.query.filter_by(userID=convener_id, status='Final_approved').first()
    if not reg or not reg.organizationID:
        return jsonify({'status': 'error', 'message': 'No valid organization found'})
    org_id = reg.organizationID
    services = Service.query.filter_by(organizationID=org_id).all()
    all_part_borrow = Service.query.filter(Service.use_status=='borrow', Service.open_status=='part').all()
    data = {}
    # 先处理普通服务
    for s in services:
        selected_orgs = []
        if s.open_status == 'part':
            selected_orgs = [str(b.organizationID) for b in all_part_borrow if b.serviceName == s.serviceName]
        data[s.serviceName] = {
            'enabled': True,
            'visibility': s.open_status,
            'selectedOrgs': selected_orgs
        }
    # 处理Thesis Sharing逻辑
    thesis_enabled = ('Search Thesis' in data and 'Get Thesis PDF' in data)
    data['Thesis Sharing'] = {
        'enabled': thesis_enabled,
        'visibility': data['Search Thesis']['visibility'] if 'Search Thesis' in data else 'private',
        'selectedOrgs': data['Search Thesis']['selectedOrgs'] if 'Search Thesis' in data else []
    }
    # 其他服务未开启
    for name in ['Course Information Sharing', 'Student Identity Authentication', 'Student GPA Record Access']:
        if name not in data:
            data[name] = {
                'enabled': False,
                'visibility': 'private',
                'selectedOrgs': []
            }
    return jsonify({'status': 'success', 'data': data})

# 保存服务配置
@service_manageBP.route('/api/services', methods=['POST'])
def save_services():
    convener_id = session.get('userID')
    reg = Registration.query.filter_by(userID=convener_id, status='Final_approved').first()
    if not reg or not reg.organizationID:
        return jsonify({'status': 'error', 'message': 'No valid organization found'})
    org_id = reg.organizationID
    data = request.json
    try:
        for key, val in data.items():
            # Thesis Sharing特殊处理
            if key == 'Thesis Sharing':
                # 需要插入/删除Search Thesis和Get Thesis PDF
                for sub_service in ['Search Thesis', 'Get Thesis PDF']:
                    service = Service.query.filter_by(serviceName=sub_service, organizationID=org_id).first()
                    if val['enabled']:
                        if not service:
                            s = Service(serviceName=sub_service, use_status='unavailable', open_status=val['visibility'], organizationID=org_id)
                            db.session.add(s)
                        else:
                            if service.open_status != val['visibility']:
                                service.open_status = val['visibility']
                    else:
                        if service:
                            # 删除api_config
                            ApiConfig.query.filter_by(serviceID=service.serviceID).delete()
                            db.session.delete(service)
                continue
            # 其他服务
            service = Service.query.filter_by(serviceName=key, organizationID=org_id).first()
            if val['enabled']:
                if not service:
                    s = Service(serviceName=key, use_status='unavailable', open_status=val['visibility'], organizationID=org_id)
                    db.session.add(s)
                else:
                    if service.open_status != val['visibility']:
                        service.open_status = val['visibility']
                if val['visibility'] == 'part':
                    exist_borrow = Service.query.filter_by(serviceName=key, use_status='borrow', open_status='part').all()
                    exist_borrow_orgs = set([str(s.organizationID) for s in exist_borrow])
                    selected_orgs = set(val.get('selectedOrgs', []))
                    for oid in selected_orgs - exist_borrow_orgs:
                        s2 = Service(serviceName=key, use_status='borrow', open_status='part', organizationID=int(oid))
                        db.session.add(s2)
                    for s in exist_borrow:
                        if str(s.organizationID) not in selected_orgs:
                            # 删除api_config
                            ApiConfig.query.filter_by(serviceID=s.serviceID).delete()
                            db.session.delete(s)
                else:
                    borrow_services = Service.query.filter_by(serviceName=key, use_status='borrow', open_status='part').all()
                    for s in borrow_services:
                        # 删除api_config
                        ApiConfig.query.filter_by(serviceID=s.serviceID).delete()
                        db.session.delete(s)
            else:
                if service:
                    # 删除api_config
                    ApiConfig.query.filter_by(serviceID=service.serviceID).delete()
                    db.session.delete(service)
                borrow_services = Service.query.filter_by(serviceName=key, use_status='borrow', open_status='part').all()
                for s in borrow_services:
                    # 删除api_config
                    ApiConfig.query.filter_by(serviceID=s.serviceID).delete()
                    db.session.delete(s)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Service configuration saved'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Fail to save: {e}'})