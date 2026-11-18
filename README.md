# Sistema de Gerenciamento de Chamados (SQL + NoSQL)

Aplicação desenvolvida para integrar bancos de dados relacionais (**SQLite**) e não relacionais (**MongoDB**) no controle de chamados de suporte técnico.

## Tecnologias Utilizadas
* **Linguagem:** Python 3
* **Banco Relacional (SQL):** SQLite (`sqlite3`)
* **Banco Documental (NoSQL):** MongoDB (`pymongo`)
* **Versionamento:** Git e GitHub

## Como Executar o Projeto
1. Certifique-se de ter o **Python 3** e o **MongoDB** rodando localmente na porta padrão (`localhost:27017`).
2. Clone o repositório:
   ```bash
   git clone https://github.com
   cd sistema-chamados
   ```
3. Instale a dependência do MongoDB:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute a aplicação:
   ```bash
   python app.py
   ```
