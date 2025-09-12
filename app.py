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
from database import db
from models.TemplatePergunta import TemplatePergunta
from models.TemplateChecklist import TemplateChecklist
from models.AuditoriaPergunta import AuditoriaPergunta
from models.AuditoriaChecklist import AuditoriaChecklist
from models.Usuario import Usuario
from models.NaoConformidade import NaoConformidade, SituacaoEnum, ClassificacaoEnum
from flask import flash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = '123'
db.init_app(app)


PERGUNTAS = [
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

def inicializar_perguntas():
    checklist = TemplateChecklist.query.filter_by(nome="Padrão").first()
    if not checklist:
        checklist = TemplateChecklist(nome="Padrão")
        db.session.add(checklist)
        db.session.commit()
    for pergunta in PERGUNTAS:
        existe = TemplatePergunta.query.filter_by(descricao=pergunta).first()
        if not existe:
            nova_pergunta = TemplatePergunta(
                descricao=pergunta,
                template_checklist=checklist
            )
            db.session.add(nova_pergunta)
    db.session.commit()

def adicionar_dias_uteis(data_inicio, dias):
    dias_adicionados = 0
    data_atual = data_inicio
    while dias_adicionados < dias:
        data_atual += timedelta(days=1)
        if data_atual.weekday() < 5:
            dias_adicionados += 1
    return data_atual


def gerar_pdf_nc(nc):
    arquivo = f"NC_{nc.id}.pdf"
    c = canvas.Canvas(arquivo, pagesize=A4)
    largura, altura = A4

    # Dados fixos
    data_solicitacao = datetime.now().date()
    
    # Acessando atributos do objeto NaoConformidade
    classificacao = nc.classificacao if nc.classificacao else "leve"
    # dias_prazo = {"urgente": 1, "media": 2, "leve": 3}.get(classificacao, 3)
    # prazo_resolucao = adicionar_dias_uteis(data_solicitacao, dias_prazo)
    
    responsavel_nome = nc.responsavel.nome if nc.responsavel else ""
    acao_corretiva = nc.acao_corretiva or ""
    observacoes = getattr(nc.auditoria_pergunta, "observacoes", "") or ""
    situacao = nc.situacao if nc.situacao else "em_aberto"

    # Cabeçalho
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, altura - 50, "Solicitação de Resolução de Não Conformidade")

    c.setFont("Helvetica", 10)
    c.drawString(50, altura - 100, f"Código de Controle: NC-{nc.id:03d}")
    c.drawString(300, altura - 100, f"Projeto: Exemplo")
    c.drawString(50, altura - 120, f"Responsável: {responsavel_nome}")

    # Datas e prazos
    c.drawString(50, altura - 160, f"Data da 1ª Solicitação: {data_solicitacao.strftime('%d/%m/%Y')}")
    c.drawString(300, altura - 160, f"Prazo de Resolução: {nc.data_limite.strftime('%d/%m/%Y')}")
    c.drawString(50, altura - 180, "Data da Solução: _______")
    c.drawString(300, altura - 180, "Nº de Escalonamentos: 1")
    c.drawString(50, altura - 200, "RQA Responsável: _______")

    # Descrição
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, altura - 230, "Você tem 24 horas úteis para contestação")

    c.setFont("Helvetica", 10)
    c.drawString(50, altura - 260, f"Descrição: {observacoes}")
    c.drawString(50, altura - 280, f"Classificação: {classificacao}")
    c.drawString(50, altura - 300, f"Ação Corretiva indicada: {acao_corretiva}")
    c.drawString(50, altura - 320, f"Situação: {situacao}")

    # Escalonamento
    c.drawString(50, altura - 360, f"Histórico de Escalonamento: {nc.escalonamento}")
    c.drawString(300, altura - 360, "Superior Responsável: Kelly")
    c.drawString(50, altura - 380, f"Prazo para Resolução: {nc.data_limite.strftime('%d/%m/%Y')}")

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
    inicializar_perguntas()
    return redirect(url_for('auditorias'))


@app.route('/auditorias')
def auditorias():
    inicializar_perguntas()
    auditorias = AuditoriaChecklist.query.order_by(AuditoriaChecklist.data_auditoria.desc()).all()
    return render_template('auditorias.html', auditorias=auditorias)


@app.route('/auditoria/<int:checklist_id>')
def detalhes_auditoria(checklist_id):
    checklist = AuditoriaChecklist.query.get_or_404(checklist_id)
    respostas = checklist.perguntas
    return render_template('checklist_detalhes.html', checklist=checklist, respostas=respostas)


@app.route('/dashboard')
def dashboard():
    respostas = AuditoriaPergunta.query.all()
    for pergunta in respostas:
        print(pergunta.auditoria_checklist)
    return render_template('dashboard.html', respostas=respostas)


@app.route('/NCs')
def NCs():
    NCsInfos = NaoConformidade.query.all()
    
    nc_dict = {nc.auditoria_pergunta_id: nc for nc in NCsInfos}

    NCs = AuditoriaPergunta.query.filter(
        AuditoriaPergunta.id.in_([nc.auditoria_pergunta_id for nc in NCsInfos])
    ).all()

    return render_template('NCs.html', NCs=NCs, nc_dict=nc_dict)


