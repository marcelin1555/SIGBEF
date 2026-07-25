# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marcello
"""
SIGBEF — API REST somente leitura (opcional, opt-in).

Permite que outros sistemas da escola consultem acervo, disponibilidade
e situação de empréstimos sem tocar no banco diretamente. Desligada por
padrão (API_ATIVA=0): nenhuma porta é aberta pra quem não usar.

Implementada 100% com a biblioteca padrão (http.server + json). Todas
as rotas exigem `Authorization: Bearer <API_TOKEN>` exceto o healthcheck
`/api/v1/ping`. Nesta versão não existe NENHUMA rota de escrita.

Uso dentro do app: o painel sobe o servidor numa thread quando a API
está ativa. Uso headless: `python sigbef.py --api`.
"""
from __future__ import annotations

import hmac
import json
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

from . import reservas, servicos
from .database import get_config, set_config, registrar_auditoria


# ---------------------------------------------------------------------------
# Liga/desliga e token
# ---------------------------------------------------------------------------
def api_ativa() -> bool:
    return (get_config("API_ATIVA", "0") or "0").strip() == "1"


# Dois níveis de acesso (princípio do menor privilégio):
#   completo — acervo + dados de leitores e circulação
#   consulta — só acervo público (livros, disponibilidade, estatísticas)
def obter_token() -> str:
    return (get_config("API_TOKEN") or "").strip()


def obter_token_consulta() -> str:
    return (get_config("API_TOKEN_CONSULTA") or "").strip()


def gerar_novo_token(executor_id: Optional[int] = None) -> str:
    """Gera (ou regenera) o token COMPLETO. O antigo deixa de valer."""
    token = secrets.token_urlsafe(32)
    set_config("API_TOKEN", token)
    registrar_auditoria(executor_id, "API_TOKEN_GERADO", "completo")
    return token


def gerar_novo_token_consulta(executor_id: Optional[int] = None) -> str:
    """Gera (ou regenera) o token de CONSULTA (só acervo)."""
    token = secrets.token_urlsafe(32)
    set_config("API_TOKEN_CONSULTA", token)
    registrar_auditoria(executor_id, "API_TOKEN_GERADO", "consulta")
    return token


def definir_api(ativo: bool, executor_id: Optional[int] = None) -> None:
    set_config("API_ATIVA", "1" if ativo else "0")
    if ativo:
        if not obter_token():
            gerar_novo_token(executor_id)
        if not obter_token_consulta():
            gerar_novo_token_consulta(executor_id)
    registrar_auditoria(executor_id,
                         "API_ATIVADA" if ativo else "API_DESATIVADA", "")


def porta_configurada() -> int:
    try:
        return int(get_config("API_PORTA", "8765") or "8765")
    except ValueError:
        return 8765


# ---------------------------------------------------------------------------
# Pareamento do aplicativo móvel
# ---------------------------------------------------------------------------
def ip_local() -> Optional[str]:
    """IP desta máquina na rede da escola, ou None se não houver rede.

    Abre um socket UDP e pergunta ao sistema qual interface seria usada
    para falar com um endereço da própria LAN. Nada é enviado e não
    depende de internet — é só uma consulta à tabela de rotas.
    """
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Endereço qualquer da faixa privada; não há tráfego real.
        sock.connect(("192.168.255.255", 1))
        ip = sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()
    # Sem rede o sistema devolve o próprio loopback, que não serve ao app
    if not ip or ip.startswith("127."):
        return None
    return ip


def endereco_pareamento() -> Optional[str]:
    """Texto que vai dentro do QR code lido pelo aplicativo.

    Formato: `sigbef://IP:PORTA`. **Não carrega token de propósito**: o
    QR fica exposto na tela do computador da biblioteca, e quem
    fotografasse ganharia acesso aos dados de todos os leitores. A
    identidade vem do login do próprio aluno (matrícula e senha).
    """
    ip = ip_local()
    if not ip:
        return None
    return f"sigbef://{ip}:{porta_configurada()}"


# ---------------------------------------------------------------------------
# Handler HTTP
# ---------------------------------------------------------------------------
_ROTA_LIVRO = re.compile(r"^/api/v1/livros/(\d+)$")
_ROTA_USUARIO_EMP = re.compile(r"^/api/v1/usuarios/([^/]+)/emprestimos$")


