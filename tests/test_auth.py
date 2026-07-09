"""
SIGBEF — Testes de autenticação (sigbef.auth).

Cobre gerar_hash, verificar_senha, autenticar, autenticar_por_codigo
e as propriedades de perfil da Sessao.
"""
from tests.base import SigbefTestCase

from sigbef import auth
from sigbef.auth import Sessao, autenticar, autenticar_por_codigo, gerar_hash, verificar_senha


class TestGerarHash(SigbefTestCase):
    """Formato e aleatoriedade do hash de senha."""

    def test_formato_do_hash(self):
        """Hash segue o formato pbkdf2$<iteracoes>$<salt_hex>$<hash_hex>."""
        h = gerar_hash("minhasenha")
        partes = h.split("$")
        self.assertEqual(len(partes), 4)
        algo, iteracoes, salt_hex, hash_hex = partes
        self.assertEqual(algo, "pbkdf2")
        self.assertEqual(int(iteracoes), auth.ITERACOES)
        # salt de 16 bytes -> 32 caracteres hex; sha256 -> 64 caracteres hex
        self.assertEqual(len(salt_hex), 32)
        self.assertEqual(len(hash_hex), 64)
        bytes.fromhex(salt_hex)  # não deve levantar (é hex válido)
        bytes.fromhex(hash_hex)

    def test_sal_aleatorio_gera_hashes_diferentes(self):
        """Duas chamadas com a mesma senha produzem hashes distintos (sal novo)."""
        h1 = gerar_hash("mesma-senha")
        h2 = gerar_hash("mesma-senha")
        self.assertNotEqual(h1, h2)
        # mas ambos verificam a senha original
        self.assertTrue(verificar_senha("mesma-senha", h1))
        self.assertTrue(verificar_senha("mesma-senha", h2))


class TestVerificarSenha(SigbefTestCase):
    """Verificação de senha contra hash armazenado, inclusive entradas malformadas."""

    def test_senha_correta_retorna_true(self):
        h = gerar_hash("segredo123")
        self.assertTrue(verificar_senha("segredo123", h))

    def test_senha_errada_retorna_false(self):
        h = gerar_hash("segredo123")
        self.assertFalse(verificar_senha("outra-coisa", h))

    def test_hash_vazio_retorna_false(self):
        self.assertFalse(verificar_senha("qualquer", ""))

    def test_hash_sem_cifrao_retorna_false(self):
        self.assertFalse(verificar_senha("qualquer", "hash-sem-separador"))

    def test_algoritmo_diferente_retorna_false(self):
        h = gerar_hash("senha")
        h_alterado = h.replace("pbkdf2", "sha1", 1)
        self.assertFalse(verificar_senha("senha", h_alterado))

    def test_hash_corrompido_nao_levanta_excecao(self):
        """Qualquer hash malformado deve resultar em False, nunca em exceção."""
        casos = [
            "",
            "$$$",
            "pbkdf2$abc$zz$ww",          # iterações não numéricas / hex inválido
            "pbkdf2$1000$nao-hex$tambem-nao",
            "pbkdf2$1000$aabb",           # faltando um campo
            "pbkdf2$1000$aa$bb$cc",       # campo a mais
            None,                          # AttributeError tratado
        ]
        for hash_ruim in casos:
            with self.subTest(hash=hash_ruim):
                self.assertFalse(verificar_senha("senha", hash_ruim))


