package br.rn.cefe.sigbef

import br.rn.cefe.sigbef.ui.components.dataParaLer
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * A biblioteca fala ISO (`2026-08-02`) porque é o formato do SQLite e
 * ordena sozinho. Ninguém no Brasil lê uma data assim, então a tela
 * converte — sem nunca esconder um dado que existe.
 */
class DataParaLerTest {

    @Test
    fun `iso vira dia barra mes barra ano`() {
        assertEquals("02/08/2026", dataParaLer("2026-08-02"))
    }

    @Test
    fun `ignora a hora que o sqlite anexa`() {
        assertEquals("02/08/2026", dataParaLer("2026-08-02 14:35:00"))
    }

    @Test
    fun `data ausente nao vira texto estranho`() {
        assertEquals("", dataParaLer(null))
        assertEquals("", dataParaLer(""))
    }

    @Test
    fun `formato inesperado passa intacto em vez de sumir`() {
        // Melhor o aluno ver algo cru do que a informação desaparecer.
        assertEquals("02/08/2026", dataParaLer("02/08/2026"))
        assertEquals("amanhã", dataParaLer("amanhã"))
        assertEquals("2026-8-2", dataParaLer("2026-8-2"))
        assertEquals("abcd-ef-gh", dataParaLer("abcd-ef-gh"))
    }
}
