package br.rn.cefe.sigbef.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoStories
import androidx.compose.material.icons.filled.Category
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.EstatisticaLeitura
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Recomendacao
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.components.RotuloSecao
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.components.dataParaLer
import br.rn.cefe.sigbef.ui.theme.SigbefCores

/**
 * "Minha leitura": o que o aluno já leu e o que a biblioteca sugere.
 *
 * Sem pontuação, medalha ou ranking entre alunos. Quantidade de livros
 * lidos não é competição — transformar isso em placar constrangeria
 * quem lê devagar, que é justamente quem a biblioteca escolar mais
 * precisa aproximar.
 */
@Composable
fun ReadingScreen(
    estatistica: EstatisticaLeitura,
    recomendacoes: List<Recomendacao>,
    isOffline: Boolean,
    onNavigate: (Screen) -> Unit,
    ultimaSincronizacao: String? = null,
    onAbrirLivro: (Int) -> Unit = {},
    onAtualizar: (() -> Unit)? = null,
    carregando: Boolean = false
) {
    Scaffold(
        topBar = {
            SigbefTopAppBar(
                title = "Minha leitura",
                subtitle = "O que você já leu e o que vem depois",
                isOffline = isOffline,
                ultimaSincronizacao = ultimaSincronizacao,
                onAtualizar = onAtualizar,
                carregando = carregando
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.READING,
                onNavigate = onNavigate
            )
        },
        containerColor = SigbefCores.atual.fundo
    ) { innerPadding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item { Spacer(modifier = Modifier.height(4.dp)) }

            if (estatistica.vazia) {
                item { ConviteParaComecar() }
            } else {
                item { ResumoDaLeitura(estatistica) }
            }

            if (recomendacoes.isNotEmpty()) {
                item {
                    RotuloSecao(
                        texto = if (estatistica.vazia) "Para começar"
                                else "Talvez você goste",
                        modifier = Modifier.padding(top = 8.dp)
                    )
                }
                items(recomendacoes, key = { it.livroId }) { r ->
                    CartaoRecomendacao(r, onAbrirLivro)
                }
            } else if (isOffline) {
                item { AvisoSemRede() }
            }

            item { Spacer(modifier = Modifier.height(8.dp)) }
        }
    }
}

/** Quem ainda não devolveu nada vê convite, não números zerados. */
@Composable
private fun ConviteParaComecar() {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = SigbefCores.atual.superficie,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Box(
                modifier = Modifier
                    .size(72.dp)
                    .clip(CircleShape)
                    .background(SigbefCores.atual.azulFundo),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.AutoStories,
                    contentDescription = null,
                    tint = SigbefCores.atual.navy,
                    modifier = Modifier.size(36.dp)
                )
            }
            Spacer(modifier = Modifier.height(14.dp))
            Text(
                text = "Sua estante começa no primeiro livro",
                style = MaterialTheme.typography.titleLarge,
                color = SigbefCores.atual.navy,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "Quando você devolver um livro, ele aparece aqui — " +
                    "com o tempo, esta tela vira o retrato do que você leu.",
                style = MaterialTheme.typography.bodyMedium,
                color = SigbefCores.atual.secundario,
                textAlign = TextAlign.Center,
                lineHeight = 20.sp
            )
        }
    }
}

@Composable
private fun ResumoDaLeitura(e: EstatisticaLeitura) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = SigbefCores.atual.superficie,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            // Faixa dourada: a assinatura da marca, igual à do cartão.
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp)
                    .background(SigbefCores.atual.dourado)
            )
            Column(modifier = Modifier.padding(20.dp)) {
                Row(verticalAlignment = Alignment.Bottom) {
                    Text(
                        text = "${e.totalLidos}",
                        style = MaterialTheme.typography.displayLarge,
                        color = SigbefCores.atual.navy
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = if (e.totalLidos == 1) "livro lido"
                               else "livros lidos",
                        style = MaterialTheme.typography.bodyLarge,
                        color = SigbefCores.atual.secundario,
                        modifier = Modifier.padding(bottom = 7.dp)
                    )
                }

                if (e.lidosNoAno > 0) {
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "${e.lidosNoAno} " +
                            (if (e.lidosNoAno == 1) "foi" else "foram") +
                            " este ano",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SigbefCores.atual.secundario
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                if (e.categoriaFavorita.isNotBlank()) {
                    LinhaDetalhe(
                        icone = Icons.Default.Category,
                        texto = "Você lê mais ${e.categoriaFavorita}",
                        apoio = "${e.lidosNaFavorita} " +
                            (if (e.lidosNaFavorita == 1) "livro" else "livros")
                    )
                }
                if (e.diasMedios > 0) {
                    Spacer(modifier = Modifier.height(8.dp))
                    LinhaDetalhe(
                        icone = Icons.Default.Schedule,
                        texto = "Fica em média ${formatarDias(e.diasMedios)} " +
                            "com cada livro"
                    )
                }
                if (e.leitorDesde.isNotBlank()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    LinhaDetalhe(
                        icone = Icons.Default.AutoStories,
                        texto = "Leitor desde ${dataParaLer(e.leitorDesde)}"
                    )
                }
            }
        }
    }
}

@Composable
private fun LinhaDetalhe(icone: ImageVector, texto: String,
                          apoio: String = "") {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            imageVector = icone,
            contentDescription = null,
            tint = SigbefCores.atual.navy,
            modifier = Modifier.size(18.dp)
        )
        Spacer(modifier = Modifier.width(10.dp))
        Text(text = texto, style = MaterialTheme.typography.bodyMedium,
             color = SigbefCores.atual.tinta)
        if (apoio.isNotBlank()) {
            Spacer(modifier = Modifier.width(6.dp))
            Text(text = "· $apoio", style = MaterialTheme.typography.bodyMedium,
                 color = SigbefCores.atual.secundario)
        }
    }
}

/** "6,4 dias" fica pedante; "6 dias" basta. */
private fun formatarDias(dias: Double): String {
    val arredondado = kotlin.math.round(dias).toInt()
    return when {
        arredondado <= 0 -> "menos de um dia"
        arredondado == 1 -> "1 dia"
        else -> "$arredondado dias"
    }
}

@Composable
private fun CartaoRecomendacao(r: Recomendacao, onAbrir: (Int) -> Unit) {
    val corLombada = try {
        Color(android.graphics.Color.parseColor(r.spineColorHex))
    } catch (e: Exception) {
        SigbefCores.atual.navy
    }

    Surface(
        modifier = Modifier.fillMaxWidth().clickable { onAbrir(r.livroId) },
        shape = RoundedCornerShape(12.dp),
        color = SigbefCores.atual.superficie,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .width(40.dp)
                    .height(58.dp)
                    .clip(RoundedCornerShape(5.dp))
                    .background(corLombada)
            )
            Spacer(modifier = Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = r.titulo,
                    style = MaterialTheme.typography.titleMedium,
                    color = SigbefCores.atual.tinta,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                if (r.motivo.isNotBlank()) {
                    Spacer(modifier = Modifier.height(3.dp))
                    // O porquê da sugestão. Sem ele, a lista parece anúncio.
                    Text(
                        text = r.motivo,
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario,
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
        }
    }
}

@Composable
private fun AvisoSemRede() {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = SigbefCores.atual.azulFundo
    ) {
        Text(
            text = "As sugestões chegam quando você estiver no Wi-Fi da " +
                "escola.",
            style = MaterialTheme.typography.bodySmall,
            color = SigbefCores.atual.navy,
            modifier = Modifier.padding(16.dp)
        )
    }
}
