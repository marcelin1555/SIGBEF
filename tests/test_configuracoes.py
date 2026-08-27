"""
SIGBEF — Configurações do sistema: validação e rastro na auditoria.

Dois defeitos reais deram origem a este arquivo:

1. **"Salvo com sucesso" mentindo.** A tela gravava com `set_config` sem
   validar. Quem digitava `0,50` na multa por dia — a forma normal de
   escrever meio real num teclado brasileiro — recebia a confirmação, mas
   `_config_float` não converte vírgula: caía no `except`, voltava para o
   padrão, e o sistema seguia cobrando R$ 1,50 por dia. Ninguém tinha como
   perceber pela tela, porque a tela mostrava o que foi digitado.

2. **Mudança de configuração sem autor.** Prazo, limite, multa, senha do
   SMTP e porta da API iam direto para o banco. Trocar o prazo de 7 para 30
   dias não deixava uma linha sequer na auditoria.
"""
from __future__ import annotations

from tests.base import SigbefTestCase

from sigbef import servicos
from sigbef.database import get_config, set_config
from sigbef.servicos import RegraNegocioError


class TestNormalizarConfig(SigbefTestCase):

    def test_virgula_decimal_e_aceita(self):
        """É o defeito de origem: 0,50 tem que virar 0.50, não sumir."""
        self.assertEqual(servicos.normalizar_config("MULTA_POR_DIA", "0,50"),
                         "0.50")
        # Separador de milhar junto com a vírgula decimal, dentro do teto.
        self.assertEqual(servicos.normalizar_config("MULTA_TETO", "1.000,00"),
                         "1000.00")

    def test_ponto_decimal_continua_valendo(self):
        self.assertEqual(servicos.normalizar_config("MULTA_POR_DIA", "2.25"),
                         "2.25")

    def test_valor_normalizado_sobrevive_a_leitura_do_sistema(self):
        """O que é gravado tem que ser lido de volta pelo cálculo da multa.

        É a ponta solta que fazia o valor sumir: `_config_float` usa
        `float()` cru, então só um valor com ponto é lido de verdade.
        """
        set_config("MULTA_POR_DIA",
                   servicos.normalizar_config("MULTA_POR_DIA", "0,50"))
        self.assertAlmostEqual(
            servicos._config_float("MULTA_POR_DIA", 1.5), 0.50)

    def test_texto_sem_numero_e_recusado(self):
        with self.assertRaises(RegraNegocioError) as ctx:
            servicos.normalizar_config("MULTA_POR_DIA", "abc")
        self.assertIn("Multa por dia", str(ctx.exception))

    def test_prazo_precisa_ser_inteiro(self):
        with self.assertRaises(RegraNegocioError):
            servicos.normalizar_config("PRAZO_ALUNO_DIAS", "7,5")

    def test_valor_fora_da_faixa_e_recusado(self):
        for chave, valor in [("PRAZO_ALUNO_DIAS", "0"),
                             ("PRAZO_ALUNO_DIAS", "9999"),
                             ("LIMITE_ALUNO", "0"),
                             ("MULTA_POR_DIA", "-1")]:
            with self.subTest(chave=chave, valor=valor):
                with self.assertRaises(RegraNegocioError):
                    servicos.normalizar_config(chave, valor)

    def test_nome_da_instituicao_nao_pode_ficar_vazio(self):
        with self.assertRaises(RegraNegocioError):
            servicos.normalizar_config("NOME_INSTITUICAO", "   ")


class TestSalvarConfiguracoes(SigbefTestCase):

    def _valores_validos(self, **troca):
        base = {chave: get_config(chave) for chave in servicos.CAMPOS_CONFIG}
        base.update(troca)
        return base

    def test_grava_e_devolve_o_que_mudou(self):
        alterados = servicos.salvar_configuracoes(
            self._valores_validos(PRAZO_ALUNO_DIAS="10"), executor_id=None)
        self.assertEqual(get_config("PRAZO_ALUNO_DIAS"), "10")
        self.assertEqual(alterados, ["Prazo padrão para alunos (dias)"])

    def test_sem_mudanca_nao_inventa_alteracao(self):
        self.assertEqual(
            servicos.salvar_configuracoes(self._valores_validos()), [])

    def test_um_campo_invalido_nao_grava_nenhum(self):
        """Validação antes da escrita — nada de formulário salvo pela metade."""
        antes = get_config("PRAZO_ALUNO_DIAS")
        with self.assertRaises(RegraNegocioError):
            servicos.salvar_configuracoes(
                self._valores_validos(PRAZO_ALUNO_DIAS="20",
                                      MULTA_POR_DIA="abc"))
        self.assertEqual(get_config("PRAZO_ALUNO_DIAS"), antes)

    def test_alteracao_aparece_na_auditoria_com_valor_antigo_e_novo(self):
        antes = get_config("PRAZO_ALUNO_DIAS")
        servicos.salvar_configuracoes(
            self._valores_validos(PRAZO_ALUNO_DIAS="30"), executor_id=None)
        registros = [r for r in servicos.listar_auditoria()
                     if r["acao"] == "CONFIG_ALTERADA"]
        self.assertEqual(len(registros), 1)
        self.assertIn("PRAZO_ALUNO_DIAS", registros[0]["detalhes"])
        self.assertIn(f"'{antes}'", registros[0]["detalhes"])
        self.assertIn("'30'", registros[0]["detalhes"])

    def test_salvar_igual_nao_polui_a_auditoria(self):
        servicos.salvar_configuracoes(self._valores_validos())
        self.assertEqual(
            [r for r in servicos.listar_auditoria()
             if r["acao"] == "CONFIG_ALTERADA"], [])


