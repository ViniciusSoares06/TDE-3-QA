from database import db

class AuditoriaChecklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    data_auditoria = db.Column(db.DateTime, nullable=False)
    aderencia = db.Column(db.Float, nullable=True)

    auditor_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    template_checklist_id = db.Column(db.Integer, db.ForeignKey('template_checklist.id'), nullable=False)

    auditor = db.relationship('Usuario', backref='auditorias', lazy=True)
    template_checklist = db.relationship('TemplateChecklist', backref='auditorias', lazy=True)

