"""
SIGBEF — Camada de banco de dados (SQLite)

Centraliza conexão, criação do esquema e funções utilitárias de acesso a dados.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


def _diretorio_padrao() -> Path:
    """Determina onde guardar o banco SQLite.

    Ordem de prioridade:
      1. Variável de ambiente SIGBEF_DB_PATH (caminho completo)
      2. Pasta `data/` ao lado do código fonte (modo desenvolvimento)
      3. %APPDATA%/SIGBEF (Windows) ou ~/.local/share/SIGBEF (Linux)
         quando rodando como executável empacotado.
    """
    # Detecta se está rodando dentro de um executável PyInstaller
    rodando_empacotado = getattr(sys, "frozen", False)

    if rodando_empacotado:
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home())) / "SIGBEF"
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / "SIGBEF"
        else:
            base = Path.home() / ".local" / "share" / "SIGBEF"
        return base

    return BASE_DIR / "data"


# Permite sobrescrever via variável de ambiente
_env_db = os.environ.get("SIGBEF_DB_PATH")
if _env_db:
    DB_PATH = Path(_env_db).expanduser().resolve()
    DATA_DIR = DB_PATH.parent
else:
    DATA_DIR = _diretorio_padrao()
    DB_PATH = DATA_DIR / "sigbef.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão SQLite com row_factory configurado.

    `timeout=10` faz escritas concorrentes esperarem em vez de falhar
    na hora com "database is locked" (balcão e kiosk simultâneos), e o
    modo WAL permite leituras durante uma escrita.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def db_cursor():
    """Context manager: abre conexão, comita ou faz rollback automaticamente."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS editora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS categoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS autor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS livro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    isbn TEXT,
    editora_id INTEGER REFERENCES editora(id),
    categoria_id INTEGER REFERENCES categoria(id),
    ano_publicacao INTEGER,
    edicao TEXT,
    sinopse TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS livro_autor (
    livro_id INTEGER NOT NULL REFERENCES livro(id) ON DELETE CASCADE,
    autor_id INTEGER NOT NULL REFERENCES autor(id) ON DELETE CASCADE,
    PRIMARY KEY (livro_id, autor_id)
);

CREATE TABLE IF NOT EXISTS exemplar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livro_id INTEGER NOT NULL REFERENCES livro(id),
    codigo_barras TEXT UNIQUE NOT NULL,
    numero_tombo TEXT,
    localizacao TEXT,
    status TEXT NOT NULL DEFAULT 'DISPONIVEL',
    motivo_baixa TEXT,
    data_baixa TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    matricula TEXT UNIQUE NOT NULL,
    email TEXT,
    telefone TEXT,
    turma TEXT,
    perfil TEXT NOT NULL CHECK (perfil IN ('ALUNO','PROFESSOR','BIBLIOTECARIO','ADMINISTRADOR')),
    senha_hash TEXT NOT NULL,
    codigo_barras TEXT UNIQUE,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS emprestimo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exemplar_id INTEGER NOT NULL REFERENCES exemplar(id),
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    data_emprestimo TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    data_prevista TEXT NOT NULL,
    data_devolucao TEXT,
    -- `multa` e o valor LANCADO na devolucao e nunca muda depois: e o
    -- historico. O que foi recebido vai em `multa_paga`, o que foi
    -- perdoado vai em `multa_isenta`, e o saldo devedor e a diferenca.
    -- Ate a v1.10.4 existia so `multa`, servindo de valor lancado E de
    -- saldo ao mesmo tempo -- entao quitar apagava o registro de que a
    -- multa existiu, e o relatorio da direcao somava so o que ninguem
    -- tinha pagado sob o rotulo "Multas lancadas".
    multa REAL NOT NULL DEFAULT 0,
    multa_paga REAL NOT NULL DEFAULT 0,
    multa_isenta REAL NOT NULL DEFAULT 0,
    multa_motivo_isencao TEXT,
    multa_quitada_em TEXT,
    origem TEXT NOT NULL DEFAULT 'BALCAO' CHECK (origem IN ('BALCAO','AUTOATENDIMENTO')),
    renovacoes INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS reserva (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    livro_id INTEGER NOT NULL REFERENCES livro(id),
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    exemplar_id INTEGER REFERENCES exemplar(id),
    status TEXT NOT NULL DEFAULT 'ATIVA'
        CHECK (status IN ('ATIVA','ATENDIDA','CANCELADA','EXPIRADA')),
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    disponivel_ate TEXT
);

