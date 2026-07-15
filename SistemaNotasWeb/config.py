import os

class Config:
    # Caminho base do projeto
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Segurança
    SECRET_KEY = 'sua_chave_secreta_super_segura'
    
    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB

# Garante que a pasta de uploads exista
if not os.path.exists(Config.UPLOAD_FOLDER):
    os.makedirs(Config.UPLOAD_FOLDER)