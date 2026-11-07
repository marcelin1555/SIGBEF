"""Configurações do sistema e brasão da instituição."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from ..database import get_config, registrar_auditoria, set_config
from ..erros import RegraNegocioError


# ---------------------------------------------------------------------------
# Brasão da instituição (imagem opcional, exibida no login e no cabeçalho)
# ---------------------------------------------------------------------------
# Guardado em base64 na tabela de configuração: o backup do banco (1
# arquivo) continua levando tudo junto, sem caminho de arquivo frágil.
# PNG e GIF apenas: são os formatos que o tk.PhotoImage lê nativamente
# no Tk 8.6, mantendo a regra de zero dependência externa.
BRASAO_CHAVE = "BRASAO_INSTITUICAO"
BRASAO_LIMITE_BYTES = 512 * 1024

_MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
_MAGIC_GIF = (b"GIF87a", b"GIF89a")


def salvar_brasao(caminho: str, usuario_id: Optional[int] = None) -> None:
    """Valida e grava a imagem do brasão da instituição.

    Levanta RegraNegocioError com mensagem amigável se o arquivo não
    for PNG/GIF ou passar do limite de tamanho.
    """
    dados = Path(caminho).read_bytes()
    eh_png = dados[:8] == _MAGIC_PNG
    eh_gif = dados[:6] in _MAGIC_GIF
    if not (eh_png or eh_gif):
        raise RegraNegocioError(
            "Formato não suportado. Use uma imagem PNG ou GIF "
            "(JPEG não é aceito).")
    if len(dados) > BRASAO_LIMITE_BYTES:
        kb = BRASAO_LIMITE_BYTES // 1024
        raise RegraNegocioError(
            f"Imagem muito grande ({len(dados) // 1024} KB). "
            f"O limite é {kb} KB; reduza a imagem e tente de novo.")
    set_config(BRASAO_CHAVE, base64.b64encode(dados).decode("ascii"))
    registrar_auditoria(usuario_id, "BRASAO_DEFINIDO",
                         f"{len(dados)} bytes")


def obter_brasao() -> Optional[str]:
    """Base64 do brasão configurado, ou None se não houver."""
    valor = get_config(BRASAO_CHAVE, "")
    return valor or None


def remover_brasao(usuario_id: Optional[int] = None) -> None:
    set_config(BRASAO_CHAVE, "")
    registrar_auditoria(usuario_id, "BRASAO_REMOVIDO", "")


# ---------------------------------------------------------------------------
# Configurações do sistema
# ---------------------------------------------------------------------------
# Até a v1.10.4 a tela de Configurações gravava direto com `set_config`, sem
# validar nada e sem passar por aqui. Dois problemas reais vinham disso:
#
# 1. Digitar "0,50" na multa era aceito com um "Salvo com sucesso" — mas
#    `get_config_float` não converte vírgula, cai no `except` e volta para o
#    padrão. A bibliotecária achava que tinha baixado a multa e o sistema
#    seguia cobrando R$ 1,50 por dia.
# 2. Mudança de prazo, de limite e de multa não deixava **nenhum** rastro na
#    auditoria. Quem alterou o prazo de 7 para 30 dias era invisível.

#: chave -> (rótulo na tela, tipo, mínimo, máximo)
CAMPOS_CONFIG: dict[str, tuple[str, str, float, float]] = {
    "PRAZO_ALUNO_DIAS": ("Prazo padrão para alunos (dias)",
                         "inteiro", 1, 365),
    "PRAZO_PROFESSOR_DIAS": ("Prazo padrão para professores (dias)",
                             "inteiro", 1, 365),
    "LIMITE_ALUNO": ("Limite de empréstimos simultâneos (aluno)",
                     "inteiro", 1, 50),
    "LIMITE_PROFESSOR": ("Limite de empréstimos simultâneos (professor)",
                         "inteiro", 1, 50),
    # A coleção tem prazo e teto próprios, e por isso aparecem aqui: a
    # mensagem que recusa uma coleção grande demais manda ajustar o teto
    # em Configurações, e mandar alguém para uma tela que não tem o
    # campo é pior do que não dizer nada.
    "PRAZO_COLECAO_DIAS": ("Prazo da coleção para a turma (dias)",
                           "inteiro", 1, 365),
    "LIMITE_COLECAO_EXEMPLARES": ("Máximo de exemplares por coleção",
                                  "inteiro", 1, 200),
    "MULTA_POR_DIA": ("Multa por dia de atraso (R$)", "dinheiro", 0, 100),
    "MULTA_TETO": ("Teto máximo de multa (R$)", "dinheiro", 0, 1000),
    "NOME_INSTITUICAO": ("Nome da instituição", "texto", 1, 120),
}

#: Chaves cujo valor nunca pode ir para a auditoria em texto claro.
CHAVES_SIGILOSAS = {"SMTP_SENHA", "API_TOKEN", "API_TOKEN_CONSULTA"}


def normalizar_config(chave: str, bruto: str) -> str:
    """Valida e converte um valor digitado para a forma canônica gravada.

    Aceita vírgula como separador decimal — é o que se digita num teclado
    brasileiro, e recusar isso sem avisar foi exatamente o defeito.
    Levanta `RegraNegocioError` com o rótulo da tela na mensagem, para o
    aviso apontar o campo errado em vez de um nome de chave interno.
    """
    if chave not in CAMPOS_CONFIG:
        raise RegraNegocioError(f"Configuração desconhecida: {chave}.")
    rotulo, tipo, minimo, maximo = CAMPOS_CONFIG[chave]
    texto = (bruto or "").strip()

    if tipo == "texto":
        if len(texto) < minimo:
            raise RegraNegocioError(f"“{rotulo}” não pode ficar em branco.")
        if len(texto) > maximo:
            raise RegraNegocioError(
                f"“{rotulo}” passa de {int(maximo)} caracteres.")
        return texto

    if not texto:
        raise RegraNegocioError(f"“{rotulo}” não pode ficar em branco.")

    if tipo == "inteiro":
        try:
            n = int(texto)
        except ValueError:
            raise RegraNegocioError(
                f"“{rotulo}” precisa ser um número inteiro. "
                f"Recebido: “{texto}”.")
        if not (minimo <= n <= maximo):
            raise RegraNegocioError(
                f"“{rotulo}” precisa estar entre {int(minimo)} e "
                f"{int(maximo)}. Recebido: {n}.")
        return str(n)

    # dinheiro
    try:
        valor = float(texto.replace(".", "").replace(",", ".")
                      if "," in texto else texto)
    except ValueError:
        raise RegraNegocioError(
            f"“{rotulo}” precisa ser um valor em reais, como 1,50 ou 1.50. "
            f"Recebido: “{texto}”.")
    if not (minimo <= valor <= maximo):
        raise RegraNegocioError(
            f"“{rotulo}” precisa estar entre {minimo:.2f} e {maximo:.2f}. "
            f"Recebido: {valor:.2f}.")
    return f"{valor:.2f}"


def salvar_configuracoes(valores: dict[str, str],
                         executor_id: int | None = None) -> list[str]:
    """Valida tudo, grava o que mudou e registra na auditoria.

    Valida **antes** de gravar qualquer coisa: um campo errado no meio do
    formulário não pode deixar metade das configurações trocadas e a outra
    metade não. Devolve a lista de rótulos alterados — vazia se nada mudou.
    """
    normalizados = {chave: normalizar_config(chave, bruto)
                    for chave, bruto in valores.items()}

    alterados: list[str] = []
    for chave, novo in normalizados.items():
        antigo = get_config(chave)
        if antigo == novo:
            continue
        set_config(chave, novo)
        rotulo = CAMPOS_CONFIG[chave][0]
        alterados.append(rotulo)
        registrar_auditoria(
            executor_id, "CONFIG_ALTERADA",
            f"{chave}: '{antigo if antigo is not None else ''}' -> '{novo}'")
    return alterados


def definir_config_auditada(chave: str, valor: str,
                            executor_id: int | None = None,
                            acao: str = "CONFIG_ALTERADA") -> bool:
    """Grava uma chave avulsa deixando rastro. Devolve True se mudou.

    Para as chaves que não têm formulário validado (cores do tema, SMTP,
    porta da API). O valor de chave sigilosa nunca vai para o detalhe: a
    auditoria registra que a senha do e-mail mudou, não qual é ela.
    """
    antigo = get_config(chave)
    if antigo == valor:
        return False
    set_config(chave, valor)
    if chave in CHAVES_SIGILOSAS:
        detalhe = f"{chave}: valor alterado"
    else:
        detalhe = f"{chave}: '{antigo if antigo is not None else ''}' -> '{valor}'"
    registrar_auditoria(executor_id, acao, detalhe)
    return True


# As telas leem configuração por aqui, nunca direto no banco.
obter_config = get_config


def definir_preferencia(chave: str, valor: str) -> None:
    """Grava uma preferência de tela, sem auditoria (ex.: boas-vindas vista)."""
    set_config(chave, valor)
