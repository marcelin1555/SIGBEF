"""
SIGBEF — Cópia de segurança do banco.

O botão "Fazer backup agora" sempre existiu, mas depender de alguém
lembrar de clicar é o mesmo que não ter backup: quando faz falta,
descobre-se que a última cópia é de agosto.

Aqui a cópia acontece sozinha ao fechar o sistema, no máximo uma vez por
dia, e as antigas somem sem intervenção.

**Por que não `shutil.copy2`:** o banco roda em modo WAL, então parte
das transações vive num arquivo `-wal` separado até o checkpoint.
Copiar só o `.db` no meio de uma escrita produz um arquivo que abre mas
está desatualizado — o pior tipo de backup, o que parece bom. A API
`sqlite3.Connection.backup()` conversa com o próprio SQLite e leva um
retrato consistente, mesmo com o sistema em uso. É da biblioteca padrão,
então a regra de zero dependência continua de pé.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from .database import (DB_PATH, db_cursor, get_config, registrar_auditoria,
                       set_config)

PREFIXO = "sigbef_backup_"
SUFIXO = ".db"


def ativo() -> bool:
    return (get_config("BACKUP_AUTO", "1") or "1").strip() == "1"


def pasta_destino() -> Path:
    """Onde as cópias ficam. Padrão: ao lado do banco, em `backups/`."""
    configurada = (get_config("BACKUP_PASTA", "") or "").strip()
    if configurada:
        return Path(configurada).expanduser()
    return Path(DB_PATH).parent / "backups"


def quantas_manter() -> int:
    try:
        return max(1, int(get_config("BACKUP_MANTER", "7") or 7))
    except ValueError:
        return 7


def copiar(destino: Optional[Path] = None) -> Path:
    """Faz uma cópia consistente do banco e devolve o caminho.

    Serve tanto para o backup automático quanto para o botão manual: o
    caminho é o mesmo, e é o único lugar do sistema que copia o banco.
    """
    if destino is None:
        pasta = pasta_destino()
        pasta.mkdir(parents=True, exist_ok=True)
        # Nome livre, sempre: duas cópias próximas (o automático logo
        # depois de um manual) caíam no mesmo carimbo e uma apagava a
        # outra em silêncio -- e a rotação passava a guardar menos
        # cópias do que o configurado. Carimbo mais fino não resolve,
        # porque o relógio tem granularidade; procurar nome livre sim.
        carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = pasta / f"{PREFIXO}{carimbo}{SUFIXO}"
        n = 2
        while destino.exists():
            destino = pasta / f"{PREFIXO}{carimbo}_{n}{SUFIXO}"
            n += 1
    else:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)

    origem = sqlite3.connect(DB_PATH, timeout=30)
    try:
        copia = sqlite3.connect(destino)
        try:
            origem.backup(copia)
        finally:
            copia.close()
    finally:
        origem.close()
    return destino


def limpar_antigos(manter: Optional[int] = None) -> list[Path]:
    """Apaga as cópias mais antigas, devolvendo o que foi removido.

    Só mexe em arquivos com o nome que este módulo gera: uma pasta de
    backup pode ter outras coisas dentro, e apagar o que não é nosso
    seria uma surpresa muito ruim.
    """
    manter = manter or quantas_manter()
    pasta = pasta_destino()
    if not pasta.exists():
        return []
    copias = sorted(pasta.glob(f"{PREFIXO}*{SUFIXO}"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    removidos = []
    for antigo in copias[manter:]:
        try:
            antigo.unlink()
            removidos.append(antigo)
        except OSError:
            # Arquivo travado ou sem permissão: não é motivo para
            # atrapalhar o fechamento do sistema.
            pass
    return removidos


def executar_se_necessario(usuario_id: Optional[int] = None) -> Optional[Path]:
    """Chamada ao fechar o sistema. Faz no máximo uma cópia por dia.

    Nunca levanta exceção: se o backup falhar (pendrive removido, disco
    cheio), a bibliotecária não pode ficar presa numa janela de erro na
    hora de ir embora. O problema fica registrado na auditoria.
    """
    if not ativo():
        return None
    hoje = date.today().isoformat()
    if (get_config("BACKUP_ULTIMO", "") or "") == hoje:
        return None

    try:
        caminho = copiar()
        removidos = limpar_antigos()
        set_config("BACKUP_ULTIMO", hoje)
        registrar_auditoria(
            usuario_id, "BACKUP_AUTOMATICO",
            f"arquivo={caminho.name}"
            + (f"; removidos={len(removidos)}" if removidos else ""))
        return caminho
    except Exception as e:            # noqa: BLE001 — ver docstring
        try:
            registrar_auditoria(usuario_id, "BACKUP_FALHOU", str(e)[:200])
        except Exception:
            pass
        return None


def ultimo() -> Optional[dict]:
    """Data e tamanho da cópia mais recente, para mostrar nas Configurações."""
    pasta = pasta_destino()
    if not pasta.exists():
        return None
    copias = sorted(pasta.glob(f"{PREFIXO}*{SUFIXO}"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    if not copias:
        return None
    p = copias[0]
    return {
        "caminho": str(p),
        "quando": datetime.fromtimestamp(p.stat().st_mtime),
        "mb": round(p.stat().st_size / 1024 / 1024, 1),
        "total": len(copias),
    }


# ---------------------------------------------------------------------------
# Restauração
# ---------------------------------------------------------------------------
#: Prefixo da cópia tirada do banco ATUAL, imediatamente antes de ele ser
#: substituído. Nome diferente do backup comum de propósito: a rotação
#: (`limpar_antigos`) não pode apagar justamente a cópia que serve para
#: desfazer uma restauração feita por engano.
PREFIXO_SALVAGUARDA = "sigbef_antes_da_restauracao_"

#: Sem estas tabelas o arquivo não é um banco do SIGBEF. A lista é curta
#: de propósito: um backup antigo pode não ter as tabelas mais novas, e
#: recusá-lo por isso seria recusar exatamente o backup de que alguém
#: mais precisa.
TABELAS_ESSENCIAIS = ("livro", "exemplar", "usuario", "emprestimo",
                      "configuracao")


class BackupInvalido(Exception):
    """O arquivo escolhido não serve como banco do SIGBEF."""


def conferir(origem) -> dict:
    """Abre o arquivo só para leitura e diz o que tem dentro.

    Existe para que a restauração possa ser confirmada com números na
    frente — "3.104 livros, 2 empréstimos em aberto, mexido pela última
    vez em 12/08" — em vez de um "tem certeza?" no vazio. Escolher o
    arquivo errado é fácil: a pasta de backup tem uma cópia por dia e
    todas têm nome parecido.

    @raise BackupInvalido se o arquivo não abrir ou não for do SIGBEF.
    """
    caminho = Path(origem)
    if not caminho.exists():
        raise BackupInvalido("O arquivo não existe: %s" % caminho)

    try:
        # `mode=ro` garante que conferir não cria nem altera nada — nem
        # mesmo o `-wal` que uma abertura normal deixaria para trás.
        uri = "file:%s?mode=ro" % caminho.as_posix().replace("?", "%3f")
        conn = sqlite3.connect(uri, uri=True, timeout=10)
    except sqlite3.Error as e:
        raise BackupInvalido("Não foi possível abrir o arquivo: %s" % e)

    try:
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")
            tabelas = {r["name"] for r in cur.fetchall()}
        except sqlite3.DatabaseError:
            raise BackupInvalido(
                "O arquivo escolhido não é um banco de dados SQLite.")

        faltando = [t for t in TABELAS_ESSENCIAIS if t not in tabelas]
        if faltando:
            raise BackupInvalido(
                "O arquivo é um banco, mas não é do SIGBEF: faltam as "
                "tabelas %s." % ", ".join(faltando))

        def conta(sql: str) -> int:
            try:
                return conn.execute(sql).fetchone()[0]
            except sqlite3.DatabaseError:
                return 0

        return {
            "caminho": str(caminho),
            "mb": round(caminho.stat().st_size / 1024 / 1024, 1),
            "livros": conta("SELECT COUNT(*) FROM livro WHERE ativo = 1"),
            "exemplares": conta("SELECT COUNT(*) FROM exemplar "
                                "WHERE status != 'BAIXADO'"),
            "usuarios": conta("SELECT COUNT(*) FROM usuario WHERE ativo = 1"),
            "emprestimos_abertos": conta(
                "SELECT COUNT(*) FROM emprestimo "
                "WHERE data_devolucao IS NULL"),
            "ultima_atividade": conn.execute(
                "SELECT MAX(timestamp) FROM auditoria").fetchone()[0]
            if "auditoria" in tabelas else None,
        }
    finally:
        conn.close()


def restaurar(origem, usuario_id: Optional[int] = None) -> dict:
    """Substitui o banco em uso pelo conteúdo de um backup.

    Três cuidados, todos deliberados:

    1. **Confere antes.** Restaurar um arquivo qualquer apagaria o
       acervo sem aviso; `conferir` recusa o que não for do SIGBEF.
    2. **Guarda o banco atual antes de sobrescrever**, com nome que a
       rotação não apaga. Restaurar é a operação mais destrutiva do
       sistema e a mais provável de ser feita em pânico — desfazer
       precisa ser possível.
    3. **Copia pela API do SQLite, não pelo sistema de arquivos.** Pelo
       mesmo motivo de `copiar`: com o banco em WAL, trocar o `.db` por
       fora deixa para trás um `-wal` do banco antigo, e o resultado é
       uma mistura dos dois.

    Depois da troca roda `init_database()`: um backup de meses atrás
    pode ser anterior a colunas que o sistema de hoje já usa, e sem a
    migração o programa quebraria logo na primeira tela.

    @return o resumo do que foi restaurado e onde ficou a salvaguarda.
    """
    resumo = conferir(origem)

    pasta = pasta_destino()
    pasta.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    salvaguarda = pasta / f"{PREFIXO_SALVAGUARDA}{carimbo}{SUFIXO}"
    n = 2
    while salvaguarda.exists():
        salvaguarda = pasta / f"{PREFIXO_SALVAGUARDA}{carimbo}_{n}{SUFIXO}"
        n += 1
    copiar(salvaguarda)

    fonte = sqlite3.connect(Path(origem), timeout=30)
    try:
        atual = sqlite3.connect(DB_PATH, timeout=30)
        try:
            # Sentido inverso do backup: o arquivo escolhido é a origem
            # e o banco em uso é o destino. O SQLite troca o conteúdo
            # inteiro numa transação — ou vai tudo, ou não vai nada.
            fonte.backup(atual)
        finally:
            atual.close()
    finally:
        fonte.close()

    from .database import init_database
    init_database()

    # A auditoria da restauração fica no banco RESTAURADO, que é onde
    # ela vai fazer falta. Quem restaurou pode não existir lá dentro —
    # um backup anterior ao cadastro dela — e nesse caso o registro fica
    # sem dono em vez de falhar por chave estrangeira.
    dono = usuario_id
    if dono is not None:
        with db_cursor() as cur:
            cur.execute("SELECT 1 FROM usuario WHERE id = ?", (dono,))
            if not cur.fetchone():
                dono = None
    registrar_auditoria(
        dono, "BACKUP_RESTAURADO",
        "arquivo=%s; salvaguarda=%s; livros=%s; exemplares=%s"
        % (Path(origem).name, salvaguarda.name,
           resumo["livros"], resumo["exemplares"]))

    return {"resumo": resumo, "salvaguarda": salvaguarda}
