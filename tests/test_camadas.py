"""As dependências entre camadas só descem: telas -> servicos -> database.

Lê os imports com `ast`, sem executar nada, para que uma tela que volte a
falar direto com o banco quebre aqui e não passe despercebida.
"""
import ast
import unittest
from pathlib import Path

PACOTE = Path(__file__).resolve().parent.parent / "sigbef"


def modulos_importados(arquivo: Path) -> set[str]:
    """Nomes dos módulos do pacote importados pelo arquivo, em qualquer nível."""
    nomes = set()
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.ImportFrom) and no.level:
            if no.module:
                nomes.add(no.module.split(".")[0])
            else:
                nomes |= {a.name for a in no.names}
    return nomes


class TestCamadas(unittest.TestCase):
    def test_telas_nao_falam_com_o_banco(self):
        for tela in sorted(PACOTE.glob("ui_*.py")):
            with self.subTest(tela=tela.name):
                self.assertNotIn("database", modulos_importados(tela))

    def test_reservas_nao_depende_dos_servicos(self):
        # servicos importa reservas; o contrário fecharia um ciclo.
        self.assertNotIn("servicos", modulos_importados(PACOTE / "reservas.py"))

    def test_base_dos_servicos_nao_importa_outros_assuntos(self):
        for nome in ("regras.py", "comum.py"):
            with self.subTest(modulo=nome):
                arquivo = PACOTE / "servicos" / nome
                irmaos = {p.stem for p in (PACOTE / "servicos").glob("*.py")}
                self.assertFalse(modulos_importados(arquivo) & irmaos)


if __name__ == "__main__":
    unittest.main()