class TestDefinirConfigAuditada(SigbefTestCase):

    def test_registra_mudanca_de_chave_avulsa(self):
        mudou = servicos.definir_config_auditada("API_PORTA", "9000")
        self.assertTrue(mudou)
        self.assertEqual(get_config("API_PORTA"), "9000")
        acoes = [r["acao"] for r in servicos.listar_auditoria()]
        self.assertIn("CONFIG_ALTERADA", acoes)

    def test_valor_igual_nao_registra_nada(self):
        servicos.definir_config_auditada("API_PORTA", "9000")
        self.assertFalse(servicos.definir_config_auditada("API_PORTA", "9000"))
        self.assertEqual(
            len([r for r in servicos.listar_auditoria()
                 if r["acao"] == "CONFIG_ALTERADA"]), 1)

    def test_senha_do_smtp_nunca_vai_para_a_auditoria(self):
        """A auditoria registra *que* mudou, não *para quê*."""
        servicos.definir_config_auditada("SMTP_SENHA", "sup3r-s3cr3ta")
        detalhes = " ".join(r["detalhes"] for r in servicos.listar_auditoria())
        self.assertNotIn("sup3r-s3cr3ta", detalhes)
        self.assertIn("SMTP_SENHA", detalhes)

    def test_tema_passa_pela_auditoria(self):
        from sigbef import ui_tema
        ui_tema.salvar_cores("#123456", "#234567", "#345678", "#456789",
                             executor_id=None)
        acoes = [r["acao"] for r in servicos.listar_auditoria()]
        self.assertEqual(acoes.count("TEMA_ALTERADO"), 4)
        self.assertEqual(get_config("tema.cor_primaria"), "#123456")


class TestReparoDeBancoAntigo(SigbefTestCase):
    """Banco que já está na escola pode ter `'0,50'` gravado.

    A validação nova impede que isso volte a acontecer, mas não conserta
    o que já está lá — e enquanto estiver lá a multa cobrada é a errada,
    sem aviso nenhum.
    """

    def test_virgula_gravada_antes_da_atualizacao_e_corrigida(self):
        from sigbef import database
        set_config("MULTA_POR_DIA", "0,50")
        with database.db_cursor() as cur:
            database._reparar_numeros_de_config(cur)
        self.assertEqual(get_config("MULTA_POR_DIA"), "0.50")
        self.assertAlmostEqual(
            servicos._config_float("MULTA_POR_DIA", 1.5), 0.50)

    def test_reparo_fica_registrado_na_auditoria(self):
        from sigbef import database
        set_config("MULTA_TETO", "80,00")
        with database.db_cursor() as cur:
            database._reparar_numeros_de_config(cur)
        acoes = [r["acao"] for r in servicos.listar_auditoria()]
        self.assertIn("CONFIG_REPARADA", acoes)

    def test_valor_ilegivel_nao_e_chutado(self):
        """Não inventar valor de multa é mais importante que consertar."""
        from sigbef import database
        set_config("MULTA_POR_DIA", "R$ 0,50 por dia")
        with database.db_cursor() as cur:
            database._reparar_numeros_de_config(cur)
        self.assertEqual(get_config("MULTA_POR_DIA"), "R$ 0,50 por dia")

    def test_valor_ja_correto_nao_e_tocado(self):
        from sigbef import database
        set_config("MULTA_POR_DIA", "1.50")
        with database.db_cursor() as cur:
            database._reparar_numeros_de_config(cur)
        self.assertEqual(get_config("MULTA_POR_DIA"), "1.50")
        self.assertEqual(
            [r for r in servicos.listar_auditoria()
             if r["acao"] == "CONFIG_REPARADA"], [])


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
