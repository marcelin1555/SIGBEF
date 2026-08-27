package br.rn.cefe.sigbef

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Nenhum código de produção pode usar API acima do `minSdk`.
 *
 * Existe por causa de um defeito real. O app declara `minSdk = 24`
 * (Android 7) e **não liga desugaring**. `java.time` só existe a partir
 * da API 26, então usá-lo derruba o app no aparelho antigo — que é
 * justamente o aparelho que este app foi feito para atender.
 *
 * A regra já estava estabelecida e escrita em três arquivos
 * (`Repository.hojeIso`, `Marca`, `HomeScreen.proximoVencimento`), cada
 * um explicando por que evitava `java.time`. Mesmo assim
 * `AvisoDevolucao.kt` passou por fora dela, e o aviso de devolução
 * quebrava no Android 7 sem ninguém perceber: o erro só aparece no
 * aparelho certo, e ninguém da equipe tem um.
 *
 * Convenção escrita em comentário depende de alguém ler o comentário.
 * Este teste não depende.
 */
class ApiMinimaTest {

    /** API que exige nível acima do minSdk -> por que não pode. */
    private val proibidas = mapOf(
        "java.time" to "exige API 26; o app é minSdk 24 sem desugaring. " +
            "Use texto ISO com SimpleDateFormat/Calendar, como " +
            "Repository.hojeIso e AvisoRegras já fazem.",
        "java.util.stream" to "exige API 24+ com pegadinhas de " +
            "desugaring. Use as coleções do Kotlin.",
        "java.util.Optional" to "exige API 24+; em Kotlin o tipo " +
            "anulável já resolve."
    )

    private fun fontesDeProducao(): List<File> {
        // Gradle roda o teste com o diretório do módulo como raiz, mas
        // não custa aceitar a raiz do projeto também.
        val candidatos = listOf(
            File("src/main/java"),
            File("app/src/main/java"),
            File("../app/src/main/java")
        )
        val raiz = candidatos.firstOrNull { it.isDirectory }
        assertTrue(
            "não encontrei as fontes de produção a partir de " +
                File("").absolutePath,
            raiz != null
        )
        return raiz!!.walkTopDown()
            .filter { it.isFile && it.extension == "kt" }
            .toList()
    }

    @Test
    fun `fontes de producao nao usam API acima do minSdk`() {
        val fontes = fontesDeProducao()
        assertTrue("nenhum .kt encontrado", fontes.isNotEmpty())

        val infracoes = mutableListOf<String>()
        for (arquivo in fontes) {
            arquivo.readLines().forEachIndexed { i, linha ->
                // Comentário citando a API é o contrário do problema:
                // é alguém explicando por que não usou.
                val corpo = linha.substringBefore("//").trim()
                if (corpo.startsWith("*") || corpo.startsWith("/*")) return@forEachIndexed
                for ((api, motivo) in proibidas) {
                    if (corpo.contains(api)) {
                        infracoes += "${arquivo.name}:${i + 1} usa $api — $motivo"
                    }
                }
            }
        }
        assertEquals(
            "API acima do minSdk em código de produção:\n" +
                infracoes.joinToString("\n"),
            emptyList<String>(), infracoes
        )
    }
}
