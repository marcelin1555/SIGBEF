"""
SIGBEF — Acrescentar exemplares a um livro que já está no acervo.

Pedido da bibliotecária, e o mesmo padrão dos últimos: a função existia
em `servicos` desde cedo, testada, e **nenhum botão chegava até ela**.
Quando chegava a segunda leva do mesmo livro-texto, o único caminho na
tela era cadastrar tudo de novo — e aí o mesmo título fica duas vezes na
busca, com o acervo contando dois livros onde há um, e a fila de espera
dividida entre dois registros que ninguém concilia depois.

O defeito achado ao ligar o botão está em `TestTomboGeradoNaoRepete`: a
numeração automática usava a **contagem** de exemplares, não o maior
número já usado. Um tombo corrigido na mão para o número seguinte fazia
a próxima leva gerar aquele mesmo número de novo — e tombo repetido é o
que faz o balcão emprestar a cópia errada.

Uso:
    python -m unittest tests.test_adicionar_exemplares -v
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import reservas, servicos
from sigbef.database import db_cursor
from sigbef.servicos import RegraNegocioError


class BaseExemplares(SigbefTestCase):

    def criar(self, titulo="Livro-texto", quantidade=2, tombos=None):
        return servicos.cadastrar_livro(
            titulo=titulo, autores=["Autoria"],
            quantidade_exemplares=quantidade, tombos=tombos)

    def tombos_de(self, livro_id):
        det = servicos.detalhes_livro(livro_id)
        return [ex["numero_tombo"] for ex in det["exemplares"]]


class TestAcrescentarAoMesmoTitulo(BaseExemplares):
    """O caso que a bibliotecária tem: chegou mais do mesmo livro."""

    def test_os_exemplares_entram_no_livro_existente(self):
        liv = self.criar(quantidade=2)

        servicos.adicionar_exemplares(liv["livro_id"], 3)

        det = servicos.detalhes_livro(liv["livro_id"])
        self.assertEqual(len(det["exemplares"]), 5)

    def test_nao_cria_um_titulo_novo(self):
        """É a razão de a função existir: cadastrar de novo deixaria o
        mesmo livro duas vezes na busca."""
        liv = self.criar(titulo="Gramática")

        servicos.adicionar_exemplares(liv["livro_id"], 2)

        self.assertEqual(len(servicos.listar_livros("Gramática")), 1)

    def test_os_novos_saem_disponiveis(self):
        liv = self.criar(quantidade=1)
        novos = servicos.adicionar_exemplares(liv["livro_id"], 2)
        for _id, codigo in novos:
            self.assertEqual(
                servicos.localizar_exemplar(codigo)["status"], "DISPONIVEL")

    def test_a_prateleira_informada_vale_para_os_novos(self):
        liv = self.criar(quantidade=1)
        novos = servicos.adicionar_exemplares(liv["livro_id"], 1,
                                              localizacao="Estante C3")
        det = servicos.detalhes_livro(liv["livro_id"])
        por_codigo = {ex["codigo_barras"]: ex for ex in det["exemplares"]}
        self.assertEqual(por_codigo[novos[0][1]]["localizacao"], "Estante C3")

    def test_fica_na_auditoria(self):
        liv = self.criar(quantidade=1)
        servicos.adicionar_exemplares(liv["livro_id"], 4)
        with db_cursor() as cur:
            cur.execute("SELECT detalhes FROM auditoria "
                        "WHERE acao = 'ADD_EXEMPLARES'")
            self.assertIn("novos=4", cur.fetchone()["detalhes"])

    def test_livro_inexistente_e_recusado(self):
        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(9999, 1)

    def test_quantidade_zero_e_recusada(self):
        liv = self.criar()
        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(liv["livro_id"], 0)


class TestTomboEscritoNaCopia(BaseExemplares):
    """A cópia física costuma chegar com o número já escrito — mesma
    razão que fez o cadastro aceitar tombo informado (v1.10.2)."""

    def test_aceita_o_tombo_informado(self):
        liv = self.criar(quantidade=1, tombos=["T-001"])

        servicos.adicionar_exemplares(liv["livro_id"], 2,
                                      tombos=["T-050", "T-051"])

        self.assertEqual(self.tombos_de(liv["livro_id"]),
                         ["T-001", "T-050", "T-051"])

    def test_em_branco_o_sistema_continua_gerando(self):
        liv = self.criar(quantidade=1)
        servicos.adicionar_exemplares(liv["livro_id"], 1)
        esperado = f"{liv['livro_id']:05d}-002"
        self.assertIn(esperado, self.tombos_de(liv["livro_id"]))

    def test_recusa_tombo_ja_usado_por_outro_livro(self):
        outro = self.criar(titulo="Outro", quantidade=1, tombos=["T-900"])
        liv = self.criar(titulo="Este", quantidade=1)

        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(liv["livro_id"], 1,
                                          tombos=["T-900"])
        self.assertEqual(len(servicos.detalhes_livro(outro["livro_id"])
                             ["exemplares"]), 1)

    def test_recusa_tombo_repetido_dentro_do_proprio_lote(self):
        liv = self.criar(quantidade=1)
        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(liv["livro_id"], 2,
                                          tombos=["T-7", "T-7"])

    def test_recusa_quantidade_de_tombos_diferente_da_quantidade(self):
        liv = self.criar(quantidade=1)
        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(liv["livro_id"], 3,
                                          tombos=["T-1", "T-2"])

    def test_nada_e_gravado_quando_o_tombo_e_recusado(self):
        """A recusa acontece antes do primeiro INSERT: meia leva gravada
        seria pior que nenhuma."""
        outro = self.criar(titulo="Outro", quantidade=1, tombos=["T-800"])
        liv = self.criar(titulo="Este", quantidade=2)

        with self.assertRaises(RegraNegocioError):
            servicos.adicionar_exemplares(liv["livro_id"], 2,
                                          tombos=["T-801", "T-800"])

        self.assertEqual(len(servicos.detalhes_livro(liv["livro_id"])
                             ["exemplares"]), 2)


class TestTomboGeradoNaoRepete(BaseExemplares):
    """O defeito achado ao ligar o botão.

    A sequência automática era a **contagem** de exemplares do livro. Um
    tombo corrigido na mão para o número seguinte fazia a próxima leva
    gerar aquele mesmo número — dois exemplares com o mesmo tombo, e o
    balcão acha o exemplar por `codigo_barras OR numero_tombo` com
    LIMIT 1: empresta a cópia errada, calada.
    """

    def test_pula_numero_que_alguem_escreveu_na_mao(self):
        liv = self.criar(quantidade=2)
        codigo = servicos.detalhes_livro(liv["livro_id"])["exemplares"][0][
            "codigo_barras"]
        # A bibliotecária corrige o tombo do primeiro para o número que a
        # sequência automática usaria a seguir.
        servicos.alterar_tombo_exemplar(codigo, f"{liv['livro_id']:05d}-003")

        servicos.adicionar_exemplares(liv["livro_id"], 1)

        tombos = self.tombos_de(liv["livro_id"])
        self.assertEqual(len(tombos), len(set(tombos)),
                         "dois exemplares ficaram com o mesmo tombo, e é "
                         "essa dupla que faz o balcão emprestar a cópia "
                         "errada")

    def test_pula_numero_ocupado_por_outro_livro(self):
        liv = self.criar(quantidade=1)
        # Outro livro cadastrado com o tombo que a sequência deste usaria.
        self.criar(titulo="Invasor", quantidade=1,
                   tombos=[f"{liv['livro_id']:05d}-002"])

        novos = servicos.adicionar_exemplares(liv["livro_id"], 1)

        ex = servicos.localizar_exemplar(novos[0][1])
        self.assertNotEqual(ex["numero_tombo"],
                            f"{liv['livro_id']:05d}-002")

    def test_leva_grande_nao_repete_entre_si(self):
        liv = self.criar(quantidade=1)
        servicos.adicionar_exemplares(liv["livro_id"], 10)
        tombos = self.tombos_de(liv["livro_id"])
        self.assertEqual(len(tombos), len(set(tombos)))


class TestFilaDeEspera(BaseExemplares):
    """Exemplar novo de livro com fila já sai separado — comportamento
    que existia e precisa continuar existindo com o botão ligado."""

    def test_o_primeiro_exemplar_novo_vai_para_quem_espera(self):
        liv = self.criar(quantidade=1)
        codigo = servicos.detalhes_livro(liv["livro_id"])["exemplares"][0][
            "codigo_barras"]
        leitor = self.criar_usuario(matricula="2024900")
        outro = self.criar_usuario(matricula="2024901")
        servicos.realizar_emprestimo(codigo_exemplar=codigo,
                                     matricula_usuario=outro["matricula"])
        reservas.criar_reserva(liv["livro_id"], leitor["id"])

        novos = servicos.adicionar_exemplares(liv["livro_id"], 1)

        ex = servicos.localizar_exemplar(novos[0][1])
        self.assertEqual(ex["status"], "RESERVADO")


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
