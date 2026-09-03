package br.rn.cefe.sigbef.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material.icons.filled.ImportContacts
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Emprestimo
import br.rn.cefe.sigbef.model.Reserva
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.components.PilulaStatus
import br.rn.cefe.sigbef.ui.components.dataParaLer
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.PesoRegular
import br.rn.cefe.sigbef.ui.theme.PesoSemibold
import br.rn.cefe.sigbef.ui.theme.SigbefCores

@Composable
fun LoansScreen(
    emprestimos: List<Emprestimo>,
    isOffline: Boolean,
    ultimaSincronizacao: String? = null,
    onNavigate: (Screen) -> Unit,
    reservas: List<Reserva> = emptyList(),
    acaoEmCurso: Boolean = false,
    onRenovar: (Emprestimo) -> Unit = {},
    onCancelarReserva: (Reserva) -> Unit = {},
    /** Buscar dados novos na biblioteca. */
    onAtualizar: (() -> Unit)? = null,
    carregando: Boolean = false
) {
    val ativos = emprestimos.filter { !it.devolvido }
    val historico = emprestimos.filter { it.devolvido }

    Scaffold(
        topBar = {
            SigbefTopAppBar(
                title = "Meus empréstimos",
                subtitle = "Acompanhe seus livros e a fila de espera",
                isOffline = isOffline,
                ultimaSincronizacao = ultimaSincronizacao,
                onAtualizar = onAtualizar,
                carregando = carregando
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.LOANS,
                onNavigate = onNavigate
            )
        },
        containerColor = SigbefCores.atual.fundo
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp, vertical = 16.dp)
        ) {
            TextButton(
                onClick = { onNavigate(Screen.RENEW_INFO) },
                modifier = Modifier.padding(0.dp)
            ) {
                Text(
                    text = "Como renovar",
                    style = MaterialTheme.typography.titleSmall,
                    color = SigbefCores.atual.azul,
                    textDecoration = TextDecoration.Underline
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // O estado vazio é para quem nunca pegou um livro. Quem tem
            // fila de espera, ou já devolveu alguma coisa, tem o que ver
            // aqui — e leria "você ainda não pegou nenhum livro" sobre a
            // própria estante de leituras, o que é falso.
            if (ativos.isEmpty() && reservas.isEmpty() && historico.isEmpty()) {
                // Empty Loans State
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Box(
                        modifier = Modifier
                            .size(140.dp)
                            .clip(CircleShape)
                            .background(SigbefCores.atual.azulFundo),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.ImportContacts,
                            contentDescription = null,
                            tint = SigbefCores.atual.navy,
                            modifier = Modifier.size(64.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    Text(
                        text = "Você ainda não pegou nenhum livro",
                        style = MaterialTheme.typography.headlineSmall,
                        color = SigbefCores.atual.navy,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Quando pegar um livro emprestado no balcão, ele aparece aqui com o prazo de devolução.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SigbefCores.atual.secundario,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 24.dp)
                    )

                    Spacer(modifier = Modifier.height(28.dp))

                    Button(
                        onClick = { onNavigate(Screen.ACERVO) },
                        colors = ButtonDefaults.buttonColors(containerColor = SigbefCores.atual.dourado),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                    ) {
                        Text(
                            text = "EXPLORAR O ACERVO",
                            style = MaterialTheme.typography.titleSmall,
                            color = SigbefCores.atual.navy,
                            letterSpacing = 1.sp
                        )
                    }
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    if (ativos.isNotEmpty()) {
                        item {
                            Text(
                                text = "COM VOCÊ AGORA (${ativos.size})",
                                style = MaterialTheme.typography.labelMedium,
                                color = SigbefCores.atual.secundario,
                                letterSpacing = 1.5.sp
                            )
                        }

                        items(ativos) { emp ->
                            ActiveLoanCard(
                                emp = emp,
                                isOffline = isOffline,
                                acaoEmCurso = acaoEmCurso,
                                onRenovar = onRenovar
                            )
                        }
                    }

                    if (reservas.isNotEmpty()) {
                        item {
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                text = "NA FILA DE ESPERA (${reservas.size})",
                                style = MaterialTheme.typography.labelMedium,
                                color = SigbefCores.atual.secundario,
                                letterSpacing = 1.5.sp
                            )
                        }

                        items(reservas) { reserva ->
                            ReservaCard(
                                reserva = reserva,
                                isOffline = isOffline,
                                acaoEmCurso = acaoEmCurso,
                                onCancelar = onCancelarReserva
                            )
                        }
                    }

                    if (historico.isNotEmpty()) {
                        item {
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                text = "HISTÓRICO RECENTE",
                                style = MaterialTheme.typography.labelMedium,
                                color = SigbefCores.atual.secundario,
                                letterSpacing = 1.5.sp
                            )
                        }

                        items(historico) { emp ->
                            HistoryLoanCard(emp = emp)
                        }

                        // Havia aqui um "Ver todo o histórico" que não
                        // fazia nada — onClick vazio. O que a biblioteca
                        // manda já são os mais recentes, e é o histórico
                        // inteiro para quase todo aluno; um botão que
                        // promete mais e não entrega é pior que nenhum.
                    }
                }
            }
        }
    }
}

