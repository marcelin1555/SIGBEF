package com.example.sigbef.ui.screens

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
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.sigbef.model.Emprestimo
import com.example.sigbef.model.Screen
import com.example.sigbef.ui.components.SigbefBottomNavigation
import com.example.sigbef.ui.components.SigbefTopAppBar
import com.example.ui.theme.SigbefBlue
import com.example.ui.theme.SigbefError
import com.example.ui.theme.SigbefGold
import com.example.ui.theme.SigbefLine
import com.example.ui.theme.SigbefMuted
import com.example.ui.theme.SigbefNavy
import com.example.ui.theme.SigbefSuccess

@Composable
fun LoansScreen(
    emprestimos: List<Emprestimo>,
    isOffline: Boolean,
    onNavigate: (Screen) -> Unit,
    onRequestRenewal: ((Int) -> Unit)? = null
) {
    val ativos = emprestimos.filter { !it.devolvido }
    val historico = emprestimos.filter { it.devolvido }

    Scaffold(
        topBar = {
            SigbefTopAppBar(isOffline = isOffline)
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.LOANS,
                onNavigate = onNavigate,
                isOffline = isOffline
            )
        },
        containerColor = Color(0xFFF7F9FC)
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .padding(horizontal = 20.dp, vertical = 16.dp)
        ) {
            Text(
                text = "Meus empréstimos",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Acompanhe seus livros e o histórico",
                fontSize = 14.sp,
                color = SigbefMuted
            )

            Spacer(modifier = Modifier.height(8.dp))

            TextButton(
                onClick = { onNavigate(Screen.RENEW_INFO) },
                modifier = Modifier.padding(0.dp)
            ) {
                Text(
                    text = "Como renovar",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = SigbefBlue,
                    textDecoration = TextDecoration.Underline
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            if (ativos.isEmpty()) {
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
                            .background(Color(0xFFD1E4FF).copy(alpha = 0.5f)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.ImportContacts,
                            contentDescription = null,
                            tint = SigbefNavy,
                            modifier = Modifier.size(64.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    Text(
                        text = "Você ainda não pegou nenhum livro",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                        color = SigbefNavy,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Quando pegar um livro emprestado no balcão, ele aparece aqui com o prazo de devolução.",
                        fontSize = 14.sp,
                        color = SigbefMuted,
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 24.dp)
                    )

                    Spacer(modifier = Modifier.height(28.dp))

                    Button(
                        onClick = { onNavigate(Screen.ACERVO) },
                        colors = ButtonDefaults.buttonColors(containerColor = SigbefGold),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                    ) {
                        Text(
                            text = "EXPLORAR O ACERVO",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = SigbefNavy,
                            letterSpacing = 1.sp
                        )
                    }
                }
            } else {
                LazyColumn(
                    verticalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxSize()
                ) {
                    item {
                        Text(
                            text = "COM VOCÊ AGORA (${ativos.size})",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = SigbefMuted,
                            letterSpacing = 1.5.sp
                        )
                    }

                    items(ativos) { emp ->
                        ActiveLoanCard(emp = emp, onRequestRenewal = onRequestRenewal)
                    }

                    if (historico.isNotEmpty()) {
                        item {
                            Spacer(modifier = Modifier.height(12.dp))
                            Text(
                                text = "HISTÓRICO RECENTE",
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                color = SigbefMuted,
                                letterSpacing = 1.5.sp
                            )
                        }

                        items(historico) { emp ->
                            HistoryLoanCard(emp = emp)
                        }

                        item {
                            TextButton(
                                onClick = { },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = "Ver todo o histórico",
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = SigbefBlue,
                                    textDecoration = TextDecoration.Underline
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ActiveLoanCard(
    emp: Emprestimo,
    onRequestRenewal: ((Int) -> Unit)? = null
) {
    val spineColor = try {
        Color(android.graphics.Color.parseColor(emp.spineColorHex))
    } catch (e: Exception) {
        SigbefNavy
    }

    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = Color.White,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(
            width = if (emp.atrasado) 1.5.dp else 1.dp,
            color = if (emp.atrasado) SigbefError else SigbefLine
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
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF1A1A1A)
                    )

                    Spacer(modifier = Modifier.height(2.dp))

                    Text(
                        text = "Devolução em ${emp.dataDevolucao}",
                        fontSize = 13.sp,
                        color = SigbefMuted,
                        textDecoration = if (emp.atrasado) TextDecoration.LineThrough else TextDecoration.None
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        if (emp.atrasado) {
                            Row(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(Color(0xFFFFDAD6))
                                    .padding(horizontal = 8.dp, vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Error,
                                    contentDescription = "Atrasado",
                                    tint = SigbefError,
                                    modifier = Modifier.size(14.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = "Atrasado",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = SigbefError
                                )
                            }
                        } else {
                            Row(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(Color(0xFF2E7D32).copy(alpha = 0.1f))
                                    .padding(horizontal = 8.dp, vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    imageVector = Icons.Default.CheckCircle,
                                    contentDescription = "Em dia",
                                    tint = SigbefSuccess,
                                    modifier = Modifier.size(14.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = "Em dia",
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = SigbefSuccess
                                )
                            }
                        }

                        if (emp.renovacaoPendente) {
                            Row(
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .background(Color(0xFFFFF8E1))
                                    .padding(horizontal = 8.dp, vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = "RENOVAÇÃO SOLICITADA",
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    color = Color(0xFFE65100)
                                )
                            }
                        }
                    }
                }
            }

            if (!emp.atrasado && !emp.devolvido) {
                Spacer(modifier = Modifier.height(12.dp))
                androidx.compose.material3.HorizontalDivider(color = SigbefLine)
                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Renovações restantes: ${emp.renovacoesRestantes}",
                        fontSize = 12.sp,
                        color = SigbefMuted
                    )

                    Button(
                        onClick = { onRequestRenewal?.invoke(emp.id) },
                        enabled = !emp.renovacaoPendente && emp.renovacoesRestantes > 0,
                        colors = ButtonDefaults.buttonColors(containerColor = SigbefNavy),
                        shape = RoundedCornerShape(6.dp),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text(
                            text = if (emp.renovacaoPendente) "SOLICITADA" else "RENOVAR LIVRO",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HistoryLoanCard(emp: Emprestimo) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = Color.White,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "${emp.livroTitulo} (${emp.autor})",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "Devolvido em ${emp.dataDevolvido ?: emp.dataDevolucao}",
                    fontSize = 12.sp,
                    color = SigbefMuted
                )
            }

            Icon(
                imageVector = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                contentDescription = null,
                tint = SigbefMuted
            )
        }
    }
}
