from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


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


def adicionar_dias_uteis(data_inicio, dias):
    dias_adicionados = 0
    data_atual = data_inicio
    while dias_adicionados < dias:
        data_atual += timedelta(days=1)
        if data_atual.weekday() < 5:
            dias_adicionados += 1
    return data_atual


def gerar_pdf_nc(nc, indice):
    arquivo = f"NC_{indice}.pdf"
    c = canvas.Canvas(arquivo, pagesize=A4)
    largura, altura = A4

    # Dados fixos
    data_solicitacao = datetime.now().date()
    classificacao = nc.get("classificacao-nc", "").lower()
    dias_prazo = {"urgente": 1, "media": 2, "leve": 3}.get(classificacao, 3)
    prazo_resolucao = adicionar_dias_uteis(data_solicitacao, dias_prazo)

    # Cabeçalho
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, altura - 50, "Solicitação de Resolução de Não Conformidade")

    c.setFont("Helvetica", 10)
    c.drawString(50, altura - 100, f"Código de Controle: NC-{indice:03d}")
    c.drawString(300, altura - 100, f"Projeto: Exemplo")
    c.drawString(50, altura - 120, f"Responsável: {nc.get('responsavel', '')}")

    # Datas e prazos
    c.drawString(50, altura - 160, f"Data da 1ª Solicitação: {data_solicitacao.strftime('%d/%m/%Y')}")
    c.drawString(300, altura - 160, f"Prazo de Resolução: {prazo_resolucao.strftime('%d/%m/%Y')}")
    c.drawString(50, altura - 180, "Data da Solução: _______")
    c.drawString(300, altura - 180, "Nº de Escalonamentos: 1")
    c.drawString(50, altura - 200, "RQA Responsável: _______")

    # Descrição
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, altura - 230, "Você tem 24 horas úteis para contestação")

    c.setFont("Helvetica", 10)
    c.drawString(50, altura - 260, f"Descrição: {nc.get('observacoes', '')}")
    c.drawString(50, altura - 280, f"Classificação: {nc.get('classificacao-nc', '')}")
    c.drawString(50, altura - 300, f"Ação Corretiva indicada: {nc.get('acao-corretiva', '')}")

    # Escalonamento
    c.drawString(50, altura - 340, "Histórico de Escalonamento: 1")
    c.drawString(300, altura - 340, "Superior Responsável: Kelly")
    c.drawString(50, altura - 360, f"Prazo para Resolução: {prazo_resolucao.strftime('%d/%m/%Y')}")

    # Observações
    c.drawString(50, altura - 400, f"Observações: {nc.get('observacoes', '')}")

    # Rodapé
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, 50, "O relatório de não conformidade de testes deve seguir as regras de gerência de configuração.")

    c.save()
    return arquivo


def enviar_email_nc(destinatario, assunto, corpo, arquivo_pdf):
    smtp_servidor = "smtp.gmail.com"
    smtp_porta = 587
    email_remetente = "vsoaressilva06@gmail.com"
    senha = "vbdr mwuz pjtk kppn"

    mensagem = MIMEMultipart()
    mensagem['From'] = email_remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto

    mensagem.attach(MIMEText(corpo, 'plain'))

    with open(arquivo_pdf, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {arquivo_pdf}")
        mensagem.attach(part)

    try:
        server = smtplib.SMTP(smtp_servidor, smtp_porta)
        server.starttls()
        server.login(email_remetente, senha)
        server.send_message(mensagem)
        server.quit()
        print(f"Email enviado para {destinatario} com o arquivo {arquivo_pdf}")
    except Exception as e:
        print(f"Erro ao enviar email para {destinatario}: {e}")


@app.route("/")
def home():
    return redirect(url_for('auditorias'))


@app.route('/auditorias')
def auditorias():
    return render_template('auditorias.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/NCs')
def NCs():
    return render_template('NCs.html')


@app.route('/checklist', methods=['GET', 'POST'])
def checklist():
    if request.method == 'POST':
        respostas = request.form 
        
        dados = {}
        for key, value in respostas.items():
            nome, idx = key.split("[")
            idx = idx.strip("]")

            if idx not in dados:
                dados[idx] = {}
            dados[idx][nome] = value

        nao_conformes = {
            i: item
            for i, item in dados.items()
            if item.get("resultado", "").lower() == "nao"
        }

        for i, nc in nao_conformes.items():
            arquivo_pdf = gerar_pdf_nc(nc, int(i))
            destinatario = nc.get("responsavel", "").strip()

            if destinatario:
                enviar_email_nc(
                    destinatario,
                    assunto=f"Não Conformidade NC-{int(i):03d}",
                    corpo=(
                        f"Olá,\n\n"
                        f"Segue em anexo o relatório da Não Conformidade NC-{int(i):03d}.\n"
                        f"Por favor, verifique e tome as ações necessárias.\n\n"
                        f"Atenciosamente,\nEquipe de Qualidade"
                    ),
                    arquivo_pdf=arquivo_pdf
                )

        print("PDFs gerados e emails enviados para os responsáveis!")

        return redirect(url_for("checklist"))
    else:
        return render_template('checklist.html', perguntas=perguntas)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)

