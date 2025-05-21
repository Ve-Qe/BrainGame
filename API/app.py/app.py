from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Configuração do banco SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o banco
db = SQLAlchemy(app)

# ✅ Garante que o banco será criado antes da primeira requisição
@app.before_first_request
def criar_banco_automaticamente():
    db.create_all()

# Modelo do usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)

# Rota de status (GET)
@app.route('/')
def home():
    return "API Flask ativa e funcionando!", 200

# Rota de cadastro (POST)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    senha = data.get('senha')

    if not username or not senha:
        return jsonify({'error': 'Campos obrigatórios'}), 400

    if Usuario.query.filter_by(username=username).first():
        return jsonify({'error': 'Usuário já existe'}), 400

    senha_hash = generate_password_hash(senha)
    novo_usuario = Usuario(username=username, senha_hash=senha_hash)
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({'message': 'Usuário registrado com sucesso'}), 201

# Rota de login (POST)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    senha = data.get('senha')

    if not username or not senha:
        return jsonify({'error': 'Campos obrigatórios'}), 400

    usuario = Usuario.query.filter_by(username=username).first()
    if not usuario or not check_password_hash(usuario.senha_hash, senha):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    return jsonify({'message': 'Login bem-sucedido'}), 200
