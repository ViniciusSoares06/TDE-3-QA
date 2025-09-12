from database import db
from sqlalchemy import Enum

ClassificacaoEnum = Enum('leve', 'media', 'urgente', name='classificacao_enum')
SituacaoEnum = Enum('em_aberto', 'em_andamento', 'encerrada', name='situacao_enum')

class NaoConformidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classificacao = db.Column(
        ClassificacaoEnum,
        default='leve',
        nullable=False
    )
    acao_corretiva = db.Column(db.String(255), nullable=True)
    situacao = db.Column(
        SituacaoEnum,
        default='em_aberto',
        nullable=False
    )
    escalonamento = db.Column(db.Integer, default=0, nullable=True)

    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    auditoria_pergunta_id = db.Column(db.Integer, db.ForeignKey('auditoria_pergunta.id'), nullable=True)

    responsavel = db.relationship('Usuario', backref='nao_conformidades', lazy=True)
    auditoria_pergunta = db.relationship('AuditoriaPergunta', backref='nao_conformidades', lazy=True)