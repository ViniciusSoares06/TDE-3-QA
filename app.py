from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

perguntas = [
    "O Plano de Projeto foi criado?",
    "O Repositório do projeto foi criado corretamente?",
    "O Plano de Gerência de Configuração foi elaborado?",
    "O Plano de Gerência de Configuração segue o template oficial?",
    "Os itens de configuração foram identificados corretamente?",
    "Os commits seguem o padrão estabelecido?",
    "O Plano de Garantia da Qualidade foi criado?",
    "O Plano de Garantia da Qualidade foi aprovado?",
    "As avaliações de qualidade foram realizadas conforme cronograma?",
    "As Não Conformidades foram registradas corretamente?",
    "Houve comunicação das advertências aos responsáveis?",
    "As ações corretivas foram solicitadas e acompanhadas?",
    "As resoluções das Não Conformidades foram verificadas?",
    "O Relatório de Garantia da Qualidade foi gerado?",
    "As medidas de qualidade foram coletadas e analisadas?"
]


@app.route("/")
def home():
    return render_template('auditorias.html')


@app.route('/checklist')
def checklist():
    return render_template('checklist.html', perguntas=perguntas)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)

