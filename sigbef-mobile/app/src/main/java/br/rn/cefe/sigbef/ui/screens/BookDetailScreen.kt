package br.rn.cefe.sigbef.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.requiredWidth
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CalendarToday
import androidx.compose.material.icons.filled.Category
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Tag
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Livro
import br.rn.cefe.sigbef.model.Reserva
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.components.PilulaStatus
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefBackground
import br.rn.cefe.sigbef.ui.theme.SigbefGold
import br.rn.cefe.sigbef.ui.theme.SigbefInk
import br.rn.cefe.sigbef.ui.theme.SigbefLine
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefSuccess
import br.rn.cefe.sigbef.ui.theme.SigbefSuccessFundo
import br.rn.cefe.sigbef.ui.theme.SigbefWarningFundo
import br.rn.cefe.sigbef.ui.theme.SigbefWarningInk

@Composable
fun BookDetailScreen(
    livro: Livro,
    isOffline: Boolean,
    onBackClick: () -> Unit,
    onNavigate: (Screen) -> Unit,
    /** Reserva ativa do aluno para ESTE livro, se já existir. */
    reservaDoLivro: Reserva? = null,
    acaoEmCurso: Boolean = false,
    onReservar: () -> Unit = {},
    onCancelarReserva: () -> Unit = {}
) {
    val spineColor = try {
        Color(android.graphics.Color.parseColor(livro.spineColorHex))
    } catch (e: Exception) {
        SigbefNavy
    }

    Scaffold(
        topBar = {
            SigbefTopAppBar(
                title = "Detalhes do livro",
                showBack = true,
                onBackClick = onBackClick,
                isOffline = isOffline
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.BOOK_DETAIL,
                onNavigate = onNavigate,
                isOffline = isOffline
            )
        },
        containerColor = SigbefBackground
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 20.dp, vertical = 16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Book Spine Art
                Box(
                    modifier = Modifier
                        .width(80.dp)
                        .height(200.dp)
                        .clip(RoundedCornerShape(4.dp))
                        .background(spineColor)
                        .border(1.dp, Color.Black.copy(alpha = 0.1f), RoundedCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Box(
                        modifier = Modifier
                            .requiredWidth(180.dp)
                            .rotate(-90f),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = livro.titulo.uppercase(),
                            fontSize = 15.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = Color.White,
                            letterSpacing = 2.sp,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Status do exemplar, como veio da biblioteca. Antes o
                // livro emprestado também aparecia em verde e com ícone
                // de confirmação — o desenho dizia o contrário do texto.
                if (livro.disponivel) {
                    PilulaStatus(
                        texto = "Disponível",
                        cor = SigbefSuccess,
                        fundo = SigbefSuccessFundo,
                        icone = Icons.Default.CheckCircle
                    )
                } else {
                    PilulaStatus(
                        texto = "Emprestado",
                        cor = SigbefWarningInk,
                        fundo = SigbefWarningFundo,
                        icone = Icons.Default.Schedule
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Title & Author
                Text(
                    text = livro.titulo,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = SigbefInk,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = livro.autor,
                    fontSize = 16.sp,
                    color = SigbefMuted,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(24.dp))

                // Bento Grid Details (2x2)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    DetailCard(
                        icon = Icons.Default.Category,
                        label = "CATEGORIA",
                        value = livro.categoria,
                        modifier = Modifier.weight(1f)
                    )
                    DetailCard(
                        icon = Icons.Default.CalendarToday,
                        label = "ANO",
                        value = livro.ano,
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    DetailCard(
                        icon = Icons.Default.Tag,
                        label = "TOMBO",
                        value = livro.tombo,
                        modifier = Modifier.weight(1f)
                    )
                    DetailCard(
                        icon = Icons.Default.QrCode,
                        label = "ISBN",
                        value = livro.isbn,
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(24.dp))

                // Synopsis Card
                Column(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.MenuBook,
                            contentDescription = null,
                            tint = SigbefNavy,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Sinopse",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                            color = SigbefInk
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        color = Color.White,
                        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
                    ) {
                        Text(
                            text = livro.sinopse,
                            fontSize = 14.sp,
                            color = SigbefInk,
                            lineHeight = 22.sp,
                            modifier = Modifier.padding(16.dp)
                        )
                    }
                }
            }

            // Fixed Action Bottom Bar
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = Color.White,
                shadowElevation = 8.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    when {
                        // Emprestar continua sendo de balcão: exige o livro
                        // na mão, e a API não faz isso de propósito.
                        livro.disponivel -> Aviso(
                            "Anote o tombo e procure o balcão para levar " +
                                "este livro."
                        )

                        reservaDoLivro != null -> {
                            Aviso(
                                if (reservaDoLivro.separado)
                                    "Seu exemplar está separado no balcão" +
                                        (reservaDoLivro.retirarAte?.let {
                                            ", retire até $it."
                                        } ?: ".")
                                else
                                    "Você é o ${reservaDoLivro.posicao}º da " +
                                        "fila deste livro."
                            )
                            OutlinedButton(
                                onClick = onCancelarReserva,
                                enabled = !isOffline && !acaoEmCurso,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("Sair da fila")
                            }
                        }

                        else -> {
                            Aviso("Este livro está emprestado. Você pode " +
                                      "entrar na fila e a biblioteca avisa " +
                                      "quando chegar a sua vez.")
                            Button(
                                onClick = onReservar,
                                enabled = !isOffline && !acaoEmCurso,
                                modifier = Modifier.fillMaxWidth(),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = SigbefNavy
                                )
                            ) {
                                Text(
                                    if (isOffline) "Sem conexão para reservar"
                                    else "Entrar na fila de espera"
                                )
                            }
                        }
                    }
                }
            }
        }
    }

}

/** Faixa de orientação em azul claro, acima do botão de ação. */
@Composable
private fun Aviso(texto: String) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = SigbefNavy.copy(alpha = 0.06f)
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.Info,
                contentDescription = null,
                tint = SigbefNavy,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.width(10.dp))
            Text(text = texto, fontSize = 13.sp, color = SigbefNavy)
        }
    }
}

@Composable
private fun DetailCard(
    icon: ImageVector,
    label: String,
    value: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        color = Color.White,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
    ) {
        Column(
            modifier = Modifier.padding(12.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = SigbefMuted,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = label,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = SigbefMuted,
                    letterSpacing = 1.sp
                )
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = SigbefInk
            )
        }
    }
}
