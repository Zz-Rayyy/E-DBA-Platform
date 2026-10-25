from flask import Blueprint, request, jsonify, session
from app.models.fee import Fee
from app.models.dataUser import DataUser
from app.models.user import User
from app.models.bank_account import BankAccount
from app.models.account_user import AccountUser
from app.models.convener_data_user import ConvenerDataUser
from app.models.paidUser import PaidUser
from app.models.base import db
import requests
from sqlalchemy import desc

pay_membership_feeBP = Blueprint('pay_membership_fee', __name__)

# 获取最新的费用结构
@pay_membership_feeBP.route('/api/fee_structure', methods=['GET'])
def get_fee_structure():
    try:
        # 获取最新的费用记录
        latest_fee = Fee.query.order_by(desc(Fee.create_time)).first()
        if not latest_fee:
            return jsonify({'status': 'error', 'message': 'No fee structure found'})

        return jsonify({
            'status': 'success',
            'data': {
                'level1Fee': float(latest_fee.level1Fee),
                'level2Fee': float(latest_fee.level2Fee),
                'level3Fee': float(latest_fee.level3Fee)
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 获取支付摘要
@pay_membership_feeBP.route('/api/payment_summary', methods=['GET'])
def get_payment_summary():
    try:
        # 获取当前用户的ID
        user_id = session.get('userID')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

        # 获取最新的费用记录
        latest_fee = Fee.query.order_by(desc(Fee.create_time)).first()
        if not latest_fee:
            return jsonify({'status': 'error', 'message': 'No fee structure found'})

        # 通过convenerDataUser表获取组织成员
        convener_members = ConvenerDataUser.query.filter_by(userID=user_id).all()
        member_ids = [m.dataUserID for m in convener_members]
        
        # 获取所有成员的信息
        members = DataUser.query.filter(DataUser.userID.in_(member_ids)).all()
        
        # 获取已支付会员费的成员ID列表
        paid_member_ids = [p.userID for p in PaidUser.query.filter(PaidUser.userID.in_(member_ids)).all()]
        
        # 过滤出未支付的成员
        unpaid_members = [m for m in members if m.userID not in paid_member_ids]
        
        # 统计各等级未支付成员数量
        level1_count = sum(1 for m in unpaid_members if m.accessRight == 1)
        level2_count = sum(1 for m in unpaid_members if m.accessRight == 2)
        level3_count = sum(1 for m in unpaid_members if m.accessRight == 3)

        # 计算总金额
        level1_total = level1_count * float(latest_fee.level1Fee)
        level2_total = level2_count * float(latest_fee.level2Fee)
        level3_total = level3_count * float(latest_fee.level3Fee)
        total_amount = level1_total + level2_total + level3_total

        return jsonify({
            'status': 'success',
            'data': {
                'totalMembers': len(members),
                'paidMembers': len(paid_member_ids),
                'unpaidMembers': len(unpaid_members),
                'level1Count': level1_count,
                'level2Count': level2_count,
                'level3Count': level3_count,
                'level1Fee': float(latest_fee.level1Fee),
                'level2Fee': float(latest_fee.level2Fee),
                'level3Fee': float(latest_fee.level3Fee),
                'level1Total': level1_total,
                'level2Total': level2_total,
                'level3Total': level3_total,
                'totalAmount': total_amount
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 处理支付
@pay_membership_feeBP.route('/api/pay', methods=['POST'])
def pay_fees():
    try:
        # 获取当前用户ID
        user_id = session.get('userID')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

        # 获取最新的费用记录
        latest_fee = Fee.query.order_by(desc(Fee.create_time)).first()
        if not latest_fee:
            return jsonify({'status': 'error', 'message': 'No fee structure found'})

        # 通过convenerDataUser表获取组织成员
        convener_members = ConvenerDataUser.query.filter_by(userID=user_id).all()
        member_ids = [m.dataUserID for m in convener_members]
        
        # 获取所有成员的信息
        members = DataUser.query.filter(DataUser.userID.in_(member_ids)).all()
        
        # 获取已支付会员费的成员ID列表
        paid_member_ids = [p.userID for p in PaidUser.query.filter(PaidUser.userID.in_(member_ids)).all()]
        
        # 过滤出未支付的成员
        unpaid_members = [m for m in members if m.userID not in paid_member_ids]
        
        # 计算总金额（只计算未支付成员的费用）
        total_amount = sum(
            float(latest_fee.level1Fee) if m.accessRight == 1 else
            float(latest_fee.level2Fee) if m.accessRight == 2 else
            float(latest_fee.level3Fee)
            for m in unpaid_members
        )

        if total_amount == 0:
            return jsonify({'status': 'success', 'message': 'No fees to pay'})

        # 获取组织的银行账户
        org_account_user = AccountUser.query.filter_by(userID=user_id).first()
        if not org_account_user:
            return jsonify({'status': 'error', 'message': 'Organization bank account not found'})
        
        org_bank_account = BankAccount.query.get(org_account_user.bankAccountID)
        if not org_bank_account:
            return jsonify({'status': 'error', 'message': 'Organization bank account not found'})

        # 获取E-DBA的银行账户
        e_admin = User.query.filter_by(userType='E-Admin').first()
        if not e_admin:
            return jsonify({'status': 'error', 'message': 'E-DBA account not found'})

        e_admin_account_user = AccountUser.query.filter_by(userID=e_admin.userID).first()
        if not e_admin_account_user:
            return jsonify({'status': 'error', 'message': 'E-DBA bank account not found'})

        e_admin_bank_account = BankAccount.query.get(e_admin_account_user.bankAccountID)
        if not e_admin_bank_account:
            return jsonify({'status': 'error', 'message': 'E-DBA bank account not found'})

        # 检查余额是否足够
        if float(org_bank_account.balance) < total_amount:
            return jsonify({'status': 'error', 'message': 'Insufficient balance'})

        # 调用转账API
        transfer_data = {
            "from_bank": org_bank_account.bank,
            "from_name": org_bank_account.name,
            "from_account": org_bank_account.account,
            "password": org_bank_account.password,
            "to_bank": e_admin_bank_account.bank,
            "to_name": e_admin_bank_account.name,
            "to_account": e_admin_bank_account.account,
            "amount": int(total_amount * 100)  # 转换为分
        }

        response = requests.post(
            'http://172.16.160.88:8001/hw/bank/transfer',
            json=transfer_data
        )

        if response.status_code != 200 or response.json().get('status') != 'success':
            return jsonify({
                'status': 'error',
                'message': f'Transfer failed: {response.json().get("reason", "Unknown error")}'
            })

        # 更新账户余额
        org_bank_account.balance = float(org_bank_account.balance) - total_amount
        e_admin_bank_account.balance = float(e_admin_bank_account.balance) + total_amount

        # 将未支付成员添加到paidUser表
        for member in unpaid_members:
            paid_user = PaidUser(userID=member.userID)
            db.session.add(paid_user)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'Successfully paid {total_amount} RMB for membership fees'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})
