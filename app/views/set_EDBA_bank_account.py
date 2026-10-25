from flask import Blueprint, request, jsonify, session
from app.models.bank_account import BankAccount
from app.models.account_user import AccountUser
from app.models.user import User
from app.models.base import db

set_bank_accountBP = Blueprint('set_bank_account', __name__)

@set_bank_accountBP.route('/api/save_bank_account', methods=['POST'])
def save_bank_account():
    # 获取当前登录的E-Admin用户ID
    user_id = session.get('userID')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    # 验证用户是否为E-Admin
    user = User.query.get(user_id)
    if not user or user.userType != 'E-Admin':
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    # 获取表单数据
    bank = request.form.get('bank')
    account = request.form.get('account')
    name = request.form.get('name')
    password = request.form.get('password')
    balance = request.form.get('balance')

    if not all([bank, account, name, password, balance]):
        return jsonify({'status': 'error', 'message': 'Missing required fields'})

    try:
        # 创建银行账户
        bank_account = BankAccount(
            bank=bank,
            account=account,
            name=name,
            password=password,
            balance=balance
        )
        db.session.add(bank_account)
        db.session.flush()  # 获取新创建的bank_accountID

        # 创建账户用户关联
        account_user = AccountUser(
            userID=user_id,
            bankAccountID=bank_account.bankAccountID
        )
        db.session.add(account_user)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Bank account saved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to save bank account: {str(e)}'
        })
