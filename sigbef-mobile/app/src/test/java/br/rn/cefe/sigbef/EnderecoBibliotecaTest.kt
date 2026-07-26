package br.rn.cefe.sigbef

import br.rn.cefe.sigbef.data.remote.RetrofitClient
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * O endereço da biblioteca é digitado à mão pelo aluno e o login viaja em
 * HTTP na rede da escola. Se o app aceitasse um host qualquer da internet,
 * matrícula e senha iriam para lá em texto puro — por isso estas regras
 * são testadas.
 */
class EnderecoBibliotecaTest {

    @Test
    fun `aceita enderecos de rede local`() {
        val locais = listOf(
            "192.168.0.104:8765",
            "192.168.1.100:8765",
            "10.0.0.5:8765",
            "172.16.5.9:8765",
            "172.31.255.254:8765",
            "127.0.0.1:8765",
            "biblioteca.local",
            "sigbef.lan",
            "localhost:8765"
        )
        for (endereco in locais) {
            assertTrue(
                "deveria aceitar $endereco",
                RetrofitClient.eEnderecoLocal(endereco)
            )
        }
    }

    @Test
    fun `recusa enderecos publicos`() {
        val publicos = listOf(
            "sigbef-api.cefe.edu.br",   // domínio inventado que existia no código
            "8.8.8.8:8765",
            "exemplo.com",
            "200.130.1.1:8765",
            "172.15.0.1:8765",          // logo abaixo da faixa privada
            "172.32.0.1:8765"           // logo acima da faixa privada
        )
        for (endereco in publicos) {
            assertFalse(
                "deveria recusar $endereco",
                RetrofitClient.eEnderecoLocal(endereco)
            )
        }
    }

    @Test
    fun `normaliza o que o aluno digita`() {
        // Sem esquema, vira http
        assertEquals("http://192.168.0.1:8765/",
                     RetrofitClient.normalizar("192.168.0.1:8765"))
        // O formato do QR code é aceito
        assertEquals("http://192.168.0.1:8765/",
                     RetrofitClient.normalizar("sigbef://192.168.0.1:8765"))
        // Espaços sobrando não atrapalham
        assertEquals("http://192.168.0.1:8765/",
                     RetrofitClient.normalizar("  192.168.0.1:8765  "))
        // URL completa é preservada
        assertEquals("http://192.168.0.1:8765/",
                     RetrofitClient.normalizar("http://192.168.0.1:8765/"))
    }

    @Test
    fun `endereco vazio nao e considerado local`() {
        assertFalse(RetrofitClient.eEnderecoLocal(""))
        assertFalse(RetrofitClient.eEnderecoLocal("   "))
    }
}
