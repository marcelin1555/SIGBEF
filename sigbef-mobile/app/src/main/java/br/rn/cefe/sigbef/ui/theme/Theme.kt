package br.rn.cefe.sigbef.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColorScheme =
  lightColorScheme(
    primary = SigbefNavy,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD1E4FF),
    onPrimaryContainer = Color(0xFF001D35),
    secondary = SigbefBlue,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFF7CBAFF),
    onSecondaryContainer = Color(0xFF004A7D),
    tertiary = SigbefGold,
    onTertiary = SigbefNavy,
    background = SigbefBackground,
    onBackground = SigbefInk,
    surface = SigbefSurface,
    onSurface = SigbefInk,
    surfaceVariant = SigbefSurfaceContainerLow,
    onSurfaceVariant = SigbefMuted,
    outline = SigbefLine,
    error = SigbefError
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