CREATE TABLE IF NOT EXISTS notificacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emprestimo_id INTEGER NOT NULL REFERENCES emprestimo(id),
    tipo TEXT NOT NULL DEFAULT 'VENCIMENTO',
    enviado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS notificacao_reserva (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL REFERENCES reserva(id),
    enviado_em TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS configuracao (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuario(id),
    acao TEXT NOT NULL,
    detalhes TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- Sessões do aplicativo de celular (um registro por aparelho pareado).
-- O token nunca é guardado em claro, só o hash — mesma postura da senha.
CREATE TABLE IF NOT EXISTS sessao_app (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuario(id),
    token_hash TEXT UNIQUE NOT NULL,
    criado_em TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    expira_em TEXT NOT NULL,
    revogada INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessao_app_token ON sessao_app(token_hash);
CREATE INDEX IF NOT EXISTS idx_sessao_app_usuario ON sessao_app(usuario_id);

-- Conferência do acervo: a bibliotecária passa o leitor nas estantes e
-- o sistema anota o que viu. No fim, a diferença entre o que existe no
-- cadastro e o que apareceu na prateleira é o resultado.
CREATE TABLE IF NOT EXISTS inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT,
    iniciado_em TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    encerrado_em TEXT,
    usuario_id INTEGER REFERENCES usuario(id)
);

-- Um exemplar só entra uma vez por conferência: passar o mesmo livro
-- duas vezes no leitor é acidente comum e não pode virar contagem dupla.
CREATE TABLE IF NOT EXISTS inventario_item (
    inventario_id INTEGER NOT NULL REFERENCES inventario(id),
    exemplar_id INTEGER NOT NULL REFERENCES exemplar(id),
    visto_em TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    PRIMARY KEY (inventario_id, exemplar_id)
);

CREATE INDEX IF NOT EXISTS idx_livro_titulo ON livro(titulo);
CREATE INDEX IF NOT EXISTS idx_livro_isbn ON livro(isbn);
CREATE INDEX IF NOT EXISTS idx_exemplar_codigo ON exemplar(codigo_barras);
-- O empréstimo de balcão procura por código de barras OU número de
-- tombo (localizar_exemplar). O código já era indexado pela restrição
-- UNIQUE, o tombo não: com um lado sem índice, o OR obrigava o SQLite a
-- varrer a tabela inteira de exemplares a cada empréstimo.
CREATE INDEX IF NOT EXISTS idx_exemplar_tombo ON exemplar(numero_tombo);
CREATE INDEX IF NOT EXISTS idx_exemplar_livro ON exemplar(livro_id);
CREATE INDEX IF NOT EXISTS idx_emprestimo_status ON emprestimo(data_devolucao);
CREATE INDEX IF NOT EXISTS idx_emprestimo_exemplar ON emprestimo(exemplar_id);
CREATE INDEX IF NOT EXISTS idx_emprestimo_usuario ON emprestimo(usuario_id);
CREATE INDEX IF NOT EXISTS idx_reserva_livro ON reserva(livro_id, status);
CREATE INDEX IF NOT EXISTS idx_reserva_usuario ON reserva(usuario_id, status);
"""


CONFIG_PADRAO = {
    "PRAZO_ALUNO_DIAS": "7",
    "PRAZO_PROFESSOR_DIAS": "14",
    "LIMITE_ALUNO": "3",
    "LIMITE_PROFESSOR": "5",
    "MULTA_POR_DIA": "1.50",
    "MULTA_TETO": "60.00",
    "NOME_INSTITUICAO": "CEFE, Centro Educacional Felinto Elísio",
    # Bloqueio temporário de conta após tentativas de senha falhas
    "LOGIN_MAX_TENTATIVAS": "5",
    "LOGIN_BLOQUEIO_MIN": "15",
    "ISBN_LOOKUP": "0",  # busca de metadados por ISBN, desligada (offline-first)
    # Cópia de segurança automática ao fechar o sistema. Nasce LIGADA:
    # a regra de opt-in vale para o que fala com a rede, e isto é
    # proteção local — quem perde o banco perde o acervo inteiro.
    "BACKUP_AUTO": "1",
    "BACKUP_PASTA": "",      # vazio = pasta "backups" ao lado do banco
    "BACKUP_MANTER": "7",    # quantas cópias guardar
    "BACKUP_ULTIMO": "",     # data da última cópia, para não repetir no dia
    "LIMITE_RESERVAS": "3",       # reservas ativas simultâneas por usuário
    "RESERVA_VALIDADE_DIAS": "2", # prazo pra retirar o exemplar reservado
    "LIMITE_RENOVACOES": "2",     # renovações seguidas que o aluno faz sozinho
    # E-mail de aviso de vencimento (opt-in; sistema segue 100% offline
    # com isso desligado)
    "EMAIL_AVISOS": "0",
    "EMAIL_DIAS_ANTES": "2",
    "SMTP_HOST": "",
    "SMTP_PORTA": "587",
    "SMTP_USUARIO": "",
    "SMTP_SENHA": "",
    "SMTP_REMETENTE": "",
    # API REST somente leitura (opt-in; desligada = nenhuma porta aberta)
    "API_ATIVA": "0",
    "API_PORTA": "8765",
    "API_TOKEN": "",           # completo: acervo + dados de leitores
    "API_TOKEN_CONSULTA": "",  # restrito: só acervo público
}


def init_database() -> None:
    """Cria o schema e popula as configurações padrão se ainda não existirem.

    Também executa migrações leves para bancos existentes que ainda não
    têm colunas novas (ex.: usuario.turma adicionado em v1.2.0).
    """
    with db_cursor() as cur:
        cur.executescript(SCHEMA_SQL)
        _migrar_schema(cur)
        for chave, valor in CONFIG_PADRAO.items():
            cur.execute(
                "INSERT OR IGNORE INTO configuracao (chave, valor) VALUES (?, ?)",
                (chave, valor),
            )


def _migrar_schema(cur) -> None:
    """Aplica ALTER TABLE em colunas que foram adicionadas em versões
    posteriores e podem não existir em bancos criados antes."""
    cur.execute("PRAGMA table_info(usuario)")
    colunas = {r["name"] for r in cur.fetchall()}
    if "turma" not in colunas:
        cur.execute("ALTER TABLE usuario ADD COLUMN turma TEXT")

    cur.execute("PRAGMA table_info(emprestimo)")
    colunas = {r["name"] for r in cur.fetchall()}
    if "renovacoes" not in colunas:
        cur.execute("ALTER TABLE emprestimo "
                    "ADD COLUMN renovacoes INTEGER NOT NULL DEFAULT 0")

    if "multa_paga" not in colunas:
        # Bancos anteriores tem so `multa`. Nada a converter: o valor que
        # esta la e, por definicao, o que ainda estava em aberto, entao
        # pago e isento nascem zerados e o saldo continua o mesmo. O que
        # ja foi quitado antes desta versao esta perdido -- `quitar_multa`
        # zerava a coluna -- e nao da para reconstruir.
        cur.execute("ALTER TABLE emprestimo "
                    "ADD COLUMN multa_paga REAL NOT NULL DEFAULT 0")
        cur.execute("ALTER TABLE emprestimo "
                    "ADD COLUMN multa_isenta REAL NOT NULL DEFAULT 0")
        cur.execute("ALTER TABLE emprestimo "
                    "ADD COLUMN multa_motivo_isencao TEXT")
        cur.execute("ALTER TABLE emprestimo ADD COLUMN multa_quitada_em TEXT")

    cur.execute("PRAGMA table_info(exemplar)")
    colunas = {r["name"] for r in cur.fetchall()}
    if "motivo_baixa" not in colunas:
        # Exemplar baixado sem motivo é exemplar que ninguém sabe
        # explicar depois: "sumiu" e "foi descartado por estar rasgado"
        # contam histórias diferentes na hora de repor o acervo.
        cur.execute("ALTER TABLE exemplar ADD COLUMN motivo_baixa TEXT")
        cur.execute("ALTER TABLE exemplar ADD COLUMN data_baixa TEXT")

    _reparar_numeros_de_config(cur)


#: Chaves numéricas que a tela de Configurações grava. Repetidas aqui, e não
#: importadas de `servicos`, porque `servicos` importa este módulo.
_CONFIG_NUMERICAS = ("MULTA_POR_DIA", "MULTA_TETO", "PRAZO_ALUNO_DIAS",
                     "PRAZO_PROFESSOR_DIAS", "LIMITE_ALUNO",
                     "LIMITE_PROFESSOR")


def _reparar_numeros_de_config(cur) -> None:
    """Conserta valores numéricos gravados com vírgula decimal.

    Até a v1.10.4 a tela gravava direto o que foi digitado, sem validar.
    Quem digitou `0,50` na multa recebeu "Salvo com sucesso" e ficou com
    `'0,50'` no banco — que `float()` não converte, então o cálculo caía
    no padrão e seguia cobrando o valor antigo, sem nenhum aviso.

    A partir daqui a tela valida antes de gravar, mas os bancos que já
    estão rodando na escola podem estar com o valor quebrado agora. Isto
    conserta uma vez, na subida: só troca vírgula por ponto, e só quando
    o resultado realmente vira número. Valor que não vira número fica
    como está — chutar um valor de multa seria pior que não mexer.
    """
    for chave in _CONFIG_NUMERICAS:
        cur.execute("SELECT valor FROM configuracao WHERE chave = ?", (chave,))
        row = cur.fetchone()
        if not row or not row["valor"] or "," not in row["valor"]:
            continue
        candidato = row["valor"].replace(".", "").replace(",", ".")
        try:
            float(candidato)
        except ValueError:
            continue
        cur.execute("UPDATE configuracao SET valor = ? WHERE chave = ?",
                    (candidato, chave))
        cur.execute(
            "INSERT INTO auditoria(usuario_id, acao, detalhes) "
            "VALUES (NULL, ?, ?)",
            ("CONFIG_REPARADA",
             f"{chave}: '{row['valor']}' -> '{candidato}' "
             "(vírgula decimal corrigida na atualização)"))


# ---------------------------------------------------------------------------
# Helpers de acesso (consultas curtas usadas em vários lugares)
# ---------------------------------------------------------------------------
def get_config(chave: str, padrao: str | None = None) -> str | None:
    with db_cursor() as cur:
        cur.execute("SELECT valor FROM configuracao WHERE chave = ?", (chave,))
        row = cur.fetchone()
        return row["valor"] if row else padrao


def set_config(chave: str, valor: str) -> None:
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO configuracao(chave, valor) VALUES(?, ?) "
            "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
            (chave, valor),
        )


def registrar_auditoria(usuario_id: int | None, acao: str, detalhes: str = "") -> None:
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO auditoria(usuario_id, acao, detalhes) VALUES (?, ?, ?)",
            (usuario_id, acao, detalhes),
        )


def db_exists() -> bool:
    return DB_PATH.exists() and DB_PATH.stat().st_size > 0
