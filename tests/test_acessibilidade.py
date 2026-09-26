"""
SIGBEF — Acessibilidade do desktop.

Contraste das cores (critério WCAG de 4,5:1 para texto), tamanho do
texto configurável e uso sem mouse: Enter nas tabelas e nos botões,
Esc nos diálogos, foco visível ao chegar numa tabela.
"""
from __future__ import annotations

import tkinter as tk
import unittest
from tkinter import ttk
from types import SimpleNamespace

from tests.base import SigbefTestCase

from sigbef import database
from sigbef import ui_tema as tema

MINIMO = 4.5
BRANCO = "#FFFFFF"


class TestContraste(unittest.TestCase):
    """Cores fixas precisam ser legíveis em qualquer predefinição."""

    def test_cores_de_estado_legiveis_como_texto_em_todo_fundo(self):
        fundos = [p["fundo"] for p in tema.PRESETS.values()] + [BRANCO]
        for nome in ("COR_SUCESSO", "COR_ERRO", "COR_AVISO"):
            cor = getattr(tema, nome)
            for fundo in fundos:
                with self.subTest(cor=nome, fundo=fundo):
                    self.assertGreaterEqual(tema.contraste(cor, fundo), MINIMO)

    def test_texto_branco_legivel_sobre_as_cores_de_estado(self):
        for nome in ("COR_SUCESSO", "COR_ERRO", "COR_AVISO"):
            with self.subTest(cor=nome):
                self.assertGreaterEqual(
                    tema.contraste(BRANCO, getattr(tema, nome)), MINIMO)

    def test_texto_de_dica_legivel(self):
        self.assertGreaterEqual(tema.contraste("#6B7280", tema.COR_FUNDO), MINIMO)
        self.assertGreaterEqual(tema.contraste("#6B7280", tema.COR_CARD), MINIMO)

    def test_secundaria_de_toda_predefinicao_fica_legivel_com_branco(self):
        # Verde Floresta tinha 3,3:1 nos botões antes da correção
        for chave, preset in tema.PRESETS.items():
            with self.subTest(preset=chave):
                cor = tema.legivel_com_branco(preset["secundaria"])
                self.assertGreaterEqual(tema.contraste(cor, BRANCO), MINIMO)

    def test_cor_personalizada_clara_e_escurecida(self):
        for clara in ("#FFFF00", "#A0E0FF", "#F5F7FA", "#FFFFFF"):
            with self.subTest(cor=clara):
                cor = tema.legivel_com_branco(clara)
                self.assertGreaterEqual(tema.contraste(cor, BRANCO), MINIMO)

    def test_cor_que_ja_passa_nao_muda(self):
        self.assertEqual(tema.legivel_com_branco("#1F4E79"), "#1F4E79")

    def test_texto_suave_do_cabecalho_legivel_em_toda_predefinicao(self):
        for chave, preset in tema.PRESETS.items():
            with self.subTest(preset=chave):
                suave = tema._suave_sobre_primaria(preset["primaria"])
                self.assertGreaterEqual(
                    tema.contraste(suave, preset["primaria"]), MINIMO)


class TestTamanhoDoTexto(SigbefTestCase):

    def tearDown(self):
        tema.ESCALA = 1.0

    def test_padrao_e_normal(self):
        tema.carregar_personalizacao()
        self.assertEqual(tema.ESCALA, 1.0)

    def test_escolha_gravada_vale_na_proxima_abertura(self):
        self.assertTrue(tema.salvar_tamanho_texto("muito_grande"))
        tema.ESCALA = 1.0
        tema.carregar_personalizacao()
        self.assertEqual(tema.ESCALA, 1.3)

    def test_tamanho_desconhecido_e_recusado(self):
        self.assertFalse(tema.salvar_tamanho_texto("gigante"))
        self.assertEqual(database.get_config("tema.tamanho_texto", None), None)

    def test_valor_estranho_no_banco_volta_ao_normal(self):
        database.set_config("tema.tamanho_texto", "gigante")
        tema.carregar_personalizacao()
        self.assertEqual(tema.ESCALA, 1.0)

    def test_escalar_acompanha_o_tamanho(self):
        tema.ESCALA = 1.15
        self.assertEqual(tema.escalar(264), 304)
        tema.ESCALA = 1.0
        self.assertEqual(tema.escalar(264), 264)


class _ComTk(SigbefTestCase):
    """Uma janela Tk de verdade; pulado onde não há tela."""

    def setUp(self):
        super().setUp()
        try:
            self.root = tk.Tk()
        except tk.TclError as e:  # pragma: no cover - sem display
            self.skipTest(f"Tk indisponível: {e}")
        self.root.geometry("+4000+4000")
        tema.aplicar_tema(self.root)
        self.root.update()

    def tearDown(self):
        tema.ESCALA = 1.0
        try:
            self.root.destroy()
        except tk.TclError:
            pass
        super().tearDown()

    def tecla(self, widget, tecla):
        widget.focus_force()
        self.root.update()
        widget.event_generate(tecla, when="now")
        self.root.update()


class TestEscalaNaJanela(_ComTk):

    def test_escala_do_tk_segue_o_tamanho_sem_acumular(self):
        base = self.root._escala_base
        tema.salvar_tamanho_texto("grande")
        tema.aplicar_tema(self.root)
        tema.aplicar_tema(self.root)  # reaplicar não multiplica de novo
        # Tolerância relativa: o Tk arredonda a escala por dentro (no
        # Windows do GitHub, 1,15 virou 1,1485), e uma comparação com três
        # casas decimais barrou o instalador da v1.14.0 sem defeito real.
        # Acumular o fator daria 1,32 — bem longe desta margem de 1%.
        fator = float(self.root.tk.call("tk", "scaling")) / base
        self.assertAlmostEqual(fator, 1.15, delta=0.01)

    def test_janela_cresce_com_o_texto(self):
        tema.ESCALA = 1.15
        janela = tk.Toplevel(self.root)
        tema.centralizar_janela(janela, 400, 300)
        janela.update()
        self.assertEqual((janela.winfo_width(), janela.winfo_height()), (460, 345))


class TestFaixaDeBotoes(_ComTk):

    def montar(self, largura, alinhar="right"):
        self.root.geometry(f"{largura}x200+4000+4000")
        faixa = tema.FaixaDeBotoes(self.root, alinhar=alinhar)
        faixa.pack(fill="x")
        botoes = [faixa.adicionar(ttk.Button(faixa, text=t)) for t in
                  ("Importar CSV", "Etiquetas em massa", "Excluir do acervo")]
        for _ in range(3):
            self.root.update()
        return faixa, botoes

    def test_sem_espaco_quebra_linha_sem_cortar_botao(self):
        faixa, botoes = self.montar(260)
        for botao in botoes:
            with self.subTest(botao=botao.cget("text")):
                self.assertEqual(botao.winfo_width(), botao.winfo_reqwidth())
                self.assertLessEqual(botao.winfo_x() + botao.winfo_width(),
                                     faixa.winfo_width())
        self.assertGreater(len({b.winfo_y() for b in botoes}), 1)
        # a faixa cresce para caber a segunda linha
        self.assertGreaterEqual(faixa.winfo_height(),
                                max(b.winfo_y() + b.winfo_height() for b in botoes))

    def test_com_espaco_fica_numa_linha_so_e_na_ordem(self):
        faixa, botoes = self.montar(900)
        self.assertEqual(len({b.winfo_y() for b in botoes}), 1)
        xs = [b.winfo_x() for b in botoes]
        self.assertEqual(xs, sorted(xs))
        # alinhada à direita: o último botão encosta na borda
        ultimo = botoes[-1]
        self.assertAlmostEqual(ultimo.winfo_x() + ultimo.winfo_width(),
                               faixa.winfo_width(), delta=1)

    def test_botoes_aparecem_mesmo_sem_evento_de_tamanho(self):
        # Defeito real: a faixa dependia de um <Configure> para ganhar
        # altura; sem ele ficava com 1 px e o cabeçalho de Livros mostrava
        # só um risco no lugar de "Mais" e "Cadastrar livro".
        faixa = tema.FaixaDeBotoes(self.root)  # nem empacotada
        botao = faixa.adicionar(ttk.Button(faixa, text="Cadastrar livro"))
        self.root.update_idletasks()
        self.assertGreaterEqual(faixa.winfo_reqheight(),
                                botao.winfo_reqheight())
        self.assertGreaterEqual(faixa.winfo_reqwidth(),
                                botao.winfo_reqwidth())

    def test_alinhada_a_esquerda(self):
        _faixa, botoes = self.montar(900, alinhar="left")
        self.assertEqual(botoes[0].winfo_x(), 0)


class TestTeclado(_ComTk):

    def test_esc_fecha_o_dialogo_pelo_mesmo_caminho_do_x(self):
        chamadas = []
        dialogo = tk.Toplevel(self.root)
        dialogo.protocol("WM_DELETE_WINDOW",
                         lambda: (chamadas.append("x"), dialogo.destroy()))
        campo = ttk.Entry(dialogo)
        campo.pack()
        resultado = tema._esc_fecha_dialogo(SimpleNamespace(widget=campo))
        self.assertEqual(resultado, "break")
        self.assertEqual(chamadas, ["x"])
        self.assertFalse(dialogo.winfo_exists())

    def test_esc_fecha_dialogo_sem_protocolo(self):
        dialogo = tk.Toplevel(self.root)
        tema._esc_fecha_dialogo(SimpleNamespace(widget=dialogo))
        self.assertFalse(dialogo.winfo_exists())

    def test_esc_nunca_fecha_a_janela_principal(self):
        campo = ttk.Entry(self.root)
        campo.pack()
        self.assertIsNone(tema._esc_fecha_dialogo(SimpleNamespace(widget=campo)))
        self.assertTrue(self.root.winfo_exists())

    def test_esc_na_lista_aberta_do_combobox_e_ignorado(self):
        self.assertIsNone(tema._esc_fecha_dialogo(
            SimpleNamespace(widget=".popdown.f.l")))

    def test_enter_na_tabela_abre_a_linha(self):
        chamadas = []
        tabela = tema.criar_tabela(self.root, columns=("a",), show="headings")
        tema.empacotar_com_rolagem(tabela, fill="both", expand=True)
        tabela.insert("", "end", values=("x",))
        tema.ao_ativar_linha(tabela, lambda: chamadas.append(1))
        self.tecla(tabela, "<Return>")
        self.assertEqual(chamadas, [1])

    def test_chegar_na_tabela_marca_a_primeira_linha(self):
        tabela = tema.criar_tabela(self.root, columns=("a",), show="headings")
        tema.empacotar_com_rolagem(tabela, fill="both", expand=True)
        primeira = tabela.insert("", "end", values=("x",))
        tabela.insert("", "end", values=("y",))
        tema._foco_na_primeira_linha(SimpleNamespace(widget=tabela))
        self.assertEqual(tabela.focus(), primeira)
        self.assertEqual(tabela.selection(), (primeira,))

    def test_chegar_na_tabela_respeita_a_selecao_existente(self):
        tabela = tema.criar_tabela(self.root, columns=("a",), show="headings")
        tabela.insert("", "end", values=("x",))
        segunda = tabela.insert("", "end", values=("y",))
        tabela.selection_set(segunda)
        tema._foco_na_primeira_linha(SimpleNamespace(widget=tabela))
        self.assertEqual(tabela.focus(), segunda)
        self.assertEqual(tabela.selection(), (segunda,))

    def test_tabela_vazia_nao_quebra(self):
        tabela = tema.criar_tabela(self.root, columns=("a",), show="headings")
        tema._foco_na_primeira_linha(SimpleNamespace(widget=tabela))
        self.assertEqual(tabela.focus(), "")

    def test_enter_no_botao_aciona_uma_vez_so(self):
        # A tela de login liga Enter na janela inteira; o botão não pode
        # disparar a ação e deixar o Enter chegar também à janela.
        chamadas = []
        self.root.bind("<Return>", lambda e: chamadas.append("janela"))
        botao = ttk.Button(self.root, text="Entrar",
                           command=lambda: chamadas.append("botao"))
        botao.pack()
        self.tecla(botao, "<Return>")
        self.assertEqual(chamadas, ["botao"])


if __name__ == "__main__":
    unittest.main()