class _Handler(BaseHTTPRequestHandler):
    server_version = "SIGBEF-API"

    # Sem log de acesso no console (auditoria cobre o que importa)
    def log_message(self, fmt, *args):  # noqa: D102
        pass

    # ---------------- infra ----------------
    def _json(self, codigo: int, payload) -> None:
        corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, codigo: int, mensagem: str) -> None:
        self._json(codigo, {"erro": mensagem})

    def _nivel_do_token(self) -> Optional[str]:
        """Retorna 'completo', 'consulta', 'aluno' ou None.

        No caso de 'aluno' (token de sessão do aplicativo), guarda em
        `self.matricula_sessao` a matrícula dona daquele aparelho — é o
        que permite barrar a leitura de dados de outro leitor.
        """
        self.matricula_sessao = None
        recebido = (self.headers.get("Authorization") or "")
        if not recebido.startswith("Bearer "):
            return None
        tok = recebido[7:].strip()
        completo = obter_token()
        consulta = obter_token_consulta()
        if completo and hmac.compare_digest(tok, completo):
            return "completo"
        if consulta and hmac.compare_digest(tok, consulta):
            return "consulta"
        from .auth import sessao_app_valida
        sessao = sessao_app_valida(tok)
        if sessao is not None:
            self.matricula_sessao = sessao.matricula
            return "aluno"
        return None

    def _escopo_da_rota(self, caminho: str) -> str:
        """'completo' para rotas com dados de leitores; 'consulta' para o
        acervo público."""
        if (_ROTA_USUARIO_EMP.match(caminho)
                or caminho == "/api/v1/emprestimos/abertos"):
            return "completo"
        return "consulta"

    # ---------------- métodos ----------------
    def do_GET(self):  # noqa: N802 (nome exigido pelo http.server)
        url = urlparse(self.path)
        caminho = url.path.rstrip("/") or "/"
        query = parse_qs(url.query)

        if caminho == "/api/v1/ping":
            from . import __version__
            self._json(200, {"ok": True, "servico": "SIGBEF",
                              "versao": __version__})
            return

        if not api_ativa():
            self._erro(403, "A API está desligada nas configurações do SIGBEF.")
            return
        nivel = self._nivel_do_token()
        if nivel is None:
            self._erro(401, "Token ausente ou inválido. Envie o header "
                            "Authorization: Bearer <token>.")
            return
        if self._escopo_da_rota(caminho) == "completo" and nivel != "completo":
            # Token de sessão do app: pode ler os PRÓPRIOS empréstimos.
            emp = _ROTA_USUARIO_EMP.match(caminho)
            if nivel == "aluno" and emp:
                if emp.group(1) != self.matricula_sessao:
                    self._erro(403, "Você só pode consultar os seus "
                                    "próprios empréstimos.")
                    return
            else:
                self._erro(403, "Este token é apenas de consulta ao acervo. "
                                "Rotas com dados de leitores exigem o token "
                                "completo.")
                return

        try:
            self._rotear(caminho, query)
        except Exception:  # nunca vazar traceback pro cliente
            self._erro(500, "Erro interno ao processar a requisição.")

    def do_POST(self):  # noqa: N802
        """Só existe um POST: o login do aplicativo. O acervo segue
        intocável — nenhuma rota altera dados da biblioteca."""
        caminho = urlparse(self.path).path.rstrip("/") or "/"
        if caminho != "/api/v1/login":
            self._erro(405, "Esta API é somente leitura (apenas GET).")
            return
        if not api_ativa():
            self._erro(403, "A API está desligada nas configurações do "
                            "SIGBEF.")
            return
        try:
            self._login()
        except Exception:
            self._erro(500, "Erro interno ao processar a requisição.")

    def _login(self) -> None:
        from .auth import autenticar, criar_sessao_app

        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            tamanho = 0
        if tamanho <= 0 or tamanho > 4096:
            self._erro(400, "Corpo da requisição ausente ou grande demais.")
            return
        try:
            dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._erro(400, "Corpo inválido: envie JSON com matricula e "
                            "senha.")
            return
        if not isinstance(dados, dict):
            self._erro(400, "Corpo inválido: envie um objeto JSON.")
            return

        matricula = str(dados.get("matricula") or "").strip()
        senha = str(dados.get("senha") or "")
        if not matricula or not senha:
            self._erro(400, "Informe matrícula e senha.")
            return

        # Reaproveita o login do desktop: já traz bloqueio por tentativas,
        # tempo constante para matrícula inexistente e registro de auditoria.
        sessao = autenticar(matricula, senha)
        if sessao is None:
            self._erro(401, "Matrícula ou senha incorretos.")
            return

        from .database import get_config

        token = criar_sessao_app(sessao.id)
        self._json(200, {
            "token": token,
            "instituicao": get_config("NOME_INSTITUICAO", "Biblioteca")
                           or "Biblioteca",
            "usuario": {
                "nome": sessao.nome,
                "matricula": sessao.matricula,
                "perfil": sessao.perfil,
            },
        })

    def _somente_leitura(self):
        """PUT/DELETE/PATCH nunca são aceitos, nem em /login."""
        self._erro(405, "Esta API é somente leitura (apenas GET).")

    do_PUT = do_DELETE = do_PATCH = _somente_leitura

    # ---------------- rotas ----------------
    def _rotear(self, caminho: str, query: dict) -> None:
        if caminho == "/api/v1/estatisticas":
            self._json(200, servicos.estatisticas())
            return

        if caminho == "/api/v1/livros":
            termo = (query.get("q") or [""])[0]
            apenas_disp = (query.get("disponiveis") or ["0"])[0] == "1"
            livros = servicos.listar_livros(termo, apenas_disp)
            self._json(200, {"total": len(livros), "livros": livros})
            return

        m = _ROTA_LIVRO.match(caminho)
        if m:
            det = servicos.detalhes_livro(int(m.group(1)))
            if not det:
                self._erro(404, "Livro não encontrado.")
                return
            self._json(200, {
                "id": det["id"], "titulo": det["titulo"],
                "isbn": det.get("isbn"),
                "ano_publicacao": det.get("ano_publicacao"),
                "edicao": det.get("edicao"),
                "sinopse": det.get("sinopse"),
                "editora": det.get("editora_nome"),
                "categoria": det.get("categoria_nome"),
                "autores": det["autores"],
                "exemplares": [
                    {"numero_tombo": ex["numero_tombo"],
                     "codigo_barras": ex["codigo_barras"],
                     "localizacao": ex.get("localizacao"),
                     "status": ex["status"]}
                    for ex in det["exemplares"]
                ],
            })
            return

        m = _ROTA_USUARIO_EMP.match(caminho)
        if m:
            u = servicos.localizar_usuario(m.group(1))
            if not u:
                self._erro(404, "Usuário não encontrado.")
                return
            dados = servicos.obter_usuario(u["id"])
            st = servicos.status_usuario(u["id"])
            abertos = servicos.listar_emprestimos_usuario(
                u["id"], somente_abertos=True)
            ativas = reservas.listar_reservas_usuario(u["id"])
            self._json(200, {
                "nome": dados["nome"],
                "matricula": dados["matricula"],
                "turma": dados.get("turma"),
                "perfil": dados["perfil"],
                "ativo": bool(dados["ativo"]),
                "pode_pegar": st.pode_pegar,
                "situacao": st.motivo,
                "limite_emprestimos": st.limite,
                "multas_em_aberto": st.multas_em_aberto,
                "emprestimos_abertos": abertos,
                "reservas_ativas": [
                    {"titulo": r["titulo"], "posicao": r["posicao"],
                     "separado": bool(r["exemplar_id"]),
                     "retirar_ate": r["disponivel_ate"]}
                    for r in ativas
                ],
            })
            return

        if caminho == "/api/v1/emprestimos/abertos":
            emprestimos = servicos.listar_emprestimos_em_aberto()
            self._json(200, {"total": len(emprestimos),
                              "emprestimos": emprestimos})
            return

        self._erro(404, "Rota não encontrada. Rotas: /api/v1/ping, "
                        "/api/v1/estatisticas, /api/v1/livros, "
                        "/api/v1/livros/{id}, "
                        "/api/v1/usuarios/{matricula}/emprestimos, "
                        "/api/v1/emprestimos/abertos.")


