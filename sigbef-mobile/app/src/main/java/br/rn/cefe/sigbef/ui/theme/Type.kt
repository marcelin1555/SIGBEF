package br.rn.cefe.sigbef.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * Escala tipográfica do SIGBEF.
 *
 * Até aqui este arquivo tinha **um** estilo definido (`bodyLarge`) e o
 * resto comentado, do jeito que o assistente de projeto do Android
 * gera. Como nenhuma tela consultava o tema, cada uma escrevia o
 * tamanho na mão — e o resultado medido foi **27 combinações
 * diferentes de tamanho e peso para 91 textos**: onze tamanhos (11, 12,
 * 13, 14, 15, 16, 17, 18, 20, 22, 24, 28, 40) e cinco pesos (Normal,
 * Medium, SemiBold, Bold, ExtraBold). Isso não é hierarquia, é ruído:
 * 15 e 16 sp lado a lado não se leem como níveis, se leem como
 * desalinho.
 *
 * **Os tamanhos saíram do uso real, não de uma escala inventada.** Os
 * grupos que o app já usava de verdade ficaram onde estavam — 13 sp
 * continua 13 sp, 14 continua 14. Só os avulsos foram encostados no
 * vizinho (15 → 14 ou 16, 17 → 18), porque um degrau de 1 sp não é
 * lido como diferença.
 *
 * **Os cinco pesos viraram dois: Regular e Semibold.** Não é escolha
 * minha: é o que o guia da marca manda desde o começo — "Regular no
 * corpo, Semibold em título e destaque" — e o que o desktop e o site já
 * fazem. Bold e ExtraBold no app eram a violação, não a norma. Nesta
 * paleta, navy sobre cinza claro, o peso 800 grita.
 *
 * **A família é a do sistema, de propósito.** O guia manda usar Segoe
 * UI onde ela existe e a pilha do sistema onde não existe; no Android
 * isso é a Roboto. Empacotar um arquivo de fonte custaria mais de
 * 100 KB no APK e ignoraria o tamanho de fonte que a pessoa configurou
 * no próprio aparelho — e este app roda em celular velho de aluno, onde
 * as duas coisas pesam.
 */
private val Familia = FontFamily.Default

/**
 * Os dois pesos, e só eles.
 *
 * Públicos porque existe um caso legítimo de peso fora do estilo: a
 * ênfase que depende do estado — a aba selecionada, a reserva que já
 * tem exemplar separado. Ali o tamanho não muda (mudar faria a linha
 * pular ao ser selecionada), só o peso. Sem estes dois nomes, esse caso
 * voltaria a escrever `FontWeight.Bold` na tela, que é de onde vieram
 * os cinco pesos que este arquivo acabou de reduzir a dois.
 */
val PesoRegular = FontWeight(400)
val PesoSemibold = FontWeight(600)

private val Regular = PesoRegular
private val Semibold = PesoSemibold

val Typography =
  Typography(
    // ------------------------------------------------------- display
    // Números grandes, e só. Um por tela, no máximo: o total de livros
    // lidos, o número do cartão.
    displayLarge =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 40.sp,
        lineHeight = 46.sp,
        letterSpacing = (-0.5).sp,
      ),
    displaySmall =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 28.sp,
        lineHeight = 34.sp,
        letterSpacing = (-0.3).sp,
      ),
    // ------------------------------------------------------ headline
    // Título de tela.
    headlineLarge =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 24.sp,
        lineHeight = 30.sp,
        letterSpacing = (-0.2).sp,
      ),
    headlineMedium =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 22.sp,
        lineHeight = 28.sp,
        letterSpacing = (-0.2).sp,
      ),
    headlineSmall =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 20.sp,
        lineHeight = 26.sp,
        letterSpacing = 0.sp,
      ),
    // --------------------------------------------------------- title
    // Título de cartão e de seção dentro da tela.
    titleLarge =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 18.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.sp,
      ),
    titleMedium =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 16.sp,
        lineHeight = 22.sp,
        letterSpacing = 0.sp,
      ),
    titleSmall =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp,
      ),
    // ---------------------------------------------------------- body
    bodyLarge =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Regular,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.15.sp,
      ),
    bodyMedium =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Regular,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.15.sp,
      ),
    // Texto de apoio: a linha que explica, embaixo do que importa.
    // É o tamanho mais usado do app (18 dos 91 textos medidos), e por
    // isso ficou onde já estava, em 13 sp — os 12 sp de corpo subiram
    // para cá em vez de o contrário, porque num celular de aluno
    // legibilidade vale mais que compactação.
    bodySmall =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Regular,
        fontSize = 13.sp,
        lineHeight = 18.sp,
        letterSpacing = 0.2.sp,
      ),
    // --------------------------------------------------------- label
    // Botão.
    labelLarge =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp,
      ),
    // Pílula de situação, aba, rótulo de campo.
    labelMedium =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.4.sp,
      ),
    // O menor tamanho que ainda se lê num celular de aluno a um braço
    // de distância. Abaixo de 11 sp, não use — aumente o contraste ou
    // corte a informação.
    labelSmall =
      TextStyle(
        fontFamily = Familia,
        fontWeight = Semibold,
        fontSize = 11.sp,
        lineHeight = 15.sp,
        letterSpacing = 0.4.sp,
      ),
  )
