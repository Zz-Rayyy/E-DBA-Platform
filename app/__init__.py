import os
import secrets

from flask import Flask, redirect, url_for

from app.models.user import User
from app.models.registration import Registration
from app.models.organization import Organization
from app.models.dataUser import DataUser
from app.models.convener_data_user import ConvenerDataUser
from app.models.course import Course
from app.models.service import Service
from app.models.api_config import ApiConfig
from app.models.policy import Policy
from app.models.question import Question
from app.models.bank_account import BankAccount
from app.models.account_user import AccountUser
from app.models.fee import Fee
from app.models.paidUser import PaidUser
from app.models.log import Log
from app.views import login, register, E_Admin_registration_review, Senior_E_Admin_registration_review, manage_member, choose_from_organizations, provide_course, service_manage, config_api, level1_function, level2_function, load_policy, browse_policy, add_admin, ask, answer, set_EDBA_bank_account, manage_member_fees, set_up_bank_account, pay_membership_fee, log, check_logs

# 定义注册蓝图方法
def register_blueprints(app):
    #app.register_blueprint(book.bookBP,url_prefix='/book')
    #app.register_blueprint(student.studentBP,url_prefix='/student')
    #app.register_blueprint(teacher.teacherBP,url_prefix='/teacher')
    app.register_blueprint(login.userBP, url_prefix='/user')
    app.register_blueprint(register.registerBP, url_prefix='/register')
    app.register_blueprint(E_Admin_registration_review.admin_registrationBP, url_prefix='/admin_registration')
    app.register_blueprint(Senior_E_Admin_registration_review.senior_adminBP, url_prefix='/senior_admin')
    app.register_blueprint(manage_member.manageBP, url_prefix='/manage_member')
    app.register_blueprint(choose_from_organizations.choose_orgBP, url_prefix='/choose_org')
    app.register_blueprint(provide_course.provide_courseBP, url_prefix='/provide_course')
    app.register_blueprint(service_manage.service_manageBP, url_prefix='/service_manage')
    app.register_blueprint(config_api.config_apiBP, url_prefix='/config_api')
    app.register_blueprint(level1_function.level1_functionBP, url_prefix='/level1_function')
    app.register_blueprint(level2_function.level2_functionBP, url_prefix='/level2_function')
    app.register_blueprint(load_policy.load_policyBP, url_prefix='/load_policy')
    app.register_blueprint(browse_policy.browse_policyBP, url_prefix='/browse_policy')
    app.register_blueprint(add_admin.t_adminBP, url_prefix='/t_admin')
    app.register_blueprint(ask.askBP, url_prefix='/ask')
    app.register_blueprint(answer.answerBP, url_prefix='/answer')
    app.register_blueprint(set_EDBA_bank_account.set_bank_accountBP, url_prefix='/set_bank_account')
    app.register_blueprint(manage_member_fees.manage_member_feesBP, url_prefix='/manage_member_fees')
    app.register_blueprint(set_up_bank_account.set_up_bank_accountBP, url_prefix='/set_up_bank_account')
    app.register_blueprint(pay_membership_fee.pay_membership_feeBP, url_prefix='/pay_membership_fee')
    app.register_blueprint(log.logBP, url_prefix='/log')
    app.register_blueprint(check_logs.check_logsBP, url_prefix='/check_logs')
# 注册插件(数据库关联)
def register_plugin(app):
    from app.models.base import db
    db.init_app(app)
    # create_all要放到app上下文环境中使用
    #app.config['SQLALCHEMY_ECHO'] = True
    with app.app_context():
        db.create_all()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
    # app.config.from_object('app.config.setting') # 基本配置(setting.py)
    app.config.from_object('app.config.secure') # 重要参数配置(secure.py)
    # 注册蓝图与app对象相关联
    register_blueprints(app)

    @app.route('/')
    def index():
        return redirect(url_for('user.login'))

    # 注册插件(数据库)与app对象相关联
    register_plugin(app)
    # 一定要记得返回app
    return app
