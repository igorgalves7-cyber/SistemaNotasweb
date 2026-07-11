import os
import re
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import pdfplumber

app = Flask(__name__)


# ==========================
# CONFIGURAÇÃO
# ==========================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "database.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# ==========================
# LEITURA DO PDF
# ==========================

def extrair_dados_pdf(caminho):
    dados = {
        "numero": "",
        "serie": "",
        "data_emissao": "",
        "data_recebimento": "",
        "fornecedor": "",
        "nome_fantasia": "",
        "cnpj": "",
        "contrato": "",
        "demanda": "",
        "campanha": "",
        "pi": "",
        "tipo_servico": "",
        "meio": "",
        "descricao": "",
        "tipo_praca": "",
        "praca": "",
        "valor": "",
        "valor_veiculacao": "",
        "ocorrencia": "",
        "conferente": "",
        "nup": "",
        "data_envio": "",
        "data_pagamento": ""
    }

    texto = ""
    with pdfplumber.open(caminho) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() or ""

    # Imprime todo o texto extraído para depuração de expressões regulares
    print("="*80)
    print(texto)
    print("="*80)

    # Número
    m = re.search(r"Número da Nota Fiscal\s+(\d+)", texto)
    if m:
        dados["numero"] = m.group(1)

    # Série
    m = re.search(r"Série do Documento\s+Nota Fiscal de Serviço\s+Eletrônica - NFS-e", texto)
    if m:
        dados["serie"] = "NFS-e"

    # Data de emissão
    m = re.search(r"Data de Geração da NFS-e\s+(\d{2}/\d{2}/\d{4})", texto)
    if m:
        dados["data_emissao"] = converter_data(m.group(1))

    # Fornecedor
    m = re.search(r"Raz[aã]o Social[:\s]+(.+)", texto, re.IGNORECASE)
    if m:
        dados["fornecedor"] = m.group(1).strip()
    else:
        m = re.search(r"Dados do Prestador de Serviço\s+([A-ZÇÃÕÁÉÍÓÚ ]+LTDA)", texto)
        if m:
            dados["fornecedor"] = m.group(1).strip()

    # Nome fantasia
    m = re.search(r"Nome Fantasia[:\s]+(.+)", texto, re.IGNORECASE)
    if m:
        dados["nome_fantasia"] = m.group(1).strip()

    # CNPJ
    m = re.search(r"CPF/CNPJ\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", texto)
    if m:
        dados["cnpj"] = m.group(1)

    # Contrato
    m = re.search(r"CONTRATO DE PUBLICIDADE Nº\s*([\d/]+)", texto)
    if m:
        dados["contrato"] = m.group(1)

    # Demanda
    m = re.search(r"Referente a ação:\s*([\d/]+)", texto)
    if m:
        dados["demanda"] = m.group(1)

    # Campanha
    m = re.search(r"Campanha:\s*([A-ZÇÃÕÁÉÍÓÚ ]+)", texto)
    if m:
        dados["campanha"] = m.group(1).strip()

    # PI
    m = re.search(r"PP\s*(\d+)", texto)
    if m:
        dados["pi"] = m.group(1)

    # Tipo de serviço
    m = re.search(r"1\)\s*Tipo:\s*([^;]+)", texto)
    if m:
        dados["tipo_servico"] = m.group(1).strip()

    # Meio
    m = re.search(r"18\)\s*Utilização:\s*([^\.]+)", texto)
    if m:
        dados["meio"] = m.group(1).strip()

    # Descrição
    m = re.search(r"20\)\s*Descrição:\s*(.*?)22\)", texto, re.S)
    if m:
        dados["descricao"] = " ".join(m.group(1).split())

    # Praça
    m = re.search(r"19\)\s*Praças:\s*([^;.\n]+)", texto)
    if m:
        dados["praca"] = m.group(1).strip()
        dados["tipo_praca"] = "Nacional"

    # Valor da Nota
    m = re.search(r"Vl\. Total dos Serviços\s*R\$\s*([\d\.,]+)", texto)
    if m:
        dados["valor"] = converter_valor(m.group(1))

    # Valor da Veiculação
    dados["valor_veiculacao"] = dados["valor"]

    # Fallback / Segunda checagem se não encontrar os campos principais
    if not dados["numero"]:
        m = re.search(r"N[úu]mero.*?(\d+)", texto, re.IGNORECASE)
        if m:
            dados["numero"] = m.group(1)

    if not dados["serie"]:
        m = re.search(r"S[ée]rie.*?(\d+)", texto, re.IGNORECASE)
        if m:
            dados["serie"] = m.group(1)

    if not dados["data_emissao"]:
        m = re.search(r"(\d{2}/\d{2}/\d{4})", texto)
        if m:
            dados["data_emissao"] = converter_data(m.group(1))

    if not dados["cnpj"]:
        m = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
        if m:
            dados["cnpj"] = m.group(0)

    if not dados["valor"]:
        valores = re.findall(r"R\$\s*([\d\.\,]+)", texto)
        if valores:
            dados["valor"] = converter_valor(valores[-1])
            dados["valor_veiculacao"] = dados["valor"]

    return dados


# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def converter_data(data):

    if not data:
        return ""

    try:
        return datetime.strptime(
            data,
            "%d/%m/%Y"
        ).strftime("%Y-%m-%d")

    except:
        return data


def converter_valor(valor):

    if not valor:
        return 0

    if isinstance(valor, (int, float)):
        return float(valor)

    valor = (
        valor
        .replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return float(valor)
    except:
        return 0


# ==========================
# MODELO
# ==========================

class Nota(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    numero = db.Column(db.String(30), nullable=False)
    serie = db.Column(db.String(20))

    data_emissao = db.Column(db.String(20))
    data_recebimento = db.Column(db.String(20))

    fornecedor = db.Column(db.String(150), nullable=False)
    nome_fantasia = db.Column(db.String(150))
    cnpj = db.Column(db.String(20))

    contrato = db.Column(db.String(50))
    demanda = db.Column(db.String(50))
    campanha = db.Column(db.String(150))
    pi = db.Column(db.String(50))

    tipo_servico = db.Column(db.String(100))
    meio = db.Column(db.String(100))
    descricao = db.Column(db.Text)

    tipo_praca = db.Column(db.String(100))
    praca = db.Column(db.String(100))

    valor = db.Column(db.Float, default=0)
    valor_veiculacao = db.Column(db.Float, default=0)

    status = db.Column(
        db.String(30),
        default="Recebida"
    )

    ocorrencia = db.Column(db.Text)

    conferente = db.Column(db.String(100))
    nup = db.Column(db.String(100))

    data_envio = db.Column(db.String(20))
    data_pagamento = db.Column(db.String(20))

    pdf = db.Column(db.String(255))


with app.app_context():
    db.create_all()

# ==========================
# DASHBOARD
# ==========================

@app.route("/")
def dashboard():

    pesquisa = request.args.get("pesquisa", "")

    if pesquisa:

        notas = Nota.query.filter(
            (Nota.numero.contains(pesquisa)) |
            (Nota.fornecedor.contains(pesquisa)) |
            (Nota.campanha.contains(pesquisa)) |
            (Nota.cnpj.contains(pesquisa))
        ).all()

    else:

        notas = Nota.query.all()

    return render_template(
        "dashboard.html",
        notas=notas,
        pesquisa=pesquisa
    )


# ==========================
# IMPORTAR PDF
# ==========================

@app.route("/importar_pdf", methods=["POST"])
def importar_pdf():

    arquivo = request.files.get("arquivo")

    if not arquivo or arquivo.filename == "":
        return redirect(url_for("receber"))

    nome_pdf = secure_filename(arquivo.filename)

    caminho_pdf = os.path.join(
        app.config["UPLOAD_FOLDER"],
        nome_pdf
    )

    arquivo.save(caminho_pdf)

    dados = extrair_dados_pdf(caminho_pdf)

    if not dados:
        dados = {}

    dados["data_emissao"] = converter_data(
        dados.get("data_emissao", "")
    )

    dados["valor"] = converter_valor(
        dados.get("valor", "")
    )

    return render_template(
        "receber.html",
        dados=dados
    )


# ==========================
# RECEBER NOTA
# ==========================

@app.route("/receber", methods=["GET", "POST"])
def receber():
    if request.method == "POST":
        print("CHEGOU NO POST")

        arquivo = request.files.get("pdf")

        nome_pdf = ""

        if arquivo and arquivo.filename != "":

            nome_pdf = secure_filename(
                arquivo.filename
            )

            arquivo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nome_pdf
                )
            )

        nova_nota = Nota(

            numero=request.form.get("numero"),

            serie=request.form.get("serie"),

            data_emissao=request.form.get("data_emissao"),

            data_recebimento=request.form.get(
                "data_recebimento"
            ),

            fornecedor=request.form.get(
                "fornecedor"
            ),

            nome_fantasia=request.form.get(
                "nome_fantasia"
            ),

            cnpj=request.form.get("cnpj"),

            contrato=request.form.get(
                "contrato"
            ),

            demanda=request.form.get(
                "demanda"
            ),

            campanha=request.form.get(
                "campanha"
            ),

            pi=request.form.get("pi"),

            tipo_servico=request.form.get(
                "tipo_servico"
            ),

            meio=request.form.get("meio"),

            descricao=request.form.get(
                "descricao"
            ),

            tipo_praca=request.form.get(
                "tipo_praca"
            ),

            praca=request.form.get("praca"),

            valor=converter_valor(
                request.form.get("valor")
            ),

            valor_veiculacao=converter_valor(
                request.form.get(
                    "valor_veiculacao"
                )
            ),

            ocorrencia=request.form.get(
                "ocorrencia"
            ),

            conferente=request.form.get(
                "conferente"
            ),

            nup=request.form.get("nup"),

            data_envio=request.form.get(
                "data_envio"
            ),

            data_pagamento=request.form.get(
                "data_pagamento"
            ),

            pdf=nome_pdf

        )

        db.session.add(nova_nota)

        print("VAI SALVAR")
        db.session.commit()
        print("SALVOU")

        return redirect("/")

    return render_template(
        "receber.html",
        dados={}
    )

