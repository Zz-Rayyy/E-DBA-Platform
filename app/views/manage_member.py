from flask import Blueprint, request, jsonify, session, render_template
from app.models.user import User
from app.models.dataUser import DataUser
from app.models.convener_data_user import ConvenerDataUser
from app.models.organization import Organization
from app.models.registration import Registration
from app.models.question import Question
from app.models.paidUser import PaidUser
from app.models.base import db

manageBP = Blueprint('manage', __name__)

@manageBP.route('/o_convener_workspace', methods=['GET'])
def o_convener_workspace():
    user_id = session.get('userID')
    org_name = ""
    user_email = ""
    organization_id = None
    
    if user_id:
        reg = Registration.query.filter_by(userID=user_id, status='Final_approved').first()
        organization = None
        if reg and reg.organizationID:
            organization = Organization.query.filter_by(organizationID=reg.organizationID).first()
            organization_id = reg.organizationID
        if organization:
            org_name = organization.organizationNameInFull
        user = User.query.get(user_id)
        if user:
            user_email = user.email
    
    if not organization_id:
        return jsonify({'status': 'error', 'message': 'No valid organization found'}), 404
        
    return render_template('O-Convener_workspace.html', 
                         org_name=org_name, 
                         user_email=user_email,
                         organization_id=organization_id)

@manageBP.route('/api/members', methods=['GET'])
def get_members():
    convener_id = session.get('userID')
    if not convener_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    data_user_ids = db.session.query(ConvenerDataUser.dataUserID).filter_by(userID=convener_id).all()
    data_user_ids = [row[0] for row in data_user_ids]
    members = []
    if data_user_ids:
        data_users = DataUser.query.filter(DataUser.userID.in_(data_user_ids)).all()
        for m in data_users:
            user = User.query.get(m.userID)
            members.append({
                'userID': m.userID,
                'name': m.name,
                'email': user.email if user else "",
                'accessRight': m.accessRight,
                'quota': m.quota
            })
    return jsonify({'status': 'success', 'data': members})

@manageBP.route('/api/member', methods=['POST'])
def add_member():
    data = request.form
    name = data.get('name')
    email = data.get('email')
    accessRight = int(data.get('accessRight'))
    quota = int(data.get('quota'))
    convener_id = session.get('userID')
    if not all([name, email, accessRight is not None, quota is not None, convener_id]):
        return jsonify({'status': 'error', 'message': 'Missing fields'})
    # 获取organizationID
    reg = Registration.query.filter_by(userID=convener_id, status='Final_approved').first()
    if not reg or not reg.organizationID:
        return jsonify({'status': 'error', 'message': 'No valid organization found for this O-Convener'})
    organizationID = reg.organizationID
    try:
        user = User(email=email, userType='DataUser')
        db.session.add(user)
        db.session.flush()
        data_user = DataUser(
            userID=user.userID,
            name=name,
            accessRight=accessRight,
            account=0,
            quota=quota,
            organizationID=organizationID
        )
        db.session.add(data_user)
        db.session.flush()
        convener_data_user = ConvenerDataUser(userID=convener_id, dataUserID=user.userID)
        db.session.add(convener_data_user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Member added'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Fail to add member: {e}'})

@manageBP.route('/api/member/<int:user_id>', methods=['POST'])
def edit_member(user_id):
    data = request.form
    name = data.get('name')
    accessRight = int(data.get('accessRight'))
    quota = int(data.get('quota'))
    data_user = DataUser.query.get(user_id)
    if not data_user:
        return jsonify({'status': 'error', 'message': 'Member not found'})
    data_user.name = name
    data_user.accessRight = accessRight
    data_user.quota = quota
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Member updated'})

@manageBP.route('/api/member/<int:user_id>', methods=['DELETE'])
def delete_member(user_id):
    data_user = DataUser.query.get(user_id)
    user = User.query.get(user_id)
    convener_id = session.get('userID')
    convener_data_user = ConvenerDataUser.query.filter_by(userID=convener_id, dataUserID=user_id).first()
    if not data_user or not user or not convener_data_user:
        return jsonify({'status': 'error', 'message': 'Member not found'})
    
    try:
        # 先删除该用户的所有问答记录
        Question.query.filter_by(userID=user_id).delete()
        
        # 删除paidUser表中的记录
        PaidUser.query.filter_by(userID=user_id).delete()
        
        # 然后删除其他相关记录
        db.session.delete(convener_data_user)
        db.session.delete(data_user)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Member deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to delete member: {str(e)}'})

@manageBP.route('/api/members/batch', methods=['POST'])
def batch_add_members():
    members = request.json.get('members', [])
    convener_id = session.get('userID')
    reg = Registration.query.filter_by(userID=convener_id, status='Final_approved').first()
    if not reg or not reg.organizationID:
        return jsonify({'status': 'error', 'message': 'No valid organization found for this O-Convener'})
    organizationID = reg.organizationID
    try:
        for m in members:
            user = User(email=m['email'], userType='DataUser')
            db.session.add(user)
            db.session.flush()
            data_user = DataUser(
                userID=user.userID,
                name=m['name'],
                accessRight=m['accessRight'],
                account=0,
                quota=m['quota'],
                organizationID=organizationID
            )
            db.session.add(data_user)
            db.session.flush()
            convener_data_user = ConvenerDataUser(userID=convener_id, dataUserID=user.userID)
            db.session.add(convener_data_user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Batch members added'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Fail to add members: {e}'})