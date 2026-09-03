package br.rn.cefe.sigbef.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

/**
 * Só cores da marca.
 *
 * Os *container* vinham do gerador de tema do Material 3 (D1E4FF,
 * 7CBAFF, 001D35, 004A7D): azuis parecidos com os nossos, mas de outra
 * família. Como os componentes do Material os usam por padrão, aquela
 * paleta reaparecia nas telas sem ninguém ter escolhido. Agora derivam
 * do navy e do azul de verdade.
 */
private val LightColorScheme =
  lightColorScheme(
    primary = SigbefNavy,
    onPrimary = Color.White,
    primaryContainer = SigbefBlueFundo,
    onPrimaryContainer = SigbefNavy,
    secondary = SigbefBlue,
    onSecondary = Color.White,
    secondaryContainer = SigbefBlueFundo,
    onSecondaryContainer = SigbefNavy,
    tertiary = SigbefGold,
    onTertiary = SigbefNavy,
    background = SigbefBackground,
    onBackground = SigbefInk,
    surface = SigbefSurface,
    onSurface = SigbefInk,
    surfaceVariant = SigbefSurfaceContainerLow,
    onSurfaceVariant = SigbefMuted,
    outline = SigbefLine,
    error = SigbefError,
    errorContainer = SigbefErrorFundo,
    onErrorContainer = SigbefError,
    // Os tons de superfície que os diálogos e menus usam. Sem eles o
    // Material inventa um lilás (visto no diálogo de pareamento), que
    // não existe em lugar nenhum da marca.
    surfaceContainerLowest = SigbefSurface,
    surfaceContainerLow = SigbefSurface,
    surfaceContainer = SigbefSurface,
    surfaceContainerHigh = SigbefSurface,
    surfaceContainerHighest = SigbefSurfaceContainerLow,
    inverseSurface = SigbefNavy,
    inverseOnSurface = Color.White,
  )

/**
 * O tema escuro, que até aqui não existia.
 *
 * `MyApplicationTheme` recebia `darkTheme` e `dynamicColor`, calculava
 * os dois e usava o esquema claro de qualquer jeito. Quem tivesse o
 * celular no escuro — a maioria, e este app é de consulta rápida no
 * corredor — levava uma tela branca de 1.400 nits na cara.
 *
 * A troca de papéis está explicada nas cores: **no escuro o navy deixa
 * de ser a primária** (some no fundo) e passa a ser a superfície
 * elevada; quem vira primária é o azul claro. Por isso `onPrimary` aqui
 * é escuro, e não branco: o texto vai *sobre* o azul claro.
 */
private val DarkColorScheme =
  darkColorScheme(
    primary = SigbefBlueClaro,
    onPrimary = SigbefNavyEscuro,
    primaryContainer = SigbefBlueFundoEscuro,
    onPrimaryContainer = SigbefBlueClaro,
    secondary = SigbefBlueClaro,
    onSecondary = SigbefNavyEscuro,
    secondaryContainer = SigbefBlueFundoEscuro,
    onSecondaryContainer = SigbefBlueClaro,
    tertiary = SigbefGoldEscuro,
    onTertiary = SigbefNavyEscuro,
    background = SigbefBackgroundEscuro,
    onBackground = SigbefInkClaro,
    surface = SigbefSurfaceEscuro,
    onSurface = SigbefInkClaro,
    surfaceVariant = SigbefSurfaceContainerEscuro,
    onSurfaceVariant = SigbefMutedClaro,
    outline = SigbefLineEscuro,
    error = SigbefErrorClaro,
    onError = SigbefNavyEscuro,
    errorContainer = SigbefErrorFundoEscuro,
    onErrorContainer = SigbefErrorClaro,
    surfaceContainerLowest = SigbefBackgroundEscuro,
    surfaceContainerLow = SigbefSurfaceEscuro,
    surfaceContainer = SigbefSurfaceEscuro,
    surfaceContainerHigh = SigbefSurfaceContainerEscuro,
    surfaceContainerHighest = SigbefSurfaceContainerEscuro,
    inverseSurface = SigbefInkClaro,
    inverseOnSurface = SigbefBackgroundEscuro,
  )

/**
 * As cores do SIGBEF, resolvidas para o tema em vigor.
 *
 * O `ColorScheme` do Material cobre primária, superfície e erro — e
 * para nada mais tem lugar. Metade do vocabulário desta interface fica
 * de fora dele: o dourado da marca, o fundo lavado de cada pílula de
 * situação, a tinta escura que vai por cima do fundo de aviso. Sem um
 * lugar para essas cores, as telas importavam `SigbefNavy` e
 * `SigbefMuted` direto do arquivo de paleta — que são os valores do
 * tema **claro**. Era por isso que o tema escuro não podia funcionar
 * nem depois de existir: ele trocaria o `ColorScheme` e as telas
 * continuariam pintando com os valores claros na mão.
 *
 * Os nomes são de papel, não de cor: `secundario`, e não "cinza";
 * `avisoFundo`, e não "laranja lavado". É o que permite que o escuro
 * use outro valor sem que a tela precise saber.
 */
