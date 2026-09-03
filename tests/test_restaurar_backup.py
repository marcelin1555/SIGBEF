"""
SIGBEF — Restaurar um backup pela própria tela.

Até aqui o sistema sabia fazer cópia de segurança e não sabia usá-la.
O roteiro de apresentação chegou a registrar isso como limitação
conhecida: "não existe um botão de restaurar dentro do sistema". Na
prática, restaurar significava alguém copiar um arquivo `.db` por cima
do outro no Explorador — com o sistema em WAL, é exatamente o jeito de
produzir um banco que abre e está pela metade.

Restaurar é a operação mais destrutiva do programa: apaga o acervo
inteiro e põe outro no lugar. Estes testes cobrem as três coisas que
precisam ser verdade para ela poder existir:

1. **Recusa o que não é banco do SIGBEF.** Escolher o arquivo errado
   na hora do desespero é o cenário mais provável de todos.
2. **Guarda o banco atual antes de sobrescrever**, com um nome que a
   rotação de backups não apaga — senão não há como desfazer.
3. **Traz o conteúdo inteiro e migra o schema**, para que um backup
   antigo não derrube o sistema logo na primeira tela.

Uso:
    python -m unittest tests.test_restaurar_backup -v
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from tests.base import SigbefTestCase

from sigbef import backup, servicos
from sigbef.backup import BackupInvalido
from sigbef.database import DB_PATH, db_cursor


class BaseRestauracao(SigbefTestCase):

    def setUp(self):
        super().setUp()
        # Cada teste com sua pasta de backup, ao lado do banco temporário.
        self.pasta = Path(DB_PATH).parent / "backups"
        with db_cursor() as cur:
            cur.execute("UPDATE configuracao SET valor = ? "
                        "WHERE chave = 'BACKUP_PASTA'", (str(self.pasta),))
            cur.execute("INSERT OR IGNORE INTO configuracao (chave, valor) "
                        "VALUES ('BACKUP_PASTA', ?)", (str(self.pasta),))

    def acervo_de(self, arquivo) -> int:
        conn = sqlite3.connect(arquivo)
        try:
            return conn.execute("SELECT COUNT(*) FROM livro").fetchone()[0]
        finally:
            conn.close()


class TestConferirAntesDeRestaurar(BaseRestauracao):

    def test_arquivo_que_nao_existe(self):
        with self.assertRaises(BackupInvalido):
            backup.conferir(self.pasta / "nao_existe.db")

    def test_arquivo_que_nao_e_banco(self):
        """O caso real: alguém aponta para a planilha, ou para o PDF."""
        qualquer = Path(DB_PATH).parent / "relatorio.csv"
        qualquer.write_text("Título;Autor\nDom Casmurro;Machado\n",
                            encoding="utf-8")
        with self.assertRaises(BackupInvalido) as ctx:
            backup.conferir(qualquer)
        self.assertIn("SQLite", str(ctx.exception))

    def test_banco_de_outro_sistema(self):
        """Abre, é SQLite, e mesmo assim não pode passar."""
        outro = Path(DB_PATH).parent / "outro_sistema.db"
        conn = sqlite3.connect(outro)
        conn.execute("CREATE TABLE clientes (id INTEGER, nome TEXT)")
        conn.commit()
        conn.close()
        with self.assertRaises(BackupInvalido) as ctx:
            backup.conferir(outro)
        self.assertIn("livro", str(ctx.exception))

    def test_conferir_resume_o_que_tem_dentro(self):
        """O resumo é o que permite confirmar com número na frente."""
        self.criar_usuario(matricula="a1")
        self.criar_livro(titulo="Um", exemplares=3)
        self.criar_livro(titulo="Dois", exemplares=2)
        copia = backup.copiar()

        resumo = backup.conferir(copia)

        self.assertEqual(resumo["livros"], 2)
        self.assertEqual(resumo["exemplares"], 5)
        self.assertEqual(resumo["usuarios"], 1)
        self.assertEqual(resumo["emprestimos_abertos"], 0)

    def test_conferir_conta_emprestimo_em_aberto(self):
        """É o número que mais importa antes de restaurar: um empréstimo
        que existe hoje e não existe no backup some do sistema."""
        self.criar_usuario(matricula="a1")
        livro = self.criar_livro(exemplares=2)
        servicos.realizar_emprestimo(
            codigo_exemplar=livro["exemplares"][0][1],
            matricula_usuario="a1")
        resumo = backup.conferir(backup.copiar())
        self.assertEqual(resumo["emprestimos_abertos"], 1)

    def test_conferir_nao_altera_o_arquivo(self):
        """Conferir abre em `mode=ro` e não pode mexer no backup.

        O SQLite ainda cria os arquivos-satélite `-wal` e `-shm` ao ler
        um banco em WAL, mesmo sem permissão de escrita no banco; eles
        são dele e ficam vazios. O que precisa ficar intacto é o `.db`,
        que é o backup de verdade.
        """
        self.criar_livro(titulo="Único")
        copia = backup.copiar()
        antes = copia.stat().st_mtime, copia.stat().st_size, copia.read_bytes()

        backup.conferir(copia)

        self.assertEqual(
            (copia.stat().st_mtime, copia.stat().st_size, copia.read_bytes()),
            antes)

    def test_conferir_recusa_escrita_no_backup(self):
        """A garantia por trás do teste acima, medida direto."""
        self.criar_livro(titulo="Único")
        copia = backup.copiar()
        uri = "file:%s?mode=ro" % Path(copia).as_posix()
        conn = sqlite3.connect(uri, uri=True)
        try:
            with self.assertRaises(sqlite3.Error):
                conn.execute("CREATE TABLE invasor (x)")
        finally:
            conn.close()


class TestRestaurar(BaseRestauracao):

    def montar_backup_diferente(self):
        """Um backup com dois livros; depois o banco fica com quatro.

        Assim dá para distinguir "restaurou" de "não fez nada": os
        números têm que voltar a ser os do backup.
        """
        self.criar_usuario(matricula="bib", perfil="BIBLIOTECARIO",
                           nome="Bibliotecária")
        self.criar_livro(titulo="Antigo um")
        self.criar_livro(titulo="Antigo dois")
        copia = backup.copiar()
        self.criar_livro(titulo="Novo três")
        self.criar_livro(titulo="Novo quatro")
        return copia

    def test_restaura_o_conteudo_do_arquivo(self):
        copia = self.montar_backup_diferente()
        self.assertEqual(len(servicos.listar_livros()), 4)

        backup.restaurar(copia)

        titulos = sorted(l["titulo"] for l in servicos.listar_livros())
        self.assertEqual(titulos, ["Antigo dois", "Antigo um"])

    def test_guarda_o_banco_atual_antes_de_sobrescrever(self):
        """Sem isso, restaurar por engano é irreversível."""
        copia = self.montar_backup_diferente()

        res = backup.restaurar(copia)

        salvaguarda = res["salvaguarda"]
        self.assertTrue(salvaguarda.exists())
        self.assertEqual(self.acervo_de(salvaguarda), 4,
                         "a salvaguarda tem que ter o acervo de ANTES")

    def test_salvaguarda_sobrevive_a_rotacao_de_backups(self):
        """A rotação apaga cópias antigas. Ela não pode apagar a única
        coisa que desfaz uma restauração."""
        copia = self.montar_backup_diferente()
        salvaguarda = backup.restaurar(copia)["salvaguarda"]

        for _ in range(10):
            backup.copiar()
        backup.limpar_antigos(manter=1)

        self.assertTrue(salvaguarda.exists(),
                        "a rotação apagou a salvaguarda da restauração")

    def test_da_para_desfazer_restaurando_a_salvaguarda(self):
        """O caminho de volta inteiro, que é a razão de a salvaguarda
        existir."""
        copia = self.montar_backup_diferente()
        salvaguarda = backup.restaurar(copia)["salvaguarda"]
        self.assertEqual(len(servicos.listar_livros()), 2)

        backup.restaurar(salvaguarda)

        self.assertEqual(len(servicos.listar_livros()), 4)

    def test_recusa_arquivo_invalido_sem_tocar_no_banco(self):
        """Recusar tem que ser recusar de verdade: nada de apagar o
        acervo e só depois descobrir que o arquivo não servia."""
        self.criar_livro(titulo="Não pode sumir")
        lixo = Path(DB_PATH).parent / "foto.jpg"
        lixo.write_bytes(b"\xff\xd8\xff\xdb isso nao e banco")

        with self.assertRaises(BackupInvalido):
            backup.restaurar(lixo)

        self.assertEqual(len(servicos.listar_livros()), 1)

    def test_registra_na_auditoria_do_banco_restaurado(self):
        copia = self.montar_backup_diferente()
        backup.restaurar(copia)
        with db_cursor() as cur:
            cur.execute("SELECT acao, detalhes FROM auditoria "
                        "WHERE acao = 'BACKUP_RESTAURADO'")
            linha = cur.fetchone()
        self.assertIsNotNone(linha, "a restauração não ficou registrada")
        self.assertIn("salvaguarda=", linha["detalhes"])

    def test_quem_restaurou_pode_nao_existir_no_backup(self):
        """Backup anterior ao cadastro de quem restaura: o registro fica
        sem dono, e não pode falhar por chave estrangeira."""
        self.criar_livro(titulo="Antigo")
        copia = backup.copiar()
        nova = self.criar_usuario(matricula="nova", perfil="BIBLIOTECARIO",
                                  nome="Contratada depois")

        backup.restaurar(copia, usuario_id=nova["id"])

        with db_cursor() as cur:
            cur.execute("SELECT usuario_id FROM auditoria "
                        "WHERE acao = 'BACKUP_RESTAURADO'")
            self.assertIsNone(cur.fetchone()["usuario_id"])

    def test_backup_antigo_ganha_as_colunas_novas(self):
        """Um backup anterior a uma migração não pode derrubar o sistema.

        Simula o caso apagando do banco atual uma coluna que veio depois
        e restaurando: `restaurar` roda a migração e a coluna volta.
        """
        self.criar_livro(titulo="De antes")
        with db_cursor() as cur:
            cur.execute("PRAGMA table_info(emprestimo)")
            colunas = {r["name"] for r in cur.fetchall()}
        self.assertIn("multa_paga", colunas,
                      "o teste precisa de uma coluna vinda de migração")

        with db_cursor() as cur:
            cur.execute("ALTER TABLE emprestimo DROP COLUMN multa_paga")
        antigo = backup.copiar()

        backup.restaurar(antigo)

        with db_cursor() as cur:
            cur.execute("PRAGMA table_info(emprestimo)")
            colunas = {r["name"] for r in cur.fetchall()}
        self.assertIn("multa_paga", colunas,
                      "restaurou um banco desatualizado e não migrou")

    def test_o_sistema_continua_funcionando_depois(self):
        """Prova de fogo: emprestar um livro do acervo restaurado."""
        copia = self.montar_backup_diferente()
        backup.restaurar(copia)

        self.criar_usuario(matricula="a1")
        livro = servicos.listar_livros()[0]
        detalhe = servicos.detalhes_livro(livro["id"])
        emp = servicos.realizar_emprestimo(
            codigo_exemplar=detalhe["exemplares"][0]["codigo_barras"],
            matricula_usuario="a1")
        self.assertTrue(emp["id"])


class TestConfirmacaoDigitada(SigbefTestCase):
    """A tela exige a frase digitada, como a de apagar tudo.

    Restaurar é a segunda operação mais destrutiva do sistema e a única
    feita sob pressão, quando algo já deu errado — que é justamente
    quando ninguém lê caixa de diálogo. Um sim/não não serve aqui.
    """

    def test_o_dialogo_exige_frase_e_so_entao_restaura(self):
        import ast
        from pathlib import Path as _P

        fonte = (_P(__file__).resolve().parent.parent
                 / "sigbef" / "ui_dialogos.py").read_text(encoding="utf-8")
        arvore = ast.parse(fonte)
        classe = next(
            n for n in ast.walk(arvore)
            if isinstance(n, ast.ClassDef)
            and n.name == "DialogoRestaurarBackup")

        frases = [a.value.value for c in classe.body
                  if isinstance(c, ast.Assign)
                  for a in [c] if isinstance(a.value, ast.Constant)
                  for t in c.targets
                  if isinstance(t, ast.Name) and t.id == "FRASE_CONFIRMACAO"]
        self.assertEqual(frases, ["RESTAURAR"])

        confirmar = next(n for n in classe.body
                         if isinstance(n, ast.FunctionDef)
                         and n.name == "_confirmar")
        corpo = ast.unparse(confirmar)
        self.assertIn("FRASE_CONFIRMACAO", corpo)
        # A checagem tem que vir ANTES da restauração, não depois.
        self.assertLess(corpo.index("FRASE_CONFIRMACAO"),
                        corpo.index("backup.restaurar"),
                        "a restauração acontece antes de conferir a frase")


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