# ==========================
# EDITAR NOTA
# ==========================

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    nota = Nota.query.get_or_404(id)

    if request.method == "POST":

        arquivo = request.files.get("pdf")

        if arquivo and arquivo.filename != "":
            nome_pdf = secure_filename(arquivo.filename)

            arquivo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nome_pdf
                )
            )

            nota.pdf = nome_pdf

        nota.numero = request.form.get("numero")
        nota.serie = request.form.get("serie")
        nota.data_emissao = request.form.get("data_emissao")
        nota.data_recebimento = request.form.get("data_recebimento")

        nota.fornecedor = request.form.get("fornecedor")
        nota.nome_fantasia = request.form.get("nome_fantasia")
        nota.cnpj = request.form.get("cnpj")

        nota.contrato = request.form.get("contrato")
        nota.demanda = request.form.get("demanda")
        nota.campanha = request.form.get("campanha")
        nota.pi = request.form.get("pi")

        nota.tipo_servico = request.form.get("tipo_servico")
        nota.meio = request.form.get("meio")
        nota.descricao = request.form.get("descricao")

        nota.tipo_praca = request.form.get("tipo_praca")
        nota.praca = request.form.get("praca")

        nota.valor = converter_valor(
            request.form.get("valor")
        )

        nota.valor_veiculacao = converter_valor(
            request.form.get("valor_veiculacao")
        )

        nota.ocorrencia = request.form.get("ocorrencia")
        nota.conferente = request.form.get("conferente")
        nota.nup = request.form.get("nup")

        nota.data_envio = request.form.get("data_envio")
        nota.data_pagamento = request.form.get("data_pagamento")

        db.session.commit()

        return redirect("/")

    return render_template(
        "editar.html",
        nota=nota
    )


# ==========================
# EXCLUIR
# ==========================

@app.route("/excluir/<int:id>")
def excluir(id):

    nota = Nota.query.get_or_404(id)

    db.session.delete(nota)
    db.session.commit()

    return redirect("/")


# ==========================
# APROVAR
# ==========================

@app.route("/aprovar/<int:id>")
def aprovar(id):

    nota = Nota.query.get_or_404(id)

    nota.status = "Aprovada"

    db.session.commit()

    return redirect("/")


# ==========================
# PENDÊNCIA
# ==========================

@app.route("/pendencia/<int:id>")
def pendencia(id):

    nota = Nota.query.get_or_404(id)

    nota.status = "Pendência"

    db.session.commit()

    return redirect("/")


# ==========================
# PAGAR
# ==========================

@app.route("/pagar/<int:id>")
def pagar(id):

    nota = Nota.query.get_or_404(id)

    nota.status = "Paga"

    db.session.commit()

    return redirect("/")


# ==========================
# VISUALIZAR PDF
# ==========================

@app.route("/visualizar/<int:id>")
def visualizar(id):

    nota = Nota.query.get_or_404(id)

    if not nota.pdf:
        return redirect("/")

    return redirect("/static/uploads/" + nota.pdf)


# ==========================
# ESTATÍSTICAS
# ==========================

@app.context_processor
def dashboard_stats():

    total_notas = Nota.query.count()

    recebidas = Nota.query.filter_by(
        status="Recebida"
    ).count()

    aprovadas = Nota.query.filter_by(
        status="Aprovada"
    ).count()

    pendencias = Nota.query.filter_by(
        status="Pendência"
    ).count()

    pagas = Nota.query.filter_by(
        status="Paga"
    ).count()

    valor_total = db.session.query(
        db.func.sum(Nota.valor)
    ).scalar() or 0

    valor_pago = db.session.query(
        db.func.sum(Nota.valor)
    ).filter(
        Nota.status == "Paga"
    ).scalar() or 0

    return dict(
        total_notas=total_notas,
        recebidas=recebidas,
        aprovadas=aprovadas,
        pendencias=pendencias,
        pagas=pagas,
        valor_total=valor_total,
        valor_pago=valor_pago
    )


# ==========================
# EXECUTAR
# ==========================

if __name__ == "__main__":
    app.run(debug=True)