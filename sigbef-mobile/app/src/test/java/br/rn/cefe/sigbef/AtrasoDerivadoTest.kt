package br.rn.cefe.sigbef

import br.rn.cefe.sigbef.aviso.AvisoRegras
import br.rn.cefe.sigbef.data.local.EmprestimoEntity
import br.rn.cefe.sigbef.data.toDomain
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * O atraso é calculado na leitura, não lido do cache.
 *
 * Defeito real: `atrasado` era gravado na sincronização e ficava
 * congelado ali. O aluno que passasse alguns dias sem rede — o caso
 * comum, que é justamente para o qual este app foi feito — via **"Em
 * dia", com selo verde, num livro vencido**. E via, na mesma sessão,
 * "prazo vencido" na tela inicial, porque `HomeScreen` e o aviso de
 * devolução sempre calcularam pela data.
 *
 * O app se contradizia em duas telas sobre o mesmo livro. Estes testes
 * fixam que as três leituras concordam.
 */
class AtrasoDerivadoTest {

    private val fmt = SimpleDateFormat("yyyy-MM-dd", Locale.US)

    private fun diasDaqui(dias: Int): String {
        val cal = Calendar.getInstance()
        cal.time = Date()
        cal.add(Calendar.DAY_OF_MONTH, dias)
        return fmt.format(cal.time)
    }

    /** Entidade como ela sai do cache: com o campo `atrasado` velho. */
    private fun doCache(prazo: String, atrasadoGravado: Boolean,
                        devolvido: Boolean = false) = EmprestimoEntity(
        livroTitulo = "Dom Casmurro",
        autor = "Machado de Assis",
        dataDevolucao = prazo,
        atrasado = atrasadoGravado,
        devolvido = devolvido
    )

    @Test
    fun `livro vencido aparece atrasado mesmo com cache dizendo que nao`() {
        // É o defeito de origem, na forma exata em que acontecia: o
        // aluno sincronizou quando ainda estava no prazo e ficou sem
        // rede; o cache guardou `false` e o dia virou.
        val emp = doCache(diasDaqui(-3), atrasadoGravado = false)
        assertTrue("cache velho não pode mandar na tela",
                   emp.toDomain().atrasado)
    }

    @Test
    fun `livro no prazo nao aparece atrasado mesmo com cache dizendo que sim`() {
        // O contrário também: renovado no balcão, cache ainda com o
        // atraso antigo. Acusar quem está em dia é pior que o inverso.
        val emp = doCache(diasDaqui(5), atrasadoGravado = true)
        assertFalse(emp.toDomain().atrasado)
    }

    @Test
    fun `livro que vence hoje ainda nao esta atrasado`() {
        assertFalse(doCache(diasDaqui(0), atrasadoGravado = false)
                        .toDomain().atrasado)
    }

    @Test
    fun `livro ja devolvido nunca aparece atrasado`() {
        // Devolvido é passado: mesmo tendo vencido, não é pendência.
        val emp = doCache(diasDaqui(-10), atrasadoGravado = true,
                          devolvido = true)
        assertFalse(emp.toDomain().atrasado)
    }

    @Test
    fun `prazo em branco nao inventa atraso`() {
        assertFalse(doCache("", atrasadoGravado = true).toDomain().atrasado)
    }

    @Test
    fun `data com hora junto e comparada so pela parte da data`() {
        val emp = doCache(diasDaqui(2) + " 23:59:00", atrasadoGravado = true)
        assertFalse(emp.toDomain().atrasado)
    }

    // ------------------------------------------------- as três leituras
    @Test
    fun `lista de emprestimos e aviso de devolucao concordam`() {
        // A contradição que o aluno via na tela: uma leitura dizia "Em
        // dia" e a outra dizia "vencido", no mesmo livro, ao mesmo
        // tempo. Se um dia divergirem de novo, este teste quebra.
        val hoje = AvisoRegras.hoje()
        val casos = listOf(-5, -1, 0, 1, 7)

        for (deslocamento in casos) {
            val prazo = diasDaqui(deslocamento)
            val emp = doCache(prazo, atrasadoGravado = false)

            val telaDiz = emp.toDomain().atrasado
            val avisoDiz = AvisoRegras.interpretarData(prazo)!! < hoje

            assertEquals(
                "divergiram para prazo em $deslocamento dia(s): " +
                    "tela=$telaDiz aviso=$avisoDiz",
                avisoDiz, telaDiz
            )
        }
    }
}