class TestAutenticar(SigbefTestCase):
    """Login por matrícula e senha."""

    def test_sucesso_com_credenciais_validas(self):
        criado = self.criar_usuario(matricula="mat001", nome="Fulano", perfil="ALUNO")
        sessao = autenticar("mat001", "senha123")
        self.assertIsNotNone(sessao)
        self.assertEqual(sessao.id, criado["id"])
        self.assertEqual(sessao.nome, "Fulano")
        self.assertEqual(sessao.matricula, "mat001")
        self.assertEqual(sessao.perfil, "ALUNO")

    def test_matricula_com_espacos_em_volta_funciona(self):
        """A matrícula digitada com espaços deve ser aceita (strip)."""
        self.criar_usuario(matricula="mat002")
        sessao = autenticar("  mat002  ", "senha123")
        self.assertIsNotNone(sessao)
        self.assertEqual(sessao.matricula, "mat002")

    def test_senha_errada_retorna_none(self):
        self.criar_usuario(matricula="mat003")
        self.assertIsNone(autenticar("mat003", "senha-errada"))

    def test_matricula_inexistente_retorna_none(self):
        self.assertIsNone(autenticar("nao-existe", "senha123"))

    def test_matricula_vazia_retorna_none(self):
        self.assertIsNone(autenticar("", "senha123"))
        self.assertIsNone(autenticar("   ", "senha123"))

    def test_senha_vazia_retorna_none(self):
        self.criar_usuario(matricula="mat004")
        self.assertIsNone(autenticar("mat004", ""))

    def test_usuario_desativado_retorna_none(self):
        from sigbef import servicos
        criado = self.criar_usuario(matricula="mat005")
        # antes de desativar, o login funciona
        self.assertIsNotNone(autenticar("mat005", "senha123"))
        servicos.alternar_status_usuario(criado["id"], ativo=False)
        self.assertIsNone(autenticar("mat005", "senha123"))


class TestAutenticarPorCodigo(SigbefTestCase):
    """Login alternativo pelo código de barras do cartão."""

    def test_sucesso_com_codigo_do_cartao(self):
        criado = self.criar_usuario(matricula="mat010", nome="Ciclana")
        self.assertIsNotNone(criado["codigo_barras"])
        sessao = autenticar_por_codigo(criado["codigo_barras"])
        self.assertIsNotNone(sessao)
        self.assertEqual(sessao.id, criado["id"])
        self.assertEqual(sessao.nome, "Ciclana")
        self.assertEqual(sessao.matricula, "mat010")

    def test_codigo_inexistente_retorna_none(self):
        self.assertIsNone(autenticar_por_codigo("USR-INEXISTENTE"))

    def test_usuario_inativo_retorna_none(self):
        from sigbef import servicos
        criado = self.criar_usuario(matricula="mat011")
        servicos.alternar_status_usuario(criado["id"], ativo=False)
        self.assertIsNone(autenticar_por_codigo(criado["codigo_barras"]))

    def test_codigo_vazio_retorna_none(self):
        self.assertIsNone(autenticar_por_codigo(""))
        self.assertIsNone(autenticar_por_codigo("   "))
        self.assertIsNone(autenticar_por_codigo(None))


class TestPropriedadesSessao(SigbefTestCase):
    """Propriedades de perfil (is_admin, is_bibliotecario, is_aluno, is_professor)."""

    def _sessao(self, perfil):
        return Sessao(id=1, nome="Teste", matricula="m1", perfil=perfil)

    def test_administrador(self):
        s = self._sessao("ADMINISTRADOR")
        self.assertTrue(s.is_admin)
        self.assertTrue(s.is_bibliotecario)  # admin também é bibliotecário
        self.assertFalse(s.is_aluno)
        self.assertFalse(s.is_professor)

    def test_bibliotecario(self):
        s = self._sessao("BIBLIOTECARIO")
        self.assertFalse(s.is_admin)
        self.assertTrue(s.is_bibliotecario)
        self.assertFalse(s.is_aluno)
        self.assertFalse(s.is_professor)

    def test_aluno(self):
        s = self._sessao("ALUNO")
        self.assertFalse(s.is_admin)
        self.assertFalse(s.is_bibliotecario)
        self.assertTrue(s.is_aluno)
        self.assertFalse(s.is_professor)

    def test_professor(self):
        s = self._sessao("PROFESSOR")
        self.assertFalse(s.is_admin)
        self.assertFalse(s.is_bibliotecario)
        self.assertFalse(s.is_aluno)
        self.assertTrue(s.is_professor)


if __name__ == "__main__":  # pragma: no cover
    import unittest
    unittest.main()
