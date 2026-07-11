import fitz
import re


def ler_pdf(caminho_pdf):

    pdf = fitz.open(caminho_pdf)

    # Lê apenas a primeira página (onde está a NF)
    texto = pdf[0].get_text()

    pdf.close()

    dados = {
        "numero": "",
        "serie": "",
        "fornecedor": "",
        "cnpj": "",
        "valor": "",
        "data_emissao": "",
        "codigo_autenticacao": ""
    }

    # Número da Nota
    numero = re.search(r"Número da Nota Fiscal\s*(\d+)", texto)
    if numero:
        dados["numero"] = numero.group(1)

    # Série
    serie = re.search(r"Série do Documento\s*(.+?)\s*Número da Nota Fiscal", texto, re.S)
    if serie:
        dados["serie"] = serie.group(1).strip()

    # Fornecedor
    fornecedor = re.search(
        r"Dados do Prestador de Serviço\s*(.*?)\n",
        texto,
        re.S
    )

    if fornecedor:
        dados["fornecedor"] = fornecedor.group(1).strip()

    # CNPJ
    cnpj = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto)
    if cnpj:
        dados["cnpj"] = cnpj.group()

    # Data
    data = re.search(r"\d{2}/\d{2}/\d{4}", texto)
    if data:
        dados["data_emissao"] = data.group()

    # Código de autenticação
    codigo = re.search(r"Cód\. de Autenticação\s*([A-Z0-9]+)", texto)
    if codigo:
        dados["codigo_autenticacao"] = codigo.group(1)

    # Valor
    valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", texto)

    if valores:
        dados["valor"] = valores[-1]

    return dados