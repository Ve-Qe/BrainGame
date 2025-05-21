from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Criação da aplicação Flask
app = Flask(__name__)
CORS(app)

# Configuração do banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa o SQLAlchemy
db = SQLAlchemy(app)

# Modelo de dados do usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)

# Criar o banco automaticamente antes do primeiro request
@app.before_first_request
def criar_banco():
    with app.app_context():
        db.create_all()

# Rota de teste
@app.route('/', methods=['GET'])
def home():
    return "API Flask ativa e funcionando!", 200

# Rota de cadastro
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

# Rota de login
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

# Execução da aplicação
if __name__ == '__main__':
    app.run(debug=True)
