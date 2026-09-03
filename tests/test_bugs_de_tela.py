"""
SIGBEF — Quatro defeitos que só apareciam na tela.

Nenhum deles quebrava o banco; todos os quatro faziam a bibliotecária
desconfiar do sistema, que é pior.

1. **Cadastro pela tela aceitava o que a planilha recusava.** A
   importação de CSV conferia o ano e o ISBN repetido desde sempre. O
   cadastro digitado na tela não conferia nada: dava para gravar um
   livro de 202 ou o mesmo ISBN em dois registros — e aí o acervo passa
   a ter dois "livros" que são o mesmo livro.

2. **O cartão de alerta ficava preso no vermelho.** Ele só trocava de
   cor quando recebia uma; quando o atraso zerava, a cor não vinha e o
   vermelho continuava. Alerta que nunca apaga deixa de ser alerta.

3. **Tabela sem barra de rolagem.** Catorze `Treeview` na interface,
   nenhuma com `Scrollbar`. Numa tela pequena, o que passava do fim da
   lista simplesmente não existia para quem olhava.

4. **Gravação que falhava em silêncio.** Exportar com o arquivo aberto
   no Excel levantava `OSError`, que morria no console — e num programa
   empacotado não há console. Clicava, não acontecia nada.

Os dois primeiros e o quarto são testados pelo comportamento. O
terceiro é de disposição de widget e é verificado lendo o código, do
mesmo jeito que `test_ui_nomes.py` faz — abrir janela num teste não é
opção.

Uso:
    python -m unittest tests.test_bugs_de_tela -v
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

from tests.base import SigbefTestCase

from sigbef import servicos
from sigbef.servicos import RegraNegocioError

RAIZ = Path(__file__).resolve().parent.parent
PACOTE = RAIZ / "sigbef"


# ---------------------------------------------------------------------------
# 1. O cadastro pela tela tem que valer as mesmas regras da planilha
# ---------------------------------------------------------------------------
class TestValidacaoDoCadastro(SigbefTestCase):

    def test_ano_com_tres_digitos_e_recusado(self):
        with self.assertRaises(RegraNegocioError) as ctx:
            self.criar_livro(titulo="Digitado errado", ano=202)
        self.assertIn("202", str(ctx.exception))

    def test_ano_no_futuro_distante_e_recusado(self):
        with self.assertRaises(RegraNegocioError):
            self.criar_livro(titulo="Do futuro", ano=3050)

    def test_ano_que_nao_e_numero_e_recusado(self):
        with self.assertRaises(RegraNegocioError):
            self.criar_livro(titulo="Ano por extenso", ano="mil e novecentos")

    def test_ano_vazio_continua_valendo(self):
        """Muito livro velho não traz ano. Não pode virar obrigatório."""
        livro = self.criar_livro(titulo="Sem ano", ano=None)
        self.assertTrue(livro["livro_id"])

    def test_ano_dentro_da_faixa_passa(self):
        livro = self.criar_livro(titulo="Normal", ano=1998)
        self.assertTrue(livro["livro_id"])

    def test_isbn_repetido_e_recusado_no_cadastro(self):
        self.criar_livro(titulo="Vidas Secas", isbn="9788501000000")
        with self.assertRaises(RegraNegocioError) as ctx:
            self.criar_livro(titulo="Vidas Secas (outro registro)",
                             isbn="9788501000000")
        # A mensagem tem que dizer ONDE já está, senão não ajuda.
        self.assertIn("Vidas Secas", str(ctx.exception))

    def test_sem_isbn_pode_repetir(self):
        """A maioria do acervo antigo não tem ISBN. Vazio não colide."""
        self.criar_livro(titulo="Um", isbn="")
        self.criar_livro(titulo="Outro", isbn="")

    def test_editar_nao_deixa_assumir_isbn_de_outro(self):
        self.criar_livro(titulo="Primeiro", isbn="9788501000001")
        segundo = self.criar_livro(titulo="Segundo", isbn="9788501000002")
        with self.assertRaises(RegraNegocioError):
            servicos.editar_livro(segundo["livro_id"], titulo="Segundo",
                                  autores=["Autora"], isbn="9788501000001")

    def test_editar_mantendo_o_proprio_isbn_funciona(self):
        """O caso que a validação ingênua quebraria: salvar sem mexer no
        ISBN não pode acusar conflito do livro consigo mesmo."""
        livro = self.criar_livro(titulo="Com ISBN", isbn="9788501000003")
        servicos.editar_livro(livro["livro_id"], titulo="Com ISBN corrigido",
                              autores=["Autora"], isbn="9788501000003")
        detalhe = servicos.detalhes_livro(livro["livro_id"])
        self.assertEqual(detalhe["titulo"], "Com ISBN corrigido")

    def test_editar_tambem_confere_o_ano(self):
        livro = self.criar_livro(titulo="Qualquer")
        with self.assertRaises(RegraNegocioError):
            servicos.editar_livro(livro["livro_id"], titulo="Qualquer",
                                  autores=["Autora"], ano=202)


# ---------------------------------------------------------------------------
# 2. O cartão de alerta tem que saber voltar ao normal
# ---------------------------------------------------------------------------
class _LabelFalso:
    """Só o suficiente para o cartão: guarda o que foi configurado.

    Evita abrir janela do Tk num teste — o cartão que interessa aqui é
    a decisão de cor, não o desenho dela.
    """

    def __init__(self):
        self.config: dict = {}

    def configure(self, **kw):
        self.config.update(kw)


class TestCartaoDeAlerta(unittest.TestCase):

    def montar(self, cor_repouso="#1F4E79"):
        from sigbef.ui_graficos import CartaoNumero
        cartao = object.__new__(CartaoNumero)
        cartao._cor_repouso = cor_repouso
        cartao._lbl_valor = _LabelFalso()
        cartao._lbl_detalhe = _LabelFalso()
        return cartao

    def test_alerta_pinta_o_numero(self):
        cartao = self.montar()
        cartao.atualizar("3", "em atraso", cor="#C62828")
        self.assertEqual(cartao._lbl_valor.config["fg"], "#C62828")

    def test_alerta_apaga_quando_o_atraso_zera(self):
        """É o defeito: sem cor nova, o vermelho ficava para sempre."""
        cartao = self.montar(cor_repouso="#1F4E79")
        cartao.atualizar("3", "em atraso", cor="#C62828")
        cartao.atualizar("0", "nenhum atraso")
        self.assertEqual(
            cartao._lbl_valor.config["fg"], "#1F4E79",
            "o cartão continuou vermelho numa biblioteca sem atraso")

    def test_valor_e_detalhe_sempre_acompanham(self):
        cartao = self.montar()
        cartao.atualizar("12", "empréstimos hoje")
        self.assertEqual(cartao._lbl_valor.config["text"], "12")
        self.assertEqual(cartao._lbl_detalhe.config["text"],
                         "empréstimos hoje")


# ---------------------------------------------------------------------------
# 3. Toda tabela precisa de barra de rolagem
# ---------------------------------------------------------------------------
MODULOS_COM_TABELA = ["ui_painel.py", "ui_dialogos.py", "ui_selfservice.py"]


def _nomes_de_tabela(arvore: ast.AST) -> set:
    """Nomes que receberam uma tabela em algum lugar."""
    nomes = set()
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Assign):
            continue
        valor = no.value
        if not (isinstance(valor, ast.Call)
                and isinstance(valor.func, ast.Attribute)
                and valor.func.attr in ("Treeview", "criar_tabela")):
            continue
        for alvo in no.targets:
            nomes.add(ast.unparse(alvo))
    return nomes


class TestTabelasTemRolagem(unittest.TestCase):

    def test_nenhuma_tabela_e_empacotada_na_mao(self):
        """`pack` reparte espaço na ordem em que é chamado: tabela com
        `expand=True` primeiro deixa a barra com largura zero. Por isso
        as duas têm que sair da mesma função."""
        problemas = []
        for nome in MODULOS_COM_TABELA:
            fonte = (PACOTE / nome).read_text(encoding="utf-8")
            arvore = ast.parse(fonte)
            tabelas = _nomes_de_tabela(arvore)
            for no in ast.walk(arvore):
                if not (isinstance(no, ast.Call)
                        and isinstance(no.func, ast.Attribute)
                        and no.func.attr == "pack"):
                    continue
                dono = ast.unparse(no.func.value)
                if dono in tabelas:
                    problemas.append("%s:%d — %s.pack() direto"
                                     % (nome, no.lineno, dono))
        self.assertEqual(problemas, [],
                         "tabela empacotada sem barra de rolagem:\n  "
                         + "\n  ".join(problemas))

    def test_toda_tabela_criada_passa_pelo_helper(self):
        """Contagem grosseira, mas é exatamente o formato do defeito:
        catorze tabelas e uma barra em todo o programa."""
        for nome in MODULOS_COM_TABELA:
            fonte = (PACOTE / nome).read_text(encoding="utf-8")
            criadas = fonte.count("criar_tabela(")
            roladas = fonte.count("empacotar_com_rolagem(")
            self.assertEqual(
                criadas, roladas,
                "%s tem %d tabelas e %d com rolagem"
                % (nome, criadas, roladas))


# ---------------------------------------------------------------------------
# 4. Gravação que falha tem que avisar
# ---------------------------------------------------------------------------
class _MessageboxFalso:
    def __init__(self):
        self.erros: list = []
        self.infos: list = []

    def showerror(self, titulo, msg, **kw):
        self.erros.append((titulo, msg))

    def showinfo(self, titulo, msg, **kw):
        self.infos.append((titulo, msg))


class TestGravacaoAvisa(unittest.TestCase):

    def setUp(self):
        from sigbef import ui_tema
        self.ui_tema = ui_tema
        self.falso = _MessageboxFalso()
        self._original = ui_tema.messagebox
        ui_tema.messagebox = self.falso

    def tearDown(self):
        self.ui_tema.messagebox = self._original

    def test_falha_de_disco_vira_aviso_na_tela(self):
        """É o defeito: o OSError subia até o laço do Tk e sumia."""
        def escrever():
            raise OSError("O arquivo está sendo usado por outro processo")

        ok = self.ui_tema.gravar_arquivo(None, "C:/saida.csv", escrever)

        self.assertFalse(ok)
        self.assertEqual(len(self.falso.erros), 1)
        self.assertEqual(self.falso.infos, [],
                         "avisou que salvou um arquivo que não foi gravado")
        titulo, msg = self.falso.erros[0]
        self.assertIn("C:/saida.csv", msg)
        self.assertIn("outro processo", msg,
                      "a mensagem do sistema tem que aparecer, senão não "
                      "dá para entender o que houve")

    def test_gravacao_boa_avisa_onde_salvou(self):
        gravou = []
        ok = self.ui_tema.gravar_arquivo(None, "C:/saida.csv",
                                         lambda: gravou.append(True))
        self.assertTrue(ok)
        self.assertEqual(gravou, [True])
        self.assertEqual(len(self.falso.infos), 1)
        self.assertIn("C:/saida.csv", self.falso.infos[0][1])

    def test_nenhuma_tela_grava_arquivo_por_fora(self):
        """A tela pode gravar, mas nunca solta.

        Toda gravação da interface tem que estar dentro de uma
        função aninhada — que é o formato exigido por
        `gravar_arquivo`. Um `open(..., "w")` no corpo do método é
        justamente o que voltava a falhar em silêncio.
        """
        soltas = []
        for nome in MODULOS_COM_TABELA:
            arvore = ast.parse((PACOTE / nome).read_text(encoding="utf-8"))
            # Toda função que mora dentro de outra: é nelas, e só
            # nelas, que uma gravação pode estar — porque é esse
            # o formato que `gravar_arquivo` recebe.
            aninhadas = [d for f in ast.walk(arvore)
                         if isinstance(f, ast.FunctionDef)
                         for d in ast.walk(f)
                         if isinstance(d, ast.FunctionDef) and d is not f]
            protegidos = {c for d in aninhadas for c in ast.walk(d)}
            for c in ast.walk(arvore):
                if not (isinstance(c, ast.Call)
                        and isinstance(c.func, ast.Name)
                        and c.func.id == "open"):
                    continue
                modo = (c.args[1].value
                        if len(c.args) > 1
                        and isinstance(c.args[1], ast.Constant)
                        else "")
                if str(modo).startswith(("w", "a", "x")) and c not in protegidos:
                    soltas.append("%s:%d" % (nome, c.lineno))
        self.assertEqual(soltas, [],
                         "gravação sem aviso de erro: "
                         + ", ".join(soltas))

    def test_mensagem_de_sucesso_pode_ser_trocada(self):
        self.ui_tema.gravar_arquivo(None, "x.csv", lambda: None,
                                    titulo_ok="Modelo salvo",
                                    mensagem_ok="Preencha no Excel.")
        self.assertEqual(self.falso.infos[0], ("Modelo salvo",
                                               "Preencha no Excel."))


# ---------------------------------------------------------------------------
# 5. A lista do acervo tem que saber que o exemplar foi baixado
# ---------------------------------------------------------------------------
class TestDetalhesAvisaQuemAbriu(unittest.TestCase):

    def test_dialogo_aceita_callback(self):
        import inspect
        from sigbef.ui_dialogos import DialogoDetalhesLivro
        parametros = inspect.signature(DialogoDetalhesLivro).parameters
        self.assertIn("ao_mudar", parametros)

    def test_todo_lugar_que_abre_o_dialogo_passa_o_callback(self):
        """O diálogo dá baixa, corrige tombo e muda prateleira. Quem o
        abre sem callback fica com a lista de trás desatualizada."""
        faltando = []
        for nome in MODULOS_COM_TABELA:
            arvore = ast.parse((PACOTE / nome).read_text(encoding="utf-8"))
            for no in ast.walk(arvore):
                if not (isinstance(no, ast.Call)
                        and isinstance(no.func, ast.Name)
                        and no.func.id == "DialogoDetalhesLivro"):
                    continue
                if not any(k.arg == "ao_mudar" for k in no.keywords):
                    faltando.append("%s:%d" % (nome, no.lineno))
        self.assertEqual(faltando, [],
                         "aberturas sem ao_mudar: " + ", ".join(faltando))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
