package br.rn.cefe.sigbef.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.ui.theme.SigbefFixo
import br.rn.cefe.sigbef.ui.theme.SigbefMuted

@Composable
fun BarcodeView(
    code: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(SigbefFixo.PapelBranco)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        if (code.isNotBlank()) {
            val barras = Code128.barras(code)
            val totalModulos = barras.sumOf { it.first }

            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(80.dp)
            ) {
                // Zona de silêncio nas pontas: sem ela o leitor não engata.
                val silencio = 10
                val unidade = size.width / (totalModulos + silencio * 2)
                var x = unidade * silencio
                for ((largura, escura) in barras) {
                    val w = unidade * largura
                    if (escura) {
                        drawRect(
                            color = SigbefFixo.TintaPreta,
                            topLeft = Offset(x, 0f),
                            size = Size(w, size.height)
                        )
                    }
                    x += w
                }
            }

            Text(
                text = code,
                style = MaterialTheme.typography.titleSmall,
                letterSpacing = 2.sp,
                color = SigbefFixo.TintaPreta,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 8.dp)
            )
        } else {
            Text(
                text = "Entre na sua conta para ver o código do seu cartão.",
                style = MaterialTheme.typography.bodySmall,
                color = SigbefMuted,
                textAlign = TextAlign.Center
            )
        }
    }
}
