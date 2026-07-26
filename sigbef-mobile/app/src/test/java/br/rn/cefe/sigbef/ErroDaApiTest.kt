package br.rn.cefe.sigbef

import br.rn.cefe.sigbef.data.remote.RetrofitClient
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Leitura do corpo de erro da API.
 *
 * Importa porque as recusas por regra de biblioteca (409) trazem a frase
 * já escrita para o aluno — "Outro leitor está esperando por este livro".
 * Se o app não conseguisse extraí-la, mostraria um "erro 409" inútil.
 */
class ErroDaApiTest {

    @Test
    fun `extrai a mensagem que o servidor escreveu`() {
        val corpo = """{"erro": "Outro leitor está esperando por este livro."}"""
        assertEquals(
            "Outro leitor está esperando por este livro.",
            RetrofitClient.lerErro(corpo)
        )
    }

    @Test
    fun `acentuacao chega intacta`() {
        val corpo = """{"erro": "O prazo já venceu. Passe na biblioteca."}"""
        assertEquals("O prazo já venceu. Passe na biblioteca.",
                     RetrofitClient.lerErro(corpo))
    }

    @Test
    fun `corpo sem o campo erro devolve vazio`() {
        assertEquals("", RetrofitClient.lerErro("""{"outra_coisa": 1}"""))
    }

    @Test
    fun `corpo que nao e json nao derruba o app`() {
        // Um proxy ou uma página de erro do servidor devolveriam HTML.
        assertEquals("", RetrofitClient.lerErro("<html>502 Bad Gateway</html>"))
        assertEquals("", RetrofitClient.lerErro(""))
    }
}
