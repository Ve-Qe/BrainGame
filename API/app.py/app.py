from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ✅ Cria as tabelas ao carregar o app
with app.app_context():
    db.create_all()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)

@app.route('/')
def home():
    return "API Flask ativa e funcionando!", 200

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    senha = data.get('senha')

    if Usuario.query.filter_by(username=username).first():
        return jsonify({'error': 'Usuário já existe'}), 400

    senha_hash = generate_password_hash(senha)
    novo_usuario = Usuario(username=username, senha_hash=senha_hash)
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({'message': 'Usuário registrado com sucesso'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    senha = data.get('senha')

    usuario = Usuario.query.filter_by(username=username).first()
    if not usuario or not check_password_hash(usuario.senha_hash, senha):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    return jsonify({'message': 'Login bem-sucedido'}), 200
