package br.rn.cefe.sigbef.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
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
    inverseOnSurface = Color.White
  )

@Composable
fun MyApplicationTheme(
  darkTheme: Boolean = isSystemInDarkTheme(),
  dynamicColor: Boolean = false,
  content: @Composable () -> Unit,
) {
  val colorScheme = LightColorScheme
  MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
}
