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
from .database import db_cursor, get_config, set_config, registrar_auditoria
from .servicos import RegraNegocioError


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
# Quantos empréstimos já devolvidos a rota do leitor devolve. Quem
# estuda há anos acumula centenas, e a tela do app mostra só os
# recentes — mandar tudo seria payload grande sem ninguém ler.
HISTORICO_MAX = 20

_ROTA_LIVRO = re.compile(r"^/api/v1/livros/(\d+)$")
_ROTA_USUARIO_EMP = re.compile(r"^/api/v1/usuarios/([^/]+)/emprestimos$")
_ROTA_CANCELAR_RES = re.compile(r"^/api/v1/reservas/(\d+)/cancelar$")
_ROTA_RENOVAR = re.compile(r"^/api/v1/emprestimos/(\d+)/renovar$")


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
        self.sessao_app = None
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
            self.sessao_app = sessao
            return "aluno"
        return None

    @staticmethod
    def _matricula_na_rota(caminho: str) -> Optional[str]:
        """Matrícula citada numa rota de dados pessoais, se houver.

        É o que permite ao token do app ler os próprios empréstimos e as
        próprias reservas, e só os próprios.
        """
        m = _ROTA_USUARIO_EMP.match(caminho)
        return m.group(1) if m else None

    def _escopo_da_rota(self, caminho: str) -> str:
        """'completo' para rotas com dados de leitores; 'consulta' para o
        acervo público."""
        if (self._matricula_na_rota(caminho)
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
            # Token de sessão do app: pode ler os PRÓPRIOS dados.
            dono = self._matricula_na_rota(caminho)
            if nivel == "aluno" and dono:
                if dono != self.matricula_sessao:
                    self._erro(403, "Você só pode consultar os seus "
                                    "próprios dados.")
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
        """As únicas gravações que a API aceita.

        São três, e todas mexem apenas na fila do próprio aluno logado:
        reservar um livro, cancelar essa reserva e renovar um empréstimo
        que é dele. O acervo — livros, exemplares, cadastros — continua
        intocável por aqui; quem altera isso é o balcão.
        """
        caminho = urlparse(self.path).path.rstrip("/") or "/"
        if not api_ativa():
            self._erro(403, "A API está desligada nas configurações do "
                            "SIGBEF.")
            return

        if caminho == "/api/v1/login":
            try:
                self._login()
            except Exception:
                self._erro(500, "Erro interno ao processar a requisição.")
            return

        acao = self._acao_de_escrita(caminho)
        if acao is None:
            self._erro(405, "Rota não aceita POST. Gravação só em "
                            "/api/v1/login, /api/v1/reservas, "
                            "/api/v1/reservas/{id}/cancelar e "
                            "/api/v1/emprestimos/{id}/renovar.")
            return

        # Escrita exige um aluno de verdade por trás. Token de sistema não
        # serve: ele não é ninguém, e toda ação aqui precisa de um dono.
        if self._nivel_do_token() != "aluno":
            self._erro(403, "Esta ação exige o login do aluno no aplicativo.")
            return

        try:
            acao()
        except RegraNegocioError as e:
            # 409: o pedido está bem formado, mas a regra da biblioteca
            # diz não. A frase vem pronta para aparecer na tela do aluno.
            self._erro(409, str(e))
        except Exception:
            self._erro(500, "Erro interno ao processar a requisição.")

    def _acao_de_escrita(self, caminho: str):
        """Casa o caminho com a função que o executa, ou None."""
        if caminho == "/api/v1/reservas":
            return self._criar_reserva
        m = _ROTA_CANCELAR_RES.match(caminho)
        if m:
            return lambda: self._cancelar_reserva(int(m.group(1)))
        m = _ROTA_RENOVAR.match(caminho)
        if m:
            return lambda: self._renovar(int(m.group(1)))
        return None

    def _corpo_json(self) -> Optional[dict]:
        """Lê o corpo da requisição como objeto JSON.

        Devolve None e já responde o erro quando o corpo não presta.
        """
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            tamanho = 0
        if tamanho <= 0 or tamanho > 4096:
            self._erro(400, "Corpo da requisição ausente ou grande demais.")
            return None
        try:
            dados = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._erro(400, "Corpo inválido: envie JSON.")
            return None
        if not isinstance(dados, dict):
            self._erro(400, "Corpo inválido: envie um objeto JSON.")
            return None
        return dados

    def _criar_reserva(self) -> None:
        dados = self._corpo_json()
        if dados is None:
            return
        try:
            livro_id = int(dados.get("livro_id"))
        except (TypeError, ValueError):
            self._erro(400, "Informe livro_id (número).")
            return

        r = reservas.criar_reserva(livro_id, self.sessao_app.id)
        self._json(201, {"reserva": r})

    def _cancelar_reserva(self, reserva_id: int) -> None:
        # usuario_id preenchido faz o próprio módulo recusar reserva
        # que seja de outro aluno.
        reservas.cancelar_reserva(reserva_id,
                                  usuario_id=self.sessao_app.id)
        self._json(200, {"ok": True})

    def _renovar(self, emprestimo_id: int) -> None:
        with db_cursor() as cur:
            cur.execute(
                "SELECT usuario_id FROM emprestimo "
                "WHERE id = ? AND data_devolucao IS NULL",
                (emprestimo_id,),
            )
            emp = cur.fetchone()
        if not emp:
            self._erro(404, "Empréstimo não encontrado.")
            return
        if emp["usuario_id"] != self.sessao_app.id:
            self._erro(403, "Este empréstimo é de outro leitor.")
            return

        # validar_regras=True: sem ninguém no balcão para julgar, valem
        # as regras (atraso, fila de espera, limite de renovações).
        r = servicos.renovar_emprestimo(emprestimo_id,
                                        operador_id=self.sessao_app.id,
                                        validar_regras=True)
        self._json(200, r)

    def _login(self) -> None:
        from .auth import autenticar, criar_sessao_app

        dados = self._corpo_json()
        if dados is None:
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
        """PUT/DELETE/PATCH nunca são aceitos, em rota nenhuma.

        As poucas gravações que existem passam todas por POST, e são
        criações — nada aqui substitui nem apaga registro.
        """
        self._erro(405, "Método não aceito. Use GET para consultar e POST "
                        "nas poucas rotas que gravam.")

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
            todos = servicos.listar_emprestimos_usuario(u["id"])
            abertos = [e for e in todos if not e["data_devolucao"]]
            # Últimos devolvidos, para o aluno rever o que já leu. Vem
            # limitado porque quem estuda há anos acumula centenas, e a
            # tela mostra só os recentes de qualquer forma.
            historico = [e for e in todos if e["data_devolucao"]][:HISTORICO_MAX]
            ativas = reservas.listar_reservas_usuario(u["id"])
            # O app precisa saber, antes de oferecer o botão, se cada
            # livro pode mesmo ser renovado — e, quando não, por quê.
            for e in abertos:
                ok, motivo = servicos.pode_renovar(e["id"])
                e["pode_renovar"] = ok
                e["motivo_renovacao"] = motivo
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
                "historico": historico,
                "reservas_ativas": [
                    {"id": r["id"], "livro_id": r["livro_id"],
                     "titulo": r["titulo"], "posicao": r["posicao"],
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