# ---------------------------------------------------------------------------
# Ciclo de vida do servidor
# ---------------------------------------------------------------------------
_servidor: Optional[ThreadingHTTPServer] = None
_thread: Optional[threading.Thread] = None


def criar_servidor(porta: Optional[int] = None,
                   bind: str = "0.0.0.0") -> ThreadingHTTPServer:
    """Cria o servidor (sem iniciar o loop). `porta=0` = porta efêmera."""
    p = porta_configurada() if porta is None else porta
    return ThreadingHTTPServer((bind, p), _Handler)


def iniciar_em_thread(porta: Optional[int] = None) -> int:
    """Sobe a API numa thread daemon. Retorna a porta em uso.

    Idempotente: se já está no ar, só devolve a porta atual.
    """
    global _servidor, _thread
    if _servidor is not None:
        return _servidor.server_address[1]
    _servidor = criar_servidor(porta)
    _thread = threading.Thread(target=_servidor.serve_forever, daemon=True)
    _thread.start()
    return _servidor.server_address[1]


def parar() -> None:
    """Derruba o servidor da thread, se estiver de pé."""
    global _servidor, _thread
    if _servidor is not None:
        _servidor.shutdown()
        _servidor.server_close()
        _servidor = None
        _thread = None


def esta_no_ar() -> bool:
    return _servidor is not None
