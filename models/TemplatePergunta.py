from database import db

class TemplatePergunta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    
    template_checklist_id = db.Column(db.Integer, db.ForeignKey('template_checklist.id'), nullable=False)

    template_checklist = db.relationship('TemplateChecklist', backref='perguntas', lazy=True)
    