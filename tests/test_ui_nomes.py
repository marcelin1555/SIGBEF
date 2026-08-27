"""
SIGBEF — Nomes usados na interface existem de verdade.

Existe por causa de um defeito real: "Devolver em lote" foi anunciado na
v1.9.0 e **nunca funcionou**. `ui_painel.py` chamava
`DialogoDevolucaoEmLote`, a classe existia em `ui_dialogos.py`, mas o
nome nunca entrou no import — clicar no botão levantava `NameError`.
Ficou quase um mês em produção sem ninguém notar, porque o executável
empacotado não tem console: o botão era simplesmente inerte.

Nenhum teste pegou porque a camada de interface não tinha teste nenhum
(`ui_painel.py` e `ui_dialogos.py` somam ~4.700 linhas). Este arquivo
cobre a classe inteira do defeito sem precisar abrir janela: percorre a
árvore sintática de cada módulo de interface e confere que todo nome
usado no nível do módulo pode ser resolvido.

Uso:
    python -m unittest tests.test_ui_nomes -v
"""
from __future__ import annotations

import ast
import builtins
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PACOTE = RAIZ / "sigbef"

# Toda a camada de interface. Se um módulo de UI novo aparecer, some aqui.
MODULOS_UI = [
    "ui_painel.py",
    "ui_dialogos.py",
    "ui_selfservice.py",
    "ui_setup.py",
    "ui_login.py",
    "ui_tema.py",
    "ui_graficos.py",
    "icones.py",
]


def _nomes_definidos(tree: ast.Module) -> set[str]:
    """Tudo que o módulo passa a conhecer: imports, defs, classes e
    atribuições de nível de módulo."""
    nomes: set[str] = set(dir(builtins))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                nomes.add(a.asname or a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                nomes.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef,
                               ast.AsyncFunctionDef)):
            nomes.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            nomes.add(node.id)
        elif isinstance(node, ast.arg):
            nomes.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            nomes.add(node.name)
        elif isinstance(node, ast.Global):
            nomes.update(node.names)
        elif isinstance(node, (ast.comprehension,)):
            alvo = node.target
            if isinstance(alvo, ast.Name):
                nomes.add(alvo.id)
    return nomes


def _nomes_usados(tree: ast.Module) -> set[str]:
    return {
        node.id for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }


class TestNomesDaInterface(unittest.TestCase):

    def test_todo_nome_usado_pode_ser_resolvido(self):
        """Nenhum módulo de interface usa um nome que não conhece.

        É esta asserção que teria pego a devolução em lote morta.
        """
        for nome_arquivo in MODULOS_UI:
            caminho = PACOTE / nome_arquivo
            with self.subTest(modulo=nome_arquivo):
                self.assertTrue(caminho.exists(),
                                f"{nome_arquivo} não encontrado")
                tree = ast.parse(caminho.read_text(encoding="utf-8"))
                faltando = _nomes_usados(tree) - _nomes_definidos(tree)
                self.assertEqual(
                    faltando, set(),
                    f"{nome_arquivo} usa nome(s) que não existem no módulo: "
                    f"{sorted(faltando)}. Falta importar?")

    def test_dialogos_usados_pelo_painel_estao_importados(self):
        """Checagem direta do caso concreto, com mensagem específica.

        O teste acima já cobre isto de forma genérica; este existe para
        que a falha diga na cara qual diálogo ficou de fora, em vez de
        um nome solto numa lista.
        """
        painel = ast.parse((PACOTE / "ui_painel.py").read_text(encoding="utf-8"))
        dialogos = ast.parse(
            (PACOTE / "ui_dialogos.py").read_text(encoding="utf-8"))

        definidos_em_dialogos = {
            n.name for n in dialogos.body if isinstance(n, ast.ClassDef)
            and n.name.startswith("Dialogo")
        }
        usados_no_painel = {
            n for n in _nomes_usados(painel) if n.startswith("Dialogo")
        }
        importados = _nomes_definidos(painel)

        for dlg in sorted(usados_no_painel):
            with self.subTest(dialogo=dlg):
                self.assertIn(
                    dlg, importados,
                    f"ui_painel.py chama {dlg} mas não o importa. "
                    f"Clicar no botão correspondente levanta NameError "
                    f"— e no .exe, sem console, o botão só fica inerte.")
                if dlg in definidos_em_dialogos:
                    continue

    def test_modulos_de_ui_importam_sem_erro(self):
        """Import de verdade, não só análise sintática.

        Pega erro de import circular e de nome ausente no topo do módulo.
        Não abre janela nenhuma: nenhum destes módulos cria widget na
        importação.
        """
        import importlib
        for nome_arquivo in MODULOS_UI:
            modulo = f"sigbef.{nome_arquivo[:-3]}"
            with self.subTest(modulo=modulo):
                importlib.import_module(modulo)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
