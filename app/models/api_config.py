from flask import Flask
from sqlalchemy import Column, Integer, String, DateTime, JSON, func, ForeignKey
from app.models.base import Base, SQLAlchemy

# app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:xxx@127.0.0.1:3306/xxx"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

class ApiConfig(Base):
    __tablename__ = 'api_config'
    id = Column(Integer, primary_key=True, autoincrement=True)
    serviceID = Column(Integer, ForeignKey('service.serviceID'), nullable=False)
    base_url = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)
    method = Column(String(10), nullable=False)
    input = Column(JSON, nullable=True)
    output = Column(JSON, nullable=True)

    def __init__(self, serviceID, base_url, path, method, input=None, output=None):
        super(ApiConfig, self).__init__()
        self.serviceID = serviceID
        self.base_url = base_url
        self.path = path
        self.method = method
        self.input = input
        self.output = output

# if __name__=='__main__':
#     db.create_all()
#     db.session.commit()
#     app.run(debug=True)
