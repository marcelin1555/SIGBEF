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

from .database import DB_PATH, get_config, registrar_auditoria, set_config

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