@Immutable
data class CoresSigbef(
  /**
   * A marca como **frente**: texto, ícone, contorno sobre uma
   * superfície clara.
   *
   * No escuro isto vira o azul claro. Tem que virar: navy sobre fundo
   * quase preto é um texto que ninguém lê.
   */
  val navy: Color,
  /**
   * A marca como **fundo**: botão principal, cabeçalho do cartão,
   * medalhão do logo — os blocos que levam conteúdo branco por cima.
   *
   * Fica navy nos dois temas, ao contrário de `navy`. É a separação que
   * faltava: com um token só, o modo escuro clareava a cor e o bloco
   * virava azul claro com texto branco em cima, ilegível. Sempre que
   * usar `marca` como fundo, use `sobreMarca` no que vai por cima.
   */
  val marca: Color,
  /** Apoio do navy: link, ícone selecionado, gráfico. */
  val azul: Color,
  /** A única faísca. Nunca em bloco grande. */
  val dourado: Color,
  /** Fundo da tela. */
  val fundo: Color,
  /** Cartão, campo, folha. */
  val superficie: Color,
  /** Superfície um degrau acima: cabeçalho de lista, célula alternada. */
  val superficieAlta: Color,
  /** Divisória e contorno. */
  val linha: Color,
  /** Texto principal. */
  val tinta: Color,
  /** Texto de apoio. Mede AA sobre `superficie` nos dois temas. */
  val secundario: Color,
  val sucesso: Color,
  val aviso: Color,
  val erro: Color,
  val sucessoFundo: Color,
  val avisoFundo: Color,
  val erroFundo: Color,
  val azulFundo: Color,
  /** Texto sobre `avisoFundo`. */
  val avisoTinta: Color,
  /**
   * Texto e ícone sobre a barra da marca.
   *
   * Branco nos dois temas, e de propósito: a barra superior continua
   * navy no escuro. Ela já é escura, e é o que faz o app ser
   * reconhecido como o sistema da escola — apagá-la no modo escuro
   * seria trocar a identidade por uma economia de brilho que o navy
   * não custa.
   */
  val sobreMarca: Color,
)

private val CoresClaras =
  CoresSigbef(
    navy = SigbefNavy,
    marca = SigbefNavy,
    azul = SigbefBlue,
    dourado = SigbefGold,
    fundo = SigbefBackground,
    superficie = SigbefSurface,
    superficieAlta = SigbefSurfaceContainerLow,
    linha = SigbefLine,
    tinta = SigbefInk,
    secundario = SigbefMuted,
    sucesso = SigbefSuccess,
    aviso = SigbefWarning,
    erro = SigbefError,
    sucessoFundo = SigbefSuccessFundo,
    avisoFundo = SigbefWarningFundo,
    erroFundo = SigbefErrorFundo,
    azulFundo = SigbefBlueFundo,
    avisoTinta = SigbefWarningInk,
    sobreMarca = Color.White,
  )

private val CoresEscuras =
  CoresSigbef(
    // No escuro o navy não serve de cor de texto nem de botão: some no
    // fundo. Quem faz esse papel é o azul claro. O navy continua vivo
    // como superfície da barra da marca, via `MaterialTheme`.
    navy = SigbefBlueClaro,
    marca = SigbefNavy,
    azul = SigbefBlueClaro,
    dourado = SigbefGoldEscuro,
    fundo = SigbefBackgroundEscuro,
    superficie = SigbefSurfaceEscuro,
    superficieAlta = SigbefSurfaceContainerEscuro,
    linha = SigbefLineEscuro,
    tinta = SigbefInkClaro,
    secundario = SigbefMutedClaro,
    sucesso = SigbefSuccessClaro,
    aviso = SigbefWarningClaro,
    erro = SigbefErrorClaro,
    sucessoFundo = SigbefSuccessFundoEscuro,
    avisoFundo = SigbefWarningFundoEscuro,
    erroFundo = SigbefErrorFundoEscuro,
    azulFundo = SigbefBlueFundoEscuro,
    avisoTinta = SigbefWarningInkClaro,
    sobreMarca = Color.White,
  )

private val LocalCoresSigbef = staticCompositionLocalOf { CoresClaras }

/**
 * Ponto de acesso às cores: `SigbefCores.atual.secundario`.
 *
 * Uma tela nunca deve importar `SigbefNavy` e companhia direto — esses
 * são os valores do tema claro. É a diferença entre "pinte de navy" e
 * "pinte com a cor da marca", e só a segunda sobrevive ao modo escuro.
 */
object SigbefCores {
  val atual: CoresSigbef
    @Composable @ReadOnlyComposable get() = LocalCoresSigbef.current
}

/**
 * @param darkTheme segue o aparelho por padrão.
 * @param dynamicColor **ignorado de propósito.** O Material 12+ sabe
 *   tirar uma paleta do papel de parede; o SIGBEF não usa. A marca da
 *   escola é a mesma no desktop, no site e aqui, e um app que muda de
 *   cor conforme a foto de fundo de cada aluno deixa de ser reconhecível
 *   como o sistema da biblioteca. O parâmetro fica na assinatura porque
 *   as telas de *preview* o passam; o que ele não faz mais é ser
 *   calculado e jogado fora.
 */
@Composable
fun MyApplicationTheme(
  darkTheme: Boolean = isSystemInDarkTheme(),
  @Suppress("UNUSED_PARAMETER") dynamicColor: Boolean = false,
  content: @Composable () -> Unit,
) {
  val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
  val cores = if (darkTheme) CoresEscuras else CoresClaras
  CompositionLocalProvider(LocalCoresSigbef provides cores) {
    MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
  }
}

/**
 * As cores que **não** mudam com o tema.
 *
 * Código de barras e QR code precisam de preto sobre branco de verdade:
 * é assim que o leitor do balcão enxerga. Pintá-los com a superfície do
 * tema deixaria o cartão digital do aluno bonito no escuro e ilegível
 * pela máquina — que é a única coisa que ele precisa fazer.
 *
 * Também vale para a câmera: o visor do leitor de QR é uma imagem de
 * vídeo, e a moldura desenhada por cima dela é branca sempre, porque o
 * fundo ali é o mundo, não o tema.
 */
object SigbefFixo {
  val PapelBranco = Color.White
  val TintaPreta = Color.Black
  val SobreCamera = Color.White
}
