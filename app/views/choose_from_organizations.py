from flask import Blueprint, render_template, session, jsonify, redirect, url_for
from app.models.dataUser import DataUser
from app.models.organization import Organization
from app.models.user import User

choose_orgBP = Blueprint('choose_org', __name__)

@choose_orgBP.route('/datauser/organizations', methods=['GET'])
def datauser_organizations_page():
    user_id = session.get('userID')
    user = User.query.get(user_id)
    user_email = user.email if user else ''
    return render_template('DataUser_page.html', user_email=user_email)

@choose_orgBP.route('/datauser/api/organizations', methods=['GET'])
def get_datauser_organizations():
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    data_user = DataUser.query.get(user_id)
    if not data_user or not data_user.organizationID:
        return jsonify({'status': 'success', 'data': []})
    org = Organization.query.get(data_user.organizationID)
    if not org:
        return jsonify({'status': 'success', 'data': []})
    data = [{
        'organizationID': org.organizationID,
        'organizationNameInFull': org.organizationNameInFull,
        'organizationNameInShort': org.organizationNameInShort
    }]
    return jsonify({'status': 'success', 'data': data})

@choose_orgBP.route('/datauser/organization/<int:org_id>/workspace', methods=['GET'])
def datauser_enter_workspace(org_id):
    user_id = session.get('userID')
    data_user = DataUser.query.get(user_id)
    org = Organization.query.get(org_id)
    if not data_user or not org:
        return "Not found", 404
    user_email = User.query.get(user_id).email if user_id else ''
    if data_user.accessRight == 3:
        return render_template('Private-DataUser_workspace.html', user_email=user_email, org_name=org.organizationNameInFull, user_id=user_id, organization_id=org.organizationID)
    elif data_user.accessRight == 2:
        return render_template('Public-DataUser_workspace_2.html', user_email=user_email, org_name=org.organizationNameInFull, user_id=user_id, organization_id=org.organizationID)
    else:
        return render_template('Public-DataUser_workspace_1.html', user_email=user_email, org_name=org.organizationNameInFull, user_id=user_id, organization_id=org.organizationID)
