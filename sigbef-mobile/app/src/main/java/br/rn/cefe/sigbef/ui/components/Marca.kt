package br.rn.cefe.sigbef.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.ui.theme.SigbefBlue
import br.rn.cefe.sigbef.ui.theme.SigbefGold
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy

/**
 * Elementos que dão ao app a mesma cara do site.
 *
 * São dois, e existem porque o site os repete: o cabeçalho em gradiente
 * fechado por uma faixa dourada, e a pílula de status arredondada. Ver
 * `docs/DESIGN.md` e `site/src/components/Hero.jsx`.
 */

/** O gradiente do topo do site (`from-[#1F4E79] to-[#2E75B6]`). */
val GradienteMarca = Brush.linearGradient(listOf(SigbefNavy, SigbefBlue))

/**
 * Data para ler, a partir do ISO que a biblioteca devolve.
 *
 * O servidor fala `2026-08-02` porque é o formato do SQLite e ordena
 * sozinho; ninguém no Brasil lê uma data assim. A conversão é textual de
 * propósito — `java.time` exigiria desugaring no minSdk 24.
 *
 * Devolve a entrada intacta se ela não estiver no formato esperado, para
 * nunca esconder do aluno um dado que existe.
 */
fun dataParaLer(iso: String?): String {
    val texto = iso?.take(10).orEmpty()
    val partes = texto.split("-")
    if (partes.size != 3 || partes.any { it.isEmpty() }) return iso.orEmpty()
    val (ano, mes, dia) = partes
    if (ano.length != 4 || mes.length != 2 || dia.length != 2) return iso.orEmpty()
    if (!texto.replace("-", "").all { it.isDigit() }) return iso.orEmpty()
    return "$dia/$mes/$ano"
}

/**
 * Cabeçalho de tela: gradiente da marca fechado pela faixa dourada.
 *
 * A faixa é o único dourado da tela — é assim que o guia manda usá-lo,
 * como faísca e nunca como bloco. Por isso ela tem 4dp e não uma barra
 * inteira.
 *
 * @param conteudo o que aparece sobre o gradiente. Fica em branco, então
 *        quem escreve aqui não precisa repetir `color = Color.White` a
 *        cada texto — o padrão já é esse.
 */
@Composable
fun CabecalhoMarca(
    modifier: Modifier = Modifier,
    conteudo: @Composable ColumnScope.() -> Unit
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(GradienteMarca)
                .padding(horizontal = 20.dp, vertical = 20.dp),
            content = conteudo
        )
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .background(SigbefGold)
        )
    }
}

/**
 * Título e subtítulo dentro de um [CabecalhoMarca]. Só para as telas não
 * repetirem os mesmos tamanhos e pesos.
 */
@Composable
fun TituloNoCabecalho(titulo: String, subtitulo: String? = null) {
    Text(
        text = titulo,
        fontSize = 24.sp,
        fontWeight = FontWeight.Bold,
        color = Color.White
    )
    if (!subtitulo.isNullOrBlank()) {
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = subtitulo,
            fontSize = 14.sp,
            color = Color.White.copy(alpha = 0.85f)
        )
    }
}

/**
 * Pílula de status, igual à do site ("✓ ok" / "atrasado").
 *
 * Nunca depende só da cor: sempre tem texto, e ícone quando cabe. Quem
 * não distingue verde de vermelho continua lendo o estado.
 */
@Composable
fun PilulaStatus(
    texto: String,
    cor: Color,
    fundo: Color,
    icone: ImageVector? = null,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(50))
            .background(fundo)
            .padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {
        if (icone != null) {
            Icon(
                imageVector = icone,
                contentDescription = null,
                tint = cor,
                modifier = Modifier.size(13.dp)
            )
            Spacer(modifier = Modifier.width(5.dp))
        }
        Text(
            text = texto,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = cor
        )
    }
}

/**
 * Rótulo em caixa alta espaçada, usado como divisória de seção.
 * O guia chama de "rótulos em caixa alta com tracking-widest".
 */
@Composable
fun RotuloSecao(texto: String, modifier: Modifier = Modifier) {
    Text(
        text = texto.uppercase(),
        fontSize = 12.sp,
        fontWeight = FontWeight.Bold,
        color = SigbefMuted,
        letterSpacing = 1.5.sp,
        modifier = modifier
    )
}
