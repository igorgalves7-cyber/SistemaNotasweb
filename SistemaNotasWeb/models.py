from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Nota(db.Model):
    __tablename__ = 'notas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50))
    serie = db.Column(db.String(20))
    data_emissao = db.Column(db.Date)
    data_recebimento = db.Column(db.DateTime, default=datetime.now)
    
    fornecedor = db.Column(db.String(255))
    cnpj = db.Column(db.String(25))
    contrato = db.Column(db.String(100))
    demanda = db.Column(db.String(100))
    campanha = db.Column(db.String(255))
    pi = db.Column(db.String(50))
    
    valor = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='Pendente')
    nup = db.Column(db.String(100))
    pdf = db.Column(db.String(255))