@Composable
private fun ActiveLoanCard(
    emp: Emprestimo,
    isOffline: Boolean,
    acaoEmCurso: Boolean,
    onRenovar: (Emprestimo) -> Unit
) {
    val spineColor = try {
        Color(android.graphics.Color.parseColor(emp.spineColorHex))
    } catch (e: Exception) {
        SigbefCores.atual.navy
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = SigbefCores.atual.superficie,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(
            width = if (emp.atrasado) 1.5.dp else 1.dp,
            color = if (emp.atrasado) SigbefCores.atual.erro else SigbefCores.atual.linha
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .width(48.dp)
                        .height(72.dp)
                        .clip(RoundedCornerShape(6.dp))
                        .background(spineColor)
                )

                Spacer(modifier = Modifier.width(16.dp))

                Column(
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        text = emp.livroTitulo,
                        style = MaterialTheme.typography.titleMedium,
                        color = SigbefCores.atual.tinta
                    )

                    Spacer(modifier = Modifier.height(2.dp))

                    Text(
                        text = "Devolução em ${dataParaLer(emp.dataDevolucao)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario,
                        textDecoration = if (emp.atrasado) TextDecoration.LineThrough else TextDecoration.None
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    if (emp.atrasado) {
                        PilulaStatus(
                            texto = "Atrasado",
                            cor = SigbefCores.atual.erro,
                            fundo = SigbefCores.atual.erroFundo,
                            icone = Icons.Default.Error
                        )
                    } else {
                        PilulaStatus(
                            texto = "Em dia",
                            cor = SigbefCores.atual.sucesso,
                            fundo = SigbefCores.atual.sucessoFundo,
                            icone = Icons.Default.CheckCircle
                        )
                    }
                }
            }

            // O veredito sobre renovar vem pronto da biblioteca, com a
            // frase que explica a recusa. O app não recalcula a regra.
            if (!emp.devolvido) {
                Spacer(modifier = Modifier.height(12.dp))
                androidx.compose.material3.HorizontalDivider(color = SigbefCores.atual.linha)
                Spacer(modifier = Modifier.height(8.dp))

                when {
                    emp.podeRenovar && !isOffline -> Button(
                        onClick = { onRenovar(emp) },
                        enabled = !acaoEmCurso,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SigbefCores.atual.marca,
                            contentColor = SigbefCores.atual.sobreMarca,
                        )
                    ) {
                        Text("Renovar empréstimo", style = MaterialTheme.typography.labelLarge)
                    }

                    emp.podeRenovar -> Text(
                        text = "Conecte-se ao Wi-Fi da escola para renovar.",
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario
                    )

                    else -> Text(
                        text = emp.motivoRenovacao.ifBlank {
                            "Para renovar, leve o livro ao balcão da " +
                                "biblioteca."
                        },
                        style = MaterialTheme.typography.bodySmall,
                        color = if (emp.atrasado) SigbefCores.atual.erro else SigbefCores.atual.secundario
                    )
                }
            }
        }
    }
}

/**
 * Um livro em que o aluno está na fila.
 *
 * Quando o exemplar já foi separado, o prazo de retirada é a informação
 * mais importante do cartão — passar dele devolve o livro para a fila.
 */
@Composable
private fun ReservaCard(
    reserva: Reserva,
    isOffline: Boolean,
    acaoEmCurso: Boolean,
    onCancelar: (Reserva) -> Unit
) {
    val spineColor = try {
        Color(android.graphics.Color.parseColor(reserva.spineColorHex))
    } catch (e: Exception) {
        SigbefCores.atual.navy
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = SigbefCores.atual.superficie,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(
            width = if (reserva.separado) 1.5.dp else 1.dp,
            color = if (reserva.separado) SigbefCores.atual.dourado else SigbefCores.atual.linha
        )
    ) {
        Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .width(48.dp)
                        .height(72.dp)
                        .clip(RoundedCornerShape(6.dp))
                        .background(spineColor)
                )

                Spacer(modifier = Modifier.width(16.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = reserva.titulo,
                        style = MaterialTheme.typography.titleMedium,
                        color = SigbefCores.atual.tinta
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = if (reserva.separado)
                            "Separado para você" +
                                (reserva.retirarAte?.let { " — retire até ${dataParaLer(it)}" }
                                    ?: "")
                        else
                            "Você é o ${reserva.posicao}º da fila",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = if (reserva.separado) PesoSemibold
                                     else PesoRegular,
                        color = if (reserva.separado) SigbefCores.atual.navy else SigbefCores.atual.secundario
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
            androidx.compose.material3.HorizontalDivider(color = SigbefCores.atual.linha)
            Spacer(modifier = Modifier.height(4.dp))

            TextButton(
                onClick = { onCancelar(reserva) },
                enabled = !isOffline && !acaoEmCurso,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = if (isOffline) "Sem conexão para sair da fila"
                           else "Sair da fila",
                    style = MaterialTheme.typography.bodySmall,
                    color = SigbefCores.atual.secundario
                )
            }
        }
    }
}

@Composable
private fun HistoryLoanCard(emp: Emprestimo) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = SigbefCores.atual.superficie,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
    ) {
        // Sem seta ">" à direita: ela prometia abrir alguma coisa, e o
        // cartão não é clicável — não há tela de detalhe do empréstimo.
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                // Sem "(autor)": o empréstimo não carrega autor (é outra
                // tabela, N:N), então saía "Título ()".
                text = emp.livroTitulo,
                style = MaterialTheme.typography.titleSmall,
                color = SigbefCores.atual.tinta
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = "Devolvido em " +
                    dataParaLer(emp.dataDevolvido ?: emp.dataDevolucao),
                style = MaterialTheme.typography.bodySmall,
                color = SigbefCores.atual.secundario
            )
        }
    }
}
