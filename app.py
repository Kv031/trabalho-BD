import sqlite3
from datetime import datetime
from pymongo import MongoClient

# Configuração dos Bancos de Dados
SQL_DB = "chamados.db"
MONGO_URI = "mongodb://localhost:27017/"

def conectar_sql():
    conn = sqlite3.connect(SQL_DB)
    conn.row_factory = sqlite3.Row
    return conn

def conectar_mongo():
    client = MongoClient(MONGO_URI)
    db = client["suporte_tecnico"]
    return db["historicos"]

def inicializar_bancos():
    with open("schema.sql", "r", encoding="utf-8") as f:
        script = f.read()
    conn = conectar_sql()
    conn.executescript(script)
    conn.commit()
    conn.close()

def registrar_historico(chamado_id, responsavel, acao, observacoes):
    colecao = conectar_mongo()
    documento = {
        "chamado_id": int(chamado_id),
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "responsavel": responsavel,
        "acao": acao,
        "observacoes": observacoes
    }
    colecao.insert_one(documento)

# 1. Cadastrar um chamado
def cadastrar_chamado():
    print("\n--- NOVO CHAMADO ---")
    nome = input("Nome do solicitante: ")
    email = input("E-mail do solicitante: ")
    setor = input("Setor: ")

    conn = conectar_sql()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM solicitantes WHERE email = ?", (email,))
    solicitante = cursor.fetchone()
    if solicitante:
        solicitante_id = solicitante["id"]
    else:
        cursor.execute(
            "INSERT INTO solicitantes (nome, email, setor) VALUES (?, ?, ?)",
            (nome, email, setor)
        )
        solicitante_id = cursor.lastrowid

    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    print("\nCategorias disponíveis:")
    for cat in categorias:
        print(f"{cat['id']} - {cat['nome']}")
    categoria_id = int(input("Escolha o ID da categoria: "))

    equipamento = input("Equipamento (ex: Notebook Dell, Impressora): ")
    descricao = input("Descrição do problema: ")

    cursor.execute(
        """INSERT INTO chamados (solicitante_id, categoria_id, equipamento, descricao)
           VALUES (?, ?, ?, ?)""",
        (solicitante_id, categoria_id, equipamento, descricao)
    )
    chamado_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Integração NoSQL: registra criação no MongoDB
    registrar_historico(
        chamado_id=chamado_id,
        responsavel=nome,
        acao="Abertura de chamado",
        observacoes=f"Chamado criado com status 'Aberto'. Problema: {descricao}"
    )
    print(f"\nChamado #{chamado_id} cadastrado com sucesso!")

# 2. Consultar e listar chamados
def listar_chamados():
    print("\n--- LISTA DE CHAMADOS ---")
    conn = conectar_sql()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, s.nome AS solicitante, cat.nome AS categoria, c.equipamento, c.status
        FROM chamados c
        JOIN solicitantes s ON c.solicitante_id = s.id
        JOIN categorias cat ON c.categoria_id = cat.id
        ORDER BY c.id DESC
    """)
    chamados = cursor.fetchall()
    conn.close()

    if not chamados:
        print("Nenhum chamado cadastrado.")
        return

    for c in chamados:
        print(f"ID: {c['id']} | Solicitante: {c['solicitante']} | Categoria: {c['categoria']} | Equip.: {c['equipamento']} | Status: {c['status']}")

# 3. Visualizar detalhes de um chamado
def detalhes_chamado():
    chamado_id = input("\nInforme o ID do chamado: ")
    conn = conectar_sql()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, s.nome AS solicitante, s.email, s.setor, cat.nome AS categoria
        FROM chamados c
        JOIN solicitantes s ON c.solicitante_id = s.id
        JOIN categorias cat ON c.categoria_id = cat.id
        WHERE c.id = ?
    """, (chamado_id,))
    c = cursor.fetchone()
    conn.close()

    if not c:
        print("Chamado não encontrado.")
        return

    print(f"\n=== DETALHES DO CHAMADO #{c['id']} ===")
    print(f"Solicitante: {c['solicitante']} ({c['email']} - Setor: {c['setor']})")
    print(f"Categoria:   {c['categoria']}")
    print(f"Equipamento: {c['equipamento']}")
    print(f"Status:      {c['status']}")
    print(f"Abertura:    {c['data_abertura']}")
    print(f"Descrição:   {c['descricao']}")

# 4. Alterar status de um chamado
def alterar_status():
    chamado_id = input("\nInforme o ID do chamado: ")
    novo_status = input("Novo status (Aberto / Em Andamento / Resolvido / Fechado): ")
    responsavel = input("Responsável pela alteração: ")
    obs = input("Observações: ")

    conn = conectar_sql()
    cursor = conn.cursor()
    cursor.execute("UPDATE chamados SET status = ? WHERE id = ?", (novo_status, chamado_id))
    if cursor.rowcount == 0:
        print("Chamado não encontrado.")
        conn.close()
        return
    conn.commit()
    conn.close()

    # Integração NoSQL: registra mudança de status no MongoDB
    registrar_historico(
        chamado_id=chamado_id,
        responsavel=responsavel,
        acao=f"Status alterado para '{novo_status}'",
        observacoes=obs
    )
    print("Status atualizado e registrado no histórico!")

# 5. Registrar comentários/movimentações no histórico
def registrar_comentario():
    chamado_id = input("\nInforme o ID do chamado: ")
    responsavel = input("Responsável pelo comentário: ")
    obs = input("Comentário / Movimentação: ")

    registrar_historico(
        chamado_id=chamado_id,
        responsavel=responsavel,
        acao="Comentário técnico",
        observacoes=obs
    )
    print("Comentário registrado no histórico (MongoDB)!")

# 6. Consultar histórico de um chamado
def consultar_historico():
    chamado_id = int(input("\nInforme o ID do chamado: "))
    colecao = conectar_mongo()
    registros = list(colecao.find({"chamado_id": chamado_id}))

    print(f"\n=== HISTÓRICO DO CHAMADO #{chamado_id} (MongoDB) ===")
    if not registros:
        print("Nenhum histórico encontrado para este chamado.")
        return

    for reg in registros:
        print(f"[{reg['data']}] {reg['acao']} - Por: {reg['responsavel']}")
        print(f"   Obs.: {reg['observacoes']}\n")

def menu():
    inicializar_bancos()
    while True:
        print("\n==========================================")
        print(" SISTEMA DE CHAMADOS (SQLite + MongoDB)")
        print("==========================================")
        print("1. Cadastrar chamado")
        print("2. Listar chamados")
        print("3. Visualizar detalhes de um chamado")
        print("4. Alterar status de um chamado")
        print("5. Registrar comentário no histórico")
        print("6. Consultar histórico de um chamado")
        print("0. Sair")
        opcao = input("Escolha uma opção: ")

        if opcao == "1": cadastrar_chamado()
        elif opcao == "2": listar_chamados()
        elif opcao == "3": detalhes_chamado()
        elif opcao == "4": alterar_status()
        elif opcao == "5": registrar_comentario()
        elif opcao == "6": consultar_historico()
        elif opcao == "0": break
        else: print("Opção inválida.")

if __name__ == "__main__":
    menu()
