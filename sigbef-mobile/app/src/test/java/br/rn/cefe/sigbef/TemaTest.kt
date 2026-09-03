package br.rn.cefe.sigbef

import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * O tema tem que chegar às telas — e o modo escuro tem que existir.
 *
 * Três defeitos reais, todos do mesmo tipo: a decisão estava tomada num
 * lugar e ignorada em outro.
 *
 * 1. **`MyApplicationTheme` recebia `darkTheme`, calculava, e usava o
 *    esquema claro de qualquer jeito.** Quem tivesse o celular no modo
 *    escuro — a maioria, e este é um app de consulta rápida no corredor
 *    — levava uma tela branca na cara.
 *
 * 2. **As telas importavam `SigbefNavy` e `SigbefMuted` direto**, que
 *    são os valores do tema *claro*. Mesmo com o esquema escuro ligado,
 *    elas continuariam pintando com os valores claros na mão. Um tema
 *    escuro assim seria só uma barra de topo diferente.
 *
 * 3. **`Type.kt` tinha um estilo definido e o resto comentado**, do
 *    jeito que o assistente do Android gera. Sem escala, cada tela
 *    inventava a sua.
 *
 * Convenção em comentário depende de alguém ler o comentário. Estes
 * testes não dependem.
 */
class TemaTest {

    private fun fontesDeUi(): List<File> {
        val candidatos = listOf(
            File("src/main/java/br/rn/cefe/sigbef/ui"),
            File("app/src/main/java/br/rn/cefe/sigbef/ui"),
            File("../app/src/main/java/br/rn/cefe/sigbef/ui")
        )
        val raiz = candidatos.firstOrNull { it.isDirectory }
        assertTrue(
            "não encontrei as telas a partir de " + File("").absolutePath,
            raiz != null
        )
        // O pacote `theme` é o único lugar onde uma cor pode nascer.
        return raiz!!.walkTopDown()
            .filter { it.isFile && it.extension == "kt" }
            .filter { !it.path.replace('\\', '/').contains("/ui/theme/") }
            .toList()
    }

    /** Linha de código, sem comentário — comentário citando é o oposto do problema. */
    private fun corpo(linha: String): String {
        val sem = linha.substringBefore("//").trim()
        return if (sem.startsWith("*") || sem.startsWith("/*")) "" else sem
    }

    @Test
    fun `nenhuma tela inventa cor`() {
        val infracoes = mutableListOf<String>()
        for (arquivo in fontesDeUi()) {
            arquivo.readLines().forEachIndexed { i, linha ->
                val corpo = corpo(linha)
                if (corpo.isEmpty()) return@forEachIndexed
                val literal = Regex("""Color\(0x""").containsMatchIn(corpo) ||
                    Regex("""\bColor\.(White|Black|Gray|Red|Green|Blue|Yellow|Cyan|Magenta)\b""")
                        .containsMatchIn(corpo)
                if (literal) {
                    infracoes += "${arquivo.name}:${i + 1}  $corpo"
                }
            }
        }
        assertEquals(
            "cor escrita na mão fora do pacote `theme`. Use " +
                "SigbefCores.atual.* (muda com o tema) ou SigbefFixo.* " +
                "(código de barras, câmera — o que não pode mudar):\n" +
                infracoes.joinToString("\n"),
            emptyList<String>(), infracoes
        )
    }

    @Test
    fun `nenhuma tela importa a paleta clara direto`() {
        // Estes são os valores do tema CLARO. Importá-los numa tela é
        // exatamente o que impedia o modo escuro de funcionar.
        val proibidos = listOf(
            "SigbefNavy", "SigbefBlue", "SigbefGold", "SigbefBackground",
            "SigbefSurface", "SigbefLine", "SigbefInk", "SigbefMuted",
            "SigbefSuccess", "SigbefWarning", "SigbefError"
        )
        // Exceções conscientes, com motivo:
        //  · Marca.kt monta o gradiente da marca num `val` de módulo, que
        //    não pode ler um CompositionLocal. Ele é fixo nos dois temas
        //    de propósito — é a barra da marca.
        //  · BarcodeView desenha papel branco e tinta preta de verdade,
        //    para o leitor do balcão enxergar; o texto de apoio ali vive
        //    sobre esse papel fixo.
        val comMotivo = setOf("Marca.kt", "BarcodeView.kt")

        val infracoes = mutableListOf<String>()
        for (arquivo in fontesDeUi()) {
            if (arquivo.name in comMotivo) continue
            arquivo.readLines().forEachIndexed { i, linha ->
                if (!linha.startsWith("import br.rn.cefe.sigbef.ui.theme.")) {
                    return@forEachIndexed
                }
                val nome = linha.substringAfterLast('.')
                if (nome in proibidos) {
                    infracoes += "${arquivo.name}:${i + 1} importa $nome"
                }
            }
        }
        assertEquals(
            "tela importando a paleta clara. Use SigbefCores.atual.*, " +
                "que resolve para o tema em vigor:\n" +
                infracoes.joinToString("\n"),
            emptyList<String>(), infracoes
        )
    }

