package br.rn.cefe.sigbef

import br.rn.cefe.sigbef.aviso.AvisoRegras
import br.rn.cefe.sigbef.data.local.EmprestimoEntity
import java.time.LocalDate
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Regra do aviso de devolução.
 *
 * A verificação é local, a partir do cache, e roda no aparelho do aluno
 * sem ninguém olhando. Errar aqui é avisar quem não devia, ou pior,
 * ficar calado com o livro vencendo.
 */
class AvisoRegrasTest {

    private val hoje = LocalDate.of(2026, 7, 27)

    private fun emprestimo(titulo: String, prazo: String) = EmprestimoEntity(
        livroTitulo = titulo,
        autor = "Autor",
        dataDevolucao = prazo
    )

    // ------------------------------------------------------ quem entra
    @Test
    fun `livro que vence amanha entra no aviso`() {
        val lista = AvisoRegras.aVencer(
            listOf(emprestimo("Dom Casmurro", "2026-07-28")), hoje, 1)
        assertEquals(1, lista.size)
    }

    @Test
    fun `livro que vence hoje entra no aviso`() {
        val lista = AvisoRegras.aVencer(
            listOf(emprestimo("Dom Casmurro", "2026-07-27")), hoje, 1)
        assertEquals(1, lista.size)
    }

    @Test
    fun `livro atrasado entra, e nao fica de fora por ja ter vencido`() {
        // Quem esqueceu ontem precisa mais do lembrete que quem vence
        // amanhã; a versão ingênua desta regra só olharia para frente.
        val lista = AvisoRegras.aVencer(
            listOf(emprestimo("Esquecido", "2026-07-20")), hoje, 1)
        assertEquals(1, lista.size)
    }

    @Test
    fun `livro com prazo distante fica de fora`() {
        val lista = AvisoRegras.aVencer(
            listOf(emprestimo("Tranquilo", "2026-08-15")), hoje, 1)
        assertTrue(lista.isEmpty())
    }

    @Test
    fun `dias antes maior aumenta a janela`() {
        val emprestimos = listOf(emprestimo("Daqui a tres dias", "2026-07-30"))
        assertTrue(AvisoRegras.aVencer(emprestimos, hoje, 1).isEmpty())
        assertEquals(1, AvisoRegras.aVencer(emprestimos, hoje, 3).size)
    }

    @Test
    fun `data ilegivel nao derruba o aviso dos outros`() {
        val lista = AvisoRegras.aVencer(
            listOf(emprestimo("Quebrado", "data estranha"),
                   emprestimo("Bom", "2026-07-28")), hoje, 1)
        assertEquals(1, lista.size)
        assertEquals("Bom", lista.first().first.livroTitulo)
    }

    // -------------------------------------------------------- mensagem
    @Test
    fun `sem nada vencendo nao ha aviso`() {
        assertNull(AvisoRegras.montarMensagem(emptyList(), hoje))
    }

    @Test
    fun `um livro so diz qual e quando`() {
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Dom Casmurro", "2026-07-28")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertTrue(aviso.texto.contains("Dom Casmurro"))
        assertTrue(aviso.texto.contains("vence amanhã"))
    }

    @Test
    fun `um livro atrasado diz que esta atrasado`() {
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Esquecido", "2026-07-20")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertTrue(aviso.texto.contains("está atrasado"))
    }

    @Test
    fun `varios livros dizem quantos, nao a lista`() {
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Um", "2026-07-28"),
                   emprestimo("Dois", "2026-07-28"),
                   emprestimo("Tres", "2026-07-27")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertTrue(aviso.texto.contains("3 livros"))
    }

    @Test
    fun `titulo muda quando ha atraso no meio`() {
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Atrasado", "2026-07-20"),
                   emprestimo("Amanha", "2026-07-28")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertEquals("Livros atrasados", aviso.titulo)
    }

    @Test
    fun `mistura de atrasado e a vencer nao chama tudo de prazo chegando`() {
        // Apareceu no teste em aparelho: o título dizia "Livros
        // atrasados" e o texto falava em "prazo chegando", o que
        // subestima o livro que já venceu.
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Atrasado", "2026-07-20"),
                   emprestimo("Amanha", "2026-07-28")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertTrue(aviso.texto, aviso.texto.contains("1 livro atrasado"))
        assertTrue(aviso.texto, aviso.texto.contains("1 outro vencendo"))
    }

    @Test
    fun `so atrasados diz que estao atrasados`() {
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Um", "2026-07-20"),
                   emprestimo("Dois", "2026-07-21")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertTrue(aviso.texto.contains("2 livros estão atrasados"))
    }

    @Test
    fun `plural correto com varios atrasados e um a vencer`() {
        val vencendo = AvisoRegras.aVencer(
            listOf(emprestimo("Um", "2026-07-20"),
                   emprestimo("Dois", "2026-07-21"),
                   emprestimo("Tres", "2026-07-28")), hoje, 1)
        val aviso = AvisoRegras.montarMensagem(vencendo, hoje)!!
        assertTrue(aviso.texto, aviso.texto.contains("2 livros atrasados"))
        assertTrue(aviso.texto, aviso.texto.contains("1 outro vencendo"))
    }

    // ------------------------------------------------------------ data
    @Test
    fun `entende o formato do servidor e o brasileiro`() {
        assertEquals(LocalDate.of(2026, 7, 28),
                     AvisoRegras.interpretarData("2026-07-28"))
        assertEquals(LocalDate.of(2026, 7, 28),
                     AvisoRegras.interpretarData("28/07/2026"))
    }

    @Test
    fun `data com hora junto tambem serve`() {
        assertEquals(LocalDate.of(2026, 7, 28),
                     AvisoRegras.interpretarData("2026-07-28 14:30:00"))
    }

    @Test
    fun `texto vazio ou invalido devolve nulo em vez de explodir`() {
        assertNull(AvisoRegras.interpretarData(""))
        assertNull(AvisoRegras.interpretarData("qualquer coisa"))
    }
}
