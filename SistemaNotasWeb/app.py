from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Nota
from utils_pdf import PDFParser, converter_valor, converter_data
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Dashboard com termos técnicos do Senado: Empenhado, Liquidado, Pago
    notas = Nota.query.order_by(Nota.id.desc()).all()
    stats = {
        'valor_total': db.session.query(func.sum(Nota.valor)).scalar() or 0.0,
        'pendentes': Nota.query.filter(Nota.status != 'Pago').count(),
        'pagas': Nota.query.filter_by(status='Pago').count(),
        'total_docs': Nota.query.count()
    }
    return render_template('dashboard.html', notas=notas, stats=stats)

@app.route('/importar', methods=['GET', 'POST'])
def importar():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            
            parser = PDFParser(path)
            dados = parser.ler_pdf()
            dados['pdf'] = filename
            return render_template('receber.html', dados=dados)
    return render_template('receber.html', dados=None)

@app.route('/salvar', methods=['POST'])
def salvar():
    try:
        nova = Nota(
            numero=request.form.get('numero'),
            serie=request.form.get('serie'),
            data_emissao=converter_data(request.form.get('data_emissao')),
            fornecedor=request.form.get('fornecedor'),
            cnpj=request.form.get('cnpj'),
            campanha=request.form.get('campanha'),
            contrato=request.form.get('contrato'),
            pi=request.form.get('pi'),
            valor=converter_valor(request.form.get('valor')),
            status='Aguardando Liquidação',
            nup=request.form.get('nup'),
            pdf=request.form.get('pdf')
        )
        db.session.add(nova)
        db.session.commit()
        flash('Documento registrado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao registrar: {e}', 'danger')
    return redirect(url_for('index'))

# ESTA É A ROTA QUE ESTAVA FALTANDO E CAUSANDO O ERRO
@app.route('/excluir/<int:id>')
def excluir(id):
    nota = Nota.query.get_or_404(id)
    db.session.delete(nota)
    db.session.commit()
    flash('Documento removido do acervo.', 'info')
    return redirect(url_for('index'))

@app.route('/status/<int:id>/<novo_status>')
def alterar_status(id, novo_status):
    nota = Nota.query.get_or_404(id)
    nota.status = novo_status
    db.session.commit()
    flash(f'Status atualizado para {novo_status}', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)