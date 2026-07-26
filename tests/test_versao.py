"""
SIGBEF — Coerência da versão entre os arquivos que a declaram.

Existe porque a versão vive em três lugares e eles divergiram: o arquivo
`VERSION` ficou parado em 1.4.0 enquanto o pacote já ia em 1.6.2, três
lançamentos atrás. Ninguém percebeu porque `VERSION` não é lido por
código nenhum — só por gente, e gente lê e acredita.

Uso:
    python -m unittest tests.test_versao -v
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# dd.dd.dd — o suficiente para pegar erro de digitação sem virar um
# validador de semver completo.
_FORMATO = re.compile(r"^\d+\.\d+\.\d+$")


def _versao_do_pacote() -> str:
    """Lê a versão sem importar o pacote (que puxaria o banco junto)."""
    texto = (RAIZ / "sigbef" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', texto)
    assert m, "__version__ não encontrado em sigbef/__init__.py"
    return m.group(1)


class TestVersaoCoerente(unittest.TestCase):

    def test_arquivo_version_bate_com_o_pacote(self):
        arquivo = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(
            arquivo, _versao_do_pacote(),
            "VERSION e sigbef/__init__.py discordam. Ao lançar uma versão, "
            "atualize os dois (e site/src/versao.js).")

    def test_site_bate_com_o_pacote(self):
        """O site mostra a versão no hero — errada, ela vira propaganda falsa."""
        arquivo = RAIZ / "site" / "src" / "versao.js"
        if not arquivo.exists():
            self.skipTest("site não está presente nesta cópia")
        texto = arquivo.read_text(encoding="utf-8")
        m = re.search(r"VERSAO\s*=\s*['\"]([^'\"]+)['\"]", texto)
        self.assertIsNotNone(m, "VERSAO não encontrada em site/src/versao.js")
        self.assertEqual(m.group(1), _versao_do_pacote())

    def test_changelog_tem_a_versao_atual(self):
        """Versão lançada sem entrada no changelog é versão sem história."""
        texto = (RAIZ / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{_versao_do_pacote()}]", texto)

    def test_formato_valido(self):
        self.assertRegex(_versao_do_pacote(), _FORMATO)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
