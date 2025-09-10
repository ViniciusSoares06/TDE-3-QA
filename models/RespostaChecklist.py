from database import db

class RespostaChecklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    checklist_name = db.Column(db.String(255), nullable=False)
    pergunta = db.Column(db.String(255), nullable=True)
    resultado = db.Column(db.String(255), nullable=True)
    responsavel = db.Column(db.String(255), nullable=True)
    classificacao_nc = db.Column(db.String(255), nullable=True)
    acao_corretiva = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.String(255), nullable=True)
    data = db.Column(db.DateTime, nullable=True)