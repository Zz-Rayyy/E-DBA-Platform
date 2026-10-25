from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary, Numeric
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class BankAccount(Base):
    __tablename__ = 'bank_account'
    bankAccountID = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    account = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    bank = Column(String(100), nullable=False)
    balance = Column(Numeric(20, 9), nullable=False)

    def __init__(self, name, account, password, bank, balance):
        super(BankAccount, self).__init__()
        self.name = name
        self.account = account
        self.password = password
        self.bank = bank
        self.balance = balance
        
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)