@app.route("/nc/<int:nc_id>/atualizar_status", methods=["POST"])
def atualizar_status_nc(nc_id):
    novo_status = request.form.get("status")

    mapeamento = {
        "Aberta": "em_aberto",
        "Em Andamento": "em_andamento",
        "Resolvida": "encerrada"
    }

    nc = NaoConformidade.query.get(nc_id)
    if nc and novo_status in mapeamento:
        nc.situacao = mapeamento[novo_status]
        db.session.commit()
    else:
        flash("Erro ao atualizar status.", "error")

    return redirect(url_for("NCs"))



@app.route('/enviar_email_nc/<int:nc_id>', methods=['POST'])
def enviar_email_nc_manual(nc_id):
    nc = NaoConformidade.query.get_or_404(nc_id)

    if not nc.data_limite:
        dias_prazo = {"urgente": 1, "media": 2, "leve": 3}.get(nc.classificacao, 3)
        nc.data_limite = adicionar_dias_uteis(datetime.now().date(), dias_prazo)
        db.session.commit()

    if not nc.responsavel:
        flash("Erro: Não há responsável definido para esta NC.", "error")
        return redirect(url_for('NCs'))

    arquivo_pdf = gerar_pdf_nc(nc)
    email_responsavel = nc.responsavel.email
    nome_responsavel = nc.responsavel.nome

    try:
        enviar_email_nc(
            destinatario=email_responsavel,
            assunto=f"Não Conformidade NC-{nc.id:03d}",
            corpo=f"Olá {nome_responsavel},\n\nSegue anexo o relatório da NC-{nc.id:03d}.",
            arquivo_pdf=arquivo_pdf
        )
        flash(f"Email enviado com sucesso para {nome_responsavel}!", "success")
    except Exception as e:
        flash(f"Erro ao enviar email: {e}", "error")

    return redirect(url_for('NCs'))

@app.route('/nc/<int:nc_id>/escalonar', methods=['POST'])
def escalonar_nc(nc_id):
    nc = NaoConformidade.query.get_or_404(nc_id)
    nc.escalonamento = (nc.escalonamento or 0) + 1
    dias_prazo = {"urgente": 1, "media": 2, "leve": 3}.get(nc.classificacao, 3)
    nc.data_limite = adicionar_dias_uteis(datetime.now().date(), dias_prazo)
    db.session.commit()
    flash(f"Escalonamento adicionado para NC-{nc.id:03d}.", "success")
    return redirect(url_for('NCs'))



@app.route('/checklist', methods=['GET', 'POST'])
def checklist():
    if request.method == 'POST':
        respostas = request.form
        checklistId = respostas.get("checklist-id")
        checklist = TemplateChecklist.query.get(checklistId)

        auditoria_checklist = AuditoriaChecklist(
            nome=checklist.nome,
            data_auditoria=datetime.now(),
            template_checklist_id=checklist.id,
            auditor_id=1
        )
        db.session.add(auditoria_checklist)
        db.session.commit()

        perguntas = TemplatePergunta.query.all()

        for pergunta in perguntas:
            perguntaId = pergunta.id
            resultado = respostas.get(f"resultado[{perguntaId}]") or "NAO_APLICAVEL"
            responsavel_email = respostas.get(f"responsavel[{perguntaId}]")
            classificacao_nc = respostas.get(f"classificacao-nc[{perguntaId}]")
            acao_corretiva = respostas.get(f"acao-corretiva[{perguntaId}]")
            situacao_nc = respostas.get(f"situacao-nc[{perguntaId}]")
            observacoes = respostas.get(f"observacoes[{perguntaId}]")

            if resultado == "NAO_CONFORME":
                if not (responsavel_email and classificacao_nc and acao_corretiva and situacao_nc and observacoes):
                    db.session.rollback()
                    return """
                        <script>
                            alert("Preencha todos os campos da Não Conformidade antes de salvar!");
                            history.go(-1);
                        </script>
                    """

            auditoria_resposta = AuditoriaPergunta(
                resultado=resultado,
                auditoria_checklist_id=auditoria_checklist.id,
                pergunta_id=perguntaId,
                observacoes=observacoes
            )
            db.session.add(auditoria_resposta)
            db.session.commit()

            if resultado == "NAO_CONFORME" and responsavel_email:
                responsavel = Usuario.query.filter_by(email=responsavel_email).first()
                if not responsavel:
                    responsavel = Usuario(nome=responsavel_email.split("@")[0], email=responsavel_email)
                    db.session.add(responsavel)
                    db.session.commit()

                nc = NaoConformidade(
                    classificacao=classificacao_nc,
                    acao_corretiva=acao_corretiva,
                    situacao=situacao_nc,
                    responsavel=responsavel,
                    auditoria_pergunta=auditoria_resposta
                )

                db.session.add(nc)
                db.session.commit()

        naoAplicaveis = AuditoriaPergunta.query.filter_by(
            auditoria_checklist_id=auditoria_checklist.id,
            resultado="NAO_APLICAVEL"
        ).count()
        conformes = AuditoriaPergunta.query.filter_by(
            auditoria_checklist_id=auditoria_checklist.id,
            resultado="CONFORME"
        ).count()
        auditoria_checklist.aderencia = conformes / (len(perguntas) - naoAplicaveis) if (len(perguntas) - naoAplicaveis) > 0 else 0
        db.session.commit()

        return redirect(url_for("checklist"))

    else:
        perguntas = TemplatePergunta.query.all()
        checklist = TemplateChecklist.query.filter_by(nome="Padrão").first()
        return render_template('checklist.html', perguntas=perguntas, checklist=checklist)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)