    @Test
    fun `o tema escuro existe e nao repete o claro`() {
        val arquivo = listOf(
            File("src/main/java/br/rn/cefe/sigbef/ui/theme/Theme.kt"),
            File("app/src/main/java/br/rn/cefe/sigbef/ui/theme/Theme.kt"),
            File("../app/src/main/java/br/rn/cefe/sigbef/ui/theme/Theme.kt")
        ).first { it.isFile }
        val fonte = arquivo.readText()

        assertTrue("não existe um darkColorScheme",
            fonte.contains("darkColorScheme("))
        assertTrue(
            "`darkTheme` é recebido e ignorado — era exatamente o defeito",
            fonte.contains("if (darkTheme) DarkColorScheme else LightColorScheme")
        )
        assertTrue(
            "as cores do SIGBEF não são fornecidas para as telas",
            fonte.contains("CompositionLocalProvider(LocalCoresSigbef provides")
        )
    }

    @Test
    fun `o claro e o escuro definem todas as cores, e diferentes`() {
        val fonte = listOf(
            File("src/main/java/br/rn/cefe/sigbef/ui/theme/Theme.kt"),
            File("app/src/main/java/br/rn/cefe/sigbef/ui/theme/Theme.kt"),
            File("../app/src/main/java/br/rn/cefe/sigbef/ui/theme/Theme.kt")
        ).first { it.isFile }.readText()

        // Os campos saem da própria declaração, e não de uma lista
        // escrita à mão: campo novo em `CoresSigbef` entra neste teste
        // sozinho. Reflexão não serve aqui — `Color` do Compose é uma
        // *value class* e vira `long` em tempo de execução, então o
        // nome do tipo some.
        val declaracao = fonte.substringAfter("data class CoresSigbef(")
            .substringBefore("\n)")
        val campos = Regex("""val (\w+): Color,""")
            .findAll(declaracao).map { it.groupValues[1] }.toList()
        assertTrue("não li os campos de CoresSigbef", campos.size >= 10)

        val claras = fonte.substringAfter("private val CoresClaras")
            .substringBefore("private val CoresEscuras")
        val escuras = fonte.substringAfter("private val CoresEscuras")
            .substringBefore("private val LocalCoresSigbef")

        val faltando = campos
            .filter { nome ->
                !claras.contains("$nome =") || !escuras.contains("$nome =")
            }
        assertEquals(
            "cor declarada em CoresSigbef e não preenchida nos dois temas: " +
                faltando.joinToString(", "),
            emptyList<String>(), faltando
        )
    }

    @Test
    fun `nenhuma tela escreve tamanho de fonte na mao`() {
        // Era o estado anterior: 27 combinações de tamanho e peso para
        // 91 textos, e nenhuma tela consultando o tema. Uma escala que
        // ninguém usa é decoração.
        val infracoes = mutableListOf<String>()
        for (arquivo in fontesDeUi()) {
            arquivo.readLines().forEachIndexed { i, linha ->
                val corpo = corpo(linha)
                if (corpo.contains(Regex("""fontSize\s*="""))) {
                    infracoes += "${arquivo.name}:${i + 1}  $corpo"
                }
            }
        }
        assertEquals(
            "tamanho de fonte escrito na tela. Use " +
                "MaterialTheme.typography.* — a escala está em Type.kt:\n" +
                infracoes.joinToString("\n"),
            emptyList<String>(), infracoes
        )
    }

    @Test
    fun `nenhuma tela escolhe peso fora da escala`() {
        // Bold e ExtraBold no app eram a violação do guia da marca
        // ("Regular no corpo, Semibold em título e destaque"), não a
        // norma. Ênfase que depende do estado usa PesoSemibold /
        // PesoRegular, que são os dois pesos da escala.
        val infracoes = mutableListOf<String>()
        for (arquivo in fontesDeUi()) {
            arquivo.readLines().forEachIndexed { i, linha ->
                val corpo = corpo(linha)
                if (corpo.contains("FontWeight.")) {
                    infracoes += "${arquivo.name}:${i + 1}  $corpo"
                }
            }
        }
        assertEquals(
            "peso escrito na tela. O estilo da escala já traz o peso; " +
                "para ênfase por estado use PesoSemibold / PesoRegular:\n" +
                infracoes.joinToString("\n"),
            emptyList<String>(), infracoes
        )
    }

    @Test
    fun `a escala tipografica esta preenchida`() {
        val fonte = listOf(
            File("src/main/java/br/rn/cefe/sigbef/ui/theme/Type.kt"),
            File("app/src/main/java/br/rn/cefe/sigbef/ui/theme/Type.kt"),
            File("../app/src/main/java/br/rn/cefe/sigbef/ui/theme/Type.kt")
        ).first { it.isFile }.readText()

        // Os papéis que as telas realmente usam. Sem eles, o Material
        // devolve o padrão dele e a hierarquia vira sorte.
        val papeis = listOf(
            "displaySmall", "headlineMedium", "headlineSmall",
            "titleLarge", "titleMedium", "titleSmall",
            "bodyLarge", "bodyMedium", "bodySmall",
            "labelLarge", "labelMedium", "labelSmall"
        )
        val faltando = papeis.filter { !fonte.contains("$it =") }
        assertEquals(
            "papel tipográfico sem estilo definido: " +
                faltando.joinToString(", "),
            emptyList<String>(), faltando
        )
    }
}
