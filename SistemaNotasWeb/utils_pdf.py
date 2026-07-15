import pdfplumber
import re
import logging
from datetime import datetime

def converter_valor(valor_str):
    if not valor_str: return 0.0
    try:
        # Remove R$, espaços e lixo, mantendo apenas números, pontos e vírgulas
        limpo = re.sub(r'[^\d,.-]', '', str(valor_str))
        if ',' in limpo and '.' in limpo:
            limpo = limpo.replace('.', '').replace(',', '.')
        elif ',' in limpo:
            limpo = limpo.replace(',', '.')
        return float(limpo)
    except:
        return 0.0

def converter_data(data_str):
    if not data_str: return None
    # Procura o padrão dia/mes/ano ou ano-mes-dia
    match = re.search(r'(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})', str(data_str))
    if match:
        data_texto = match.group(1)
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try:
                return datetime.strptime(data_texto, fmt).date()
            except:
                continue
    return None

class PDFParser:
    def __init__(self, path):
        self.path = path
        self.text = ""
        self.full_content = []
        self._carregar_pdf()

    def _carregar_pdf(self):
        with pdfplumber.open(self.path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                self.text += page_text + "\n"
                self.full_content.extend(page_text.split('\n'))

    def buscar_multiplo(self, regex_list):
        """Tenta vários padrões até encontrar um"""
        for regex in regex_list:
            match = re.search(regex, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""

    def extrair_por_proximidade(self, palavra_chave, linhas_abaixo=1):
        """Busca uma palavra e tenta pegar o valor na linha seguinte ou ao lado"""
        for i, linha in enumerate(self.full_content):
            if palavra_chave.lower() in linha.lower():
                # Tenta pegar na mesma linha após os dois pontos
                if ":" in linha:
                    res = linha.split(":", 1)[1].strip()
                    if res: return res
                # Se não achou na linha, olha a linha de baixo
                if i + linhas_abaixo < len(self.full_content):
                    return self.full_content[i + linhas_abaixo].strip()
        return ""

    def ler_pdf(self):
        # 1. Extração de Números e Datas (Geralmente no topo)
        numero = self.buscar_multiplo([
            r'Número da Nota\s+([\d.]+)', 
            r'Número da Nota Fiscal[:.\s]+(\d+)',
            r'NFS-e\s+nº\s+(\d+)',
            r'Nº\s*(\d{3,})'
        ])
        
        data_emissao = self.buscar_multiplo([
            r'Data e Hora de Emissão\s*(\d{2}/\d{2}/\d{4})',
            r'Emissão[:.\s]+(\d{2}/\d{2}/\d{4})',
            r'Data[:.\s]+(\d{2}/\d{2}/\d{4})'
        ])

        # 2. Prestador (Foca no topo do documento)
        # Pegamos o primeiro CNPJ que aparecer (Prestador)
        cnpj_prestador = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', self.text)
        cnpj = cnpj_prestador.group(0) if cnpj_prestador else ""

        # 3. Campos Específicos de Publicidade (Dentro da Discriminação/Descrição)
        # Estes campos costumam vir após palavras-chave no meio do texto
        campanha = self.buscar_multiplo([
            r'CAMPANHA[:.\s]+([^\n|]+)',
            r'Observação[:.\s]+CAMPANHA[:.\s]+([^\n]+)',
            r'Produto/Ação[:.\s]+([^\n]+)'
        ])
        
        pi = self.buscar_multiplo([
            r'Número de PI[:.\s]+(\d+)',
            r'Pedido de Inserção[:.\s]+(\d+)',
            r'PI\s*[nºNº]*[:.\s]+(\d+)'
        ])

        contrato = self.buscar_multiplo([
            r'CONTRATO[:.\s]+(\d+/\d+)',
            r'CONTRATO[:.\s]+(\d{2,})'
        ])

        # 4. Valores (Busca o Valor Líquido ou Total)
        valor_bruto = self.buscar_multiplo([
            r'VALOR TOTAL DA NOTA\s*=\s*R?\s*([\d.,]+)',
            r'VALOR TOTAL DO SERVIÇO\s*=\s*R?\s*([\d.,]+)',
            r'VALOR LÍQUIDO DA NOTA FISCAL\s*R?\s*([\d.,]+)',
            r'Total da Nota\s*R?\s*([\d.,]+)'
        ])

        return {
            'numero': numero,
            'serie': self.buscar_multiplo([r'Série[:.\s]+(\d+)', r'Série da Nota[:.\s]+(\d+)']),
            'data_emissao': converter_data(data_emissao),
            'fornecedor': self.extrair_por_proximidade("Razão Social"),
            'cnpj': cnpj,
            'contrato': contrato,
            'campanha': campanha,
            'pi': pi,
            'valor': converter_valor(valor_bruto),
            'descricao': self.text[:500] # Para conferência rápida
        }