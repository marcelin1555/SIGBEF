"""
SIGBEF — Interface enxuta e boas-vindas.

Menos botões fixos: ações de linha no menu da própria linha, o raro no
"Mais", busca enquanto se digita. E o passo a passo que aparece na
primeira vez de cada pessoa.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

from tests.base import SigbefTestCase

from sigbef import icones
from sigbef import ui_boas_vindas as bv
from sigbef import ui_tema as tema
from sigbef.auth import Sessao


class _ComTk(SigbefTestCase):

    def setUp(self):
        super().setUp()
        try:
            self.root = tk.Tk()
        except tk.TclError as e:  # pragma: no cover - sem display
            self.skipTest(f"Tk indisponível: {e}")
        icones.limpar_cache()  # imagens da janela raiz do teste anterior
        self.root.geometry("900x600+4000+4000")
        tema.aplicar_tema(self.root)
        self.root.update()

    def tearDown(self):
        try:
            self.root.update()  # roda o que ficou agendado antes de fechar
            self.root.destroy()
        except tk.TclError:
            pass
        super().tearDown()

    def esperar(self, ms):
        fim = []
        self.root.after(ms, lambda: fim.append(1))
        while not fim:
            self.root.update()


class TestBuscaAoDigitar(_ComTk):

    def montar(self):
        chamadas = []
        campo = ttk.Entry(self.root)
        campo.pack()
        tema.busca_ao_digitar(campo, lambda: chamadas.append(campo.get()),
                              atraso=80)
        campo.focus_force()
        self.root.update()
        return campo, chamadas

    def digitar(self, campo, texto):
        for letra in texto:
            campo.insert("end", letra)
            campo.event_generate("<KeyRelease>", when="now")

    def test_pesquisa_uma_vez_depois_da_pausa(self):
        campo, chamadas = self.montar()
        self.digitar(campo, "joao")
        self.assertEqual(chamadas, [])  # ainda digitando
        self.esperar(200)
        self.assertEqual(chamadas, ["joao"])

    def test_tecla_que_nao_muda_o_texto_nao_pesquisa(self):
        campo, chamadas = self.montar()
        campo.event_generate("<KeyRelease>", when="now")  # seta, Shift...
        self.esperar(200)
        self.assertEqual(chamadas, [])

    def test_enter_pesquisa_na_hora_e_cancela_a_espera(self):
        campo, chamadas = self.montar()
        self.digitar(campo, "ab")
        campo.event_generate("<Return>", when="now")
        self.root.update()
        self.assertEqual(chamadas, ["ab"])
        self.esperar(200)
        self.assertEqual(chamadas, ["ab"])  # não repetiu


class TestMenus(_ComTk):

    def test_botao_mais_tem_as_acoes_na_ordem(self):
        feito = []
        botao = tema.botao_menu(self.root, "Mais", [
            ("Importar", lambda: feito.append("importar")),
            None,
            ("Etiquetas", lambda: feito.append("etiquetas")),
        ])
        menu = self.root.nametowidget(botao["menu"])
        self.assertEqual(menu.index("end"), 2)
        self.assertEqual(menu.entrycget(0, "label"), "Importar")
        self.assertEqual(menu.type(1), "separator")
        menu.invoke(2)
        self.assertEqual(feito, ["etiquetas"])

    def test_menu_de_linha_pelo_teclado_sem_linha_nao_abre(self):
        tabela = tema.criar_tabela(self.root, columns=("a",), show="headings")
        tema.menu_de_linha(tabela, [("Editar", lambda: None)])
        self.assertTrue(tabela.bind("<Shift-F10>"))
        self.assertTrue(tabela.bind("<Button-3>"))


class TestBotaoDoAluno(_ComTk):
    """Um botão só, que vira 'Entrar na fila' quando não há exemplar."""

    def setUp(self):
        super().setUp()
        from sigbef.ui_painel import SecaoPesquisaAluno
        self.criar_usuario("aluna1")
        sessao = Sessao(id=1, nome="Aluna", matricula="aluna1", perfil="ALUNO")
        painel = SimpleNamespace(sessao=sessao)
        self.secao = SecaoPesquisaAluno(self.root, painel)
        self.secao.pack(fill="both", expand=True)

    def linha(self, disp):
        return self.secao.tree.insert("", "end",
                                      values=(1, "Livro", "", "", "", disp))

    def test_com_exemplar_pega_emprestado(self):
        self.secao.tree.selection_set(self.linha("2/3"))
        self.secao._ajustar_botao()
        self.assertIn("Pegar emprestado", self.secao.btn_acao.cget("text"))

    def test_sem_exemplar_vira_fila_e_o_enter_reserva(self):
        self.secao.tree.selection_set(self.linha("0/2"))
        self.secao._ajustar_botao()
        self.assertIn("fila", self.secao.btn_acao.cget("text"))
        chamou = []
        self.secao._reservar = lambda: chamou.append("fila")
        self.secao._pegar_emprestado = lambda: chamou.append("pegar")
        self.secao._acao_principal()
        self.assertEqual(chamou, ["fila"])

    def test_sem_selecao_tenta_pegar_e_avisa(self):
        self.secao._acao_principal()
        self.assertIn("Selecione", self.secao.lbl_msg.cget("text"))


class TestBoasVindas(_ComTk):

    def sessao(self, perfil="BIBLIOTECARIO", uid=7):
        return Sessao(id=uid, nome="Laiane", matricula="laiane", perfil=perfil)

    def test_primeira_vez_ainda_nao_viu(self):
        self.assertFalse(bv.ja_viu(7))

    def test_cada_pessoa_ve_a_sua(self):
        bv.marcar_como_vista(7)
        self.assertTrue(bv.ja_viu(7))
        self.assertFalse(bv.ja_viu(8))

    def test_conteudo_segue_o_perfil(self):
        d = bv.DialogoBoasVindas(self.root, self.sessao("BIBLIOTECARIO"))
        self.assertIs(d.passos, bv.PASSOS_BIBLIOTECA)
        d.destroy()
        d = bv.DialogoBoasVindas(self.root, self.sessao("ALUNO", 9))
        self.assertIs(d.passos, bv.PASSOS_LEITOR)
        d.destroy()

    def test_navega_e_o_ultimo_botao_fecha_marcando_como_vista(self):
        fechou = []
        d = bv.DialogoBoasVindas(self.root, self.sessao(),
                                 ao_fechar=lambda: fechou.append(1))
        self.assertEqual(d.lbl_passo.cget("text"), "Passo 1 de 5")
        self.assertFalse(d.btn_voltar.winfo_manager())  # nada para voltar
        for _ in range(4):
            d._proximo()
        self.root.update()
        self.assertEqual(d.btn_proximo.cget("text"), "Começar a usar")
        self.assertFalse(d.btn_pular.winfo_manager())
        # Voltar fica à esquerda de Próximo
        self.assertLess(d.btn_voltar.winfo_x(), d.btn_proximo.winfo_x())
        d._proximo()
        self.assertFalse(d.winfo_exists())
        self.assertEqual(fechou, [1])
        self.assertTrue(bv.ja_viu(7))

    def test_pular_tambem_conta_como_visto(self):
        d = bv.DialogoBoasVindas(self.root, self.sessao())
        d.btn_pular.invoke()
        self.assertTrue(bv.ja_viu(7))

    def test_nao_passa_do_primeiro_nem_do_ultimo(self):
        d = bv.DialogoBoasVindas(self.root, self.sessao())
        d._voltar()
        self.assertEqual(d.atual, 0)
        d._ir(99)
        self.assertEqual(d.atual, len(bv.PASSOS_BIBLIOTECA) - 1)
        d.destroy()

    def test_textos_cabem_na_janela(self):
        # O passo 4 já foi cortado no rodapé uma vez: cada passo tem de
        # caber na altura que a janela pede.
        d = bv.DialogoBoasVindas(self.root, self.sessao())
        for i in range(len(d.passos)):
            d._ir(i)
            d.update()
            ultimo = d.corpo.winfo_children()[-1]
            base_texto = ultimo.winfo_rooty() + ultimo.winfo_height()
            topo_botoes = d.btn_proximo.winfo_rooty()
            with self.subTest(passo=i + 1):
                self.assertLess(base_texto, topo_botoes)
        d.destroy()


if __name__ == "__main__":
    import unittest
    unittest.main()
