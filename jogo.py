import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import os
import sqlite3
import hashlib
from datetime import datetime

# Configurações
CAMINHO_IMAGENS = "imagens"
DB_FILE = "usuarios.db"

# Itens disponíveis
itens = [
    {"nome": "Boneca Abalabu", "chance": 50, "imagem": "boneca.png"},
    {"nome": "Frigo Camelo", "chance": 30, "imagem": "frigo.png"},
    {"nome": "Chimpanzini Bananini", "chance": 15, "imagem": "bananini.png"},
    {"nome": "Girafa Celeste", "chance": 5, "imagem": "girafa.png"},
]

# Variáveis globais
usuario_logado = None
inventario = {}
historico = []

# ------------------------------
# Banco de dados e funções
# ------------------------------

def conectar_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Cria tabelas se não existirem
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE,
        senha TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventario (
        usuario_id INTEGER,
        nome TEXT,
        quantidade INTEGER,
        imagem TEXT,
        PRIMARY KEY (usuario_id, nome),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        nome TEXT,
        data TEXT,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')
    conn.commit()
    return conn, cursor

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def criar_usuario(nome, senha):
    conn, cursor = conectar_db()
    try:
        cursor.execute("INSERT INTO usuarios (nome, senha) VALUES (?, ?)", (nome, hash_senha(senha)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def validar_login(nome, senha):
    conn, cursor = conectar_db()
    cursor.execute("SELECT id, senha FROM usuarios WHERE nome = ?", (nome,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        usuario_id, senha_hash = resultado
        if senha_hash == hash_senha(senha):
            return usuario_id
    return None

def carregar_inventario(usuario_id):
    global inventario
    inventario = {}
    conn, cursor = conectar_db()
    cursor.execute("SELECT nome, quantidade, imagem FROM inventario WHERE usuario_id = ?", (usuario_id,))
    for nome, quantidade, imagem in cursor.fetchall():
        inventario[nome] = {"quantidade": quantidade, "imagem": imagem}
    conn.close()

def salvar_item(usuario_id, nome, imagem):
    conn, cursor = conectar_db()
    cursor.execute("SELECT quantidade FROM inventario WHERE usuario_id = ? AND nome = ?", (usuario_id, nome))
    resultado = cursor.fetchone()
    if resultado:
        quantidade = resultado[0] + 1
        cursor.execute("UPDATE inventario SET quantidade = ? WHERE usuario_id = ? AND nome = ?", (quantidade, usuario_id, nome))
    else:
        cursor.execute("INSERT INTO inventario (usuario_id, nome, quantidade, imagem) VALUES (?, ?, ?, ?)", (usuario_id, nome, 1, imagem))
    conn.commit()
    conn.close()

def carregar_historico(usuario_id):
    global historico
    historico = []
    conn, cursor = conectar_db()
    cursor.execute("SELECT nome FROM historico WHERE usuario_id = ? ORDER BY id DESC LIMIT 10", (usuario_id,))
    historico = [row[0] for row in cursor.fetchall()]
    conn.close()

def salvar_historico(usuario_id, nome):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn, cursor = conectar_db()
    cursor.execute("INSERT INTO historico (usuario_id, nome, data) VALUES (?, ?, ?)", (usuario_id, nome, agora))
    conn.commit()
    conn.close()

# ------------------------------
# Interface de login/cadastro
# ------------------------------

def tela_login():
    limpar_janela()
    janela.title("Login - Jogo da Sorte")

    tk.Label(janela, text="Nome de usuário:", fg="white", bg="#222").pack(pady=5)
    entry_nome = tk.Entry(janela)
    entry_nome.pack(pady=5)

    tk.Label(janela, text="Senha:", fg="white", bg="#222").pack(pady=5)
    entry_senha = tk.Entry(janela, show="*")
    entry_senha.pack(pady=5)

    def tentar_login():
        nome = entry_nome.get().strip()
        senha = entry_senha.get().strip()
        if not nome or not senha:
            messagebox.showwarning("Aviso", "Preencha nome e senha")
            return
        usuario_id = validar_login(nome, senha)
        if usuario_id:
            iniciar_jogo(usuario_id, nome)
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos")

    def tentar_cadastro():
        nome = entry_nome.get().strip()
        senha = entry_senha.get().strip()
        if not nome or not senha:
            messagebox.showwarning("Aviso", "Preencha nome e senha")
            return
        if criar_usuario(nome, senha):
            messagebox.showinfo("Sucesso", "Conta criada com sucesso! Faça login.")
        else:
            messagebox.showerror("Erro", "Nome de usuário já existe")

    btn_login = tk.Button(janela, text="Entrar", command=tentar_login, bg="green", fg="white")
    btn_login.pack(pady=10)

    btn_cadastro = tk.Button(janela, text="Cadastrar", command=tentar_cadastro, bg="blue", fg="white")
    btn_cadastro.pack()

# ------------------------------
# Limpar janela para trocar tela
# ------------------------------

def limpar_janela():
    for widget in janela.winfo_children():
        widget.destroy()

# ------------------------------
# Tela principal do jogo
# ------------------------------

def iniciar_jogo(usuario_id, nome_usuario):
    global usuario_logado
    usuario_logado = {"id": usuario_id, "nome": nome_usuario}
    carregar_inventario(usuario_id)
    carregar_historico(usuario_id)

    limpar_janela()
    janela.title(f"Jogo da Sorte - {nome_usuario}")

    resultado_var = tk.StringVar()
    resultado_label = tk.Label(janela, textvariable=resultado_var, font=("Arial", 14), fg="white", bg="#222")
    resultado_label.pack(pady=10)

    imagem_label = tk.Label(janela, bg="#222")
    imagem_label.pack()

    def sortear_item():
        sorteio = random.uniform(0, 100)
        acumulado = 0
        for item in itens:
            acumulado += item["chance"]
            if sorteio <= acumulado:
                nome = item["nome"]
                imagem_path = os.path.join(CAMINHO_IMAGENS, item["imagem"])
                mostrar_resultado(nome, imagem_path)
                salvar_item(usuario_id, nome, item["imagem"])
                carregar_inventario(usuario_id)
                salvar_historico(usuario_id, nome)
                carregar_historico(usuario_id)
                return

    def mostrar_resultado(nome, imagem_path):
        resultado_var.set(f"Você ganhou: {nome}")
        try:
            img = Image.open(imagem_path).resize((100, 100))
            img_tk = ImageTk.PhotoImage(img)
            imagem_label.config(image=img_tk)
            imagem_label.image = img_tk
        except Exception as e:
            imagem_label.config(image='')
            resultado_var.set(f"Você ganhou: {nome}\n(Imagem não encontrada)")
            print("Erro ao carregar imagem:", e)

    def abrir_inventario():
        janela_inv = tk.Toplevel(janela)
        janela_inv.title("Inventário")
        janela_inv.geometry("400x400")
        janela_inv.configure(bg="#222")

        label = tk.Label(janela_inv, text="Seus Itens:", font=("Arial", 14), fg="lightgreen", bg="#222")
        label.pack(pady=10)

        frame_itens = tk.Frame(janela_inv, bg="#222")
        frame_itens.pack(fill="both", expand=True)

        if not inventario:
            vazio = tk.Label(frame_itens, text="Nenhum item ainda.", fg="white", bg="#222")
            vazio.pack()
            return

        for nome_item, dados in inventario.items():
            item_frame = tk.Frame(frame_itens, bg="#333", padx=5, pady=5)
            item_frame.pack(pady=5, fill="x", padx=10)

            imagem_path = os.path.join(CAMINHO_IMAGENS, dados["imagem"])
            try:
                img = Image.open(imagem_path).resize((50, 50))
                img_tk = ImageTk.PhotoImage(img)
                img_label = tk.Label(item_frame, image=img_tk, bg="#333")
                img_label.image = img_tk
                img_label.pack(side="left")
            except:
                img_label = tk.Label(item_frame, text="[sem imagem]", bg="#333", fg="white")
                img_label.pack(side="left")

            texto = f"{nome_item}\nQuantidade: {dados['quantidade']}"
            info_label = tk.Label(item_frame, text=texto, fg="white", bg="#333", justify="left", font=("Arial", 10))
            info_label.pack(side="left", padx=10)

    def abrir_historico():
        janela_hist = tk.Toplevel(janela)
        janela_hist.title("Histórico")
        janela_hist.geometry("300x300")
        janela_hist.configure(bg="#222")

        label = tk.Label(janela_hist, text="Últimos Sorteios:", font=("Arial", 14), fg="skyblue", bg="#222")
        label.pack(pady=10)

        texto = "\n".join(historico) if historico else "Nenhum sorteio ainda."
        conteudo = tk.Label(janela_hist, text=texto, fg="white", bg="#222", justify="left")
        conteudo.pack(padx=20, pady=10)

    def trocar_usuario():
        global usuario_logado, inventario, historico
        usuario_logado = None
        inventario = {}
        historico = []
        tela_login()

    frame_botoes = tk.Frame(janela, bg="#222")
    frame_botoes.pack(pady=10)

    btn_sortear = tk.Button(janela, text="🎁 Abrir Caixa", command=sortear_item,
                            bg="red", fg="white", font=("Arial", 20), padx=30, pady=10)
    btn_sortear.pack(pady=20)

    btn_inventario = tk.Button(frame_botoes, text="🧰 Inventário", command=abrir_inventario,
                               bg="#444", fg="white", font=("Arial", 12), width=15)
    btn_inventario.pack(side="left", padx=10)

    btn_historico = tk.Button(frame_botoes, text="📜 Histórico", command=abrir_historico,
                              bg="#444", fg="white", font=("Arial", 12), width=15)
    btn_historico.pack(side="left", padx=10)

    btn_logout = tk.Button(frame_botoes, text="🔄 Trocar Usuário", command=trocar_usuario,
                           bg="#666", fg="white", font=("Arial", 12), width=15)
    btn_logout.pack(side="left", padx=10)

# ------------------------------
# Inicialização da janela
# ------------------------------

janela = tk.Tk()
janela.geometry("500x450")
janela.configure(bg="#222")

tela_login()

janela.mainloop()
