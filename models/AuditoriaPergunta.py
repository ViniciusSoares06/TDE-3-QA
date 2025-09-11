from database import db
from sqlalchemy import Enum

ResultadoEnum = Enum('CONFORME', 'NAO_CONFORME', 'NAO_APLICAVEL', name='situacao_enum')

class AuditoriaPergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resultado = db.Column(ResultadoEnum, nullable=True)
    observacoes = db.Column(db.String(255), nullable=True)

    auditoria_checklist_id = db.Column(db.Integer, db.ForeignKey('auditoria_checklist.id'), nullable=False)
    pergunta_id = db.Column(db.Integer, db.ForeignKey('template_pergunta.id'), nullable=False)

    auditoria_checklist = db.relationship('AuditoriaChecklist', backref='perguntas', lazy=True)
    pergunta = db.relationship('TemplatePergunta', backref='perguntas', lazy=True)