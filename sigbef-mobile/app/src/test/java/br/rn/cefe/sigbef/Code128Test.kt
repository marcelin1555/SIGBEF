package br.rn.cefe.sigbef

import br.rn.cefe.sigbef.ui.components.Code128
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * O cartão diz "apresente este código no balcão", então ele precisa ser
 * legível pelo mesmo leitor que lê o cartão impresso.
 *
 * Os valores esperados foram gerados pela implementação do desktop
 * (`sigbef/barcode_util.py`), que já está em produção — se as duas
 * divergirem, o leitor do balcão não reconhece o celular.
 */
class Code128Test {

    @Test
    fun `valores conferem com a implementacao do desktop`() {
        // start(104) + dígitos + verificador + stop(106)
        assertEquals(
            listOf(104, 18, 16, 18, 20, 16, 16, 17, 68, 106),
            Code128.valores("2024001")
        )
        assertEquals(
            listOf(104, 53, 51, 18, 22, 16, 23, 18, 19, 17, 18, 19, 20, 31, 106),
            Code128.valores("US2607231234")
        )
        assertEquals(listOf(104, 33, 34, 106), Code128.valores("A"))
    }

    @Test
    fun `quantidade de barras confere com o desktop`() {
        assertEquals(61, Code128.barras("2024001").size)
        assertEquals(91, Code128.barras("US2607231234").size)
        assertEquals(25, Code128.barras("A").size)
    }

    @Test
    fun `comeca com barra escura e alterna dentro de cada simbolo`() {
        val barras = Code128.barras("2024001")
        // O padrão inicia sempre pelo start B: 2 escura, 1 clara, 1 escura...
        assertEquals(Pair(2, true), barras[0])
        assertEquals(Pair(1, false), barras[1])
        assertEquals(Pair(1, true), barras[2])
        assertEquals(Pair(2, false), barras[3])
    }

    @Test
    fun `digito verificador muda quando o codigo muda`() {
        val a = Code128.valores("2024001")
        val b = Code128.valores("2024002")
        // penúltimo item é o dígito verificador (antes do stop)
        assertTrue(a[a.size - 2] != b[b.size - 2])
    }

    @Test
    fun `matricula longa continua produzindo barras validas`() {
        val barras = Code128.barras("202530039460")
        assertTrue(barras.isNotEmpty())
        assertTrue(barras.all { it.first in 1..4 })
    }
}
