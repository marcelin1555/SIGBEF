package br.rn.cefe.sigbef.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Código de barras **Code 128B real**, escaneável por qualquer leitor.
 *
 * A versão anterior desenhava barras pseudo-aleatórias derivadas do hash
 * do texto ("deterministic pseudo-barcode"): parecia um código de barras,
 * mas nenhum leitor conseguia ler. Como o cartão diz "apresente este
 * código no balcão", isso deixava o aluno na mão.
 *
 * A tabela e o algoritmo são os mesmos do desktop (sigbef/barcode_util.py),
 * para que o leitor da biblioteca leia o cartão do celular exatamente
 * como lê o cartão impresso.
 */
private object Code128 {

    /** Larguras dos 107 símbolos do padrão, alternando barra/espaço. */
    private val SIMBOLOS = arrayOf(
        "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312",
        "132212", "221213", "221312", "231212", "112232", "122132", "122231", "113222",
        "123122", "123221", "223211", "221132", "221231", "213212", "223112", "312131",
        "311222", "321122", "321221", "312212", "322112", "322211", "212123", "212321",
        "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
        "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121",
        "313121", "211331", "231131", "213113", "213311", "213131", "311123", "311321",
        "331121", "312113", "312311", "332111", "314111", "221411", "431111", "111224",
        "111422", "121124", "121421", "141122", "141221", "112214", "112412", "122114",
        "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
        "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112",
        "421211", "212141", "214121", "412121", "111143", "111341", "131141", "114113",
        "114311", "411113", "411311", "113141", "114131", "311141", "411131", "211412",
        "211214", "211232", "2331112"
    )

    private const val START_B = 104
    private const val STOP = 106

    /** start + dados + dígito verificador + stop. */
    private fun valores(texto: String): List<Int> {
        val v = mutableListOf(START_B)
        for (ch in texto) {
            val o = ch.code
            v.add(if (o in 32..126) o - 32 else 0)
        }
        var soma = v[0]
        for (i in 1 until v.size) {
            soma += v[i] * i
        }
        v.add(soma % 103)
        v.add(STOP)
        return v
    }

    /** Pares (largura em módulos, é barra escura). */
    fun barras(texto: String): List<Pair<Int, Boolean>> {
        val saida = mutableListOf<Pair<Int, Boolean>>()
        for (valor in valores(texto)) {
            var escura = true
            for (d in SIMBOLOS[valor]) {
                saida.add(Pair(d - '0', escura))
                escura = !escura
            }
        }
        return saida
    }
}

@Composable
fun BarcodeView(
    code: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(Color.White)
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
                            color = Color.Black,
                            topLeft = Offset(x, 0f),
                            size = Size(w, size.height)
                        )
                    }
                    x += w
                }
            }

            Text(
                text = code,
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 2.sp,
                color = Color.Black,
                textAlign = TextAlign.Center,
                modifier = Modifier.padding(top = 8.dp)
            )
        } else {
            Text(
                text = "Entre na sua conta para ver o código do seu cartão.",
                fontSize = 13.sp,
                color = Color.Gray,
                textAlign = TextAlign.Center
            )
        }
    }
}
