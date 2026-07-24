package com.example.sigbef.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Autorenew
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.ImportContacts
import androidx.compose.material.icons.filled.LibraryBooks
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.sigbef.model.Emprestimo
import com.example.sigbef.model.Screen
import com.example.sigbef.model.Usuario
import com.example.sigbef.ui.components.SigbefBottomNavigation
import com.example.sigbef.ui.components.SigbefTopAppBar
import com.example.ui.theme.SigbefBlue
import com.example.ui.theme.SigbefLine
import com.example.ui.theme.SigbefMuted
import com.example.ui.theme.SigbefNavy
import com.example.ui.theme.SigbefWarning

@Composable
fun HomeScreen(
    usuario: Usuario,
    emprestimos: List<Emprestimo> = emptyList(),
    isOffline: Boolean,
    onNavigate: (Screen) -> Unit
) {
    val ativos = emprestimos.filter { !it.devolvido }
    val atrasados = ativos.filter { it.atrasado }
    val maxLivros = usuario.limMaxLivros
    Scaffold(
        topBar = {
            SigbefTopAppBar(isOffline = isOffline)
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.HOME,
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
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                // Header Greeting
                Text(
                    text = "Olá, ${usuario.nome.split(" ").first()}!",
                    fontSize = 26.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF1A1A1A)
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = usuario.turma,
                    fontSize = 14.sp,
                    color = SigbefMuted
                )

                Spacer(modifier = Modifier.height(20.dp))

                // Main Status Card
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    color = Color.White,
                    shadowElevation = 2.dp,
                    border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.Top
                        ) {
                            Column {
                                Text(
                                    text = if (ativos.isEmpty()) "Nenhum livro emprestado" else "${ativos.size} ${if (ativos.size == 1) "livro com você" else "livros com você"}",
                                    fontSize = 18.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFF1A1A1A)
                                )

                                Spacer(modifier = Modifier.height(6.dp))

                                if (atrasados.isNotEmpty()) {
                                    Row(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(Color(0xFFFFDAD6))
                                            .padding(horizontal = 8.dp, vertical = 4.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.Schedule,
                                            contentDescription = null,
                                            tint = Color(0xFFB71C1C),
                                            modifier = Modifier.size(14.dp)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(
                                            text = "${atrasados.size} com devolução em atraso",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = Color(0xFFB71C1C)
                                        )
                                    }
                                } else if (ativos.isNotEmpty()) {
                                    Row(
                                        modifier = Modifier
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(Color(0xFFEF6C00).copy(alpha = 0.1f))
                                            .padding(horizontal = 8.dp, vertical = 4.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Icon(
                                            imageVector = Icons.Default.Schedule,
                                            contentDescription = null,
                                            tint = SigbefWarning,
                                            modifier = Modifier.size(14.dp)
                                        )
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(
                                            text = "1 vence em 3 dias",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = SigbefWarning
                                        )
                                    }
                                } else {
                                    Text(
                                        text = "Explore o acervo para reservar",
                                        fontSize = 13.sp,
                                        color = SigbefMuted
                                    )
                                }
                            }

                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .clip(CircleShape)
                                    .background(Color(0xFFD1E4FF)),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.ImportContacts,
                                    contentDescription = null,
                                    tint = SigbefNavy,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        // Progress Bar
                        LinearProgressIndicator(
                            progress = { (ativos.size.toFloat() / maxLivros.toFloat()).coerceIn(0f, 1f) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(RoundedCornerShape(4.dp)),
                            color = SigbefBlue,
                            trackColor = Color(0xFFE6E8EB)
                        )

                        Spacer(modifier = Modifier.height(6.dp))

                        Text(
                            text = "${ativos.size} de $maxLivros do limite",
                            fontSize = 12.sp,
                            color = SigbefMuted,
                            modifier = Modifier.align(Alignment.End)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                // Bento Grid Shortcuts (2x2)
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    BentoShortcutCard(
                        title = "Buscar no acervo",
                        icon = Icons.Default.Search,
                        onClick = { onNavigate(Screen.ACERVO) },
                        modifier = Modifier.weight(1f)
                    )
                    BentoShortcutCard(
                        title = "Meu cartão",
                        icon = Icons.Default.Badge,
                        onClick = { onNavigate(Screen.CARD) },
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    BentoShortcutCard(
                        title = "Meus empréstimos",
                        icon = Icons.Default.LibraryBooks,
                        onClick = { onNavigate(Screen.LOANS) },
                        modifier = Modifier.weight(1f)
                    )
                    BentoShortcutCard(
                        title = "Como renovar",
                        icon = Icons.Default.Autorenew,
                        onClick = { onNavigate(Screen.RENEW_INFO) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }

            // Bottom Connection Status Footer
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 8.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(if (!isOffline) Color(0xFF2E7D32) else SigbefWarning)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = if (!isOffline) "Conectado à ${usuario.escola}" else "Modo offline — biblioteca do CEFE",
                    fontSize = 13.sp,
                    color = SigbefMuted
                )
            }
        }
    }
}

@Composable
private fun BentoShortcutCard(
    title: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .aspectRatio(1.1f)
            .clickable { onClick() },
        shape = RoundedCornerShape(16.dp),
        color = Color.White,
        shadowElevation = 1.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.Start
        ) {
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(RoundedCornerShape(10.dp))
                    .background(Color(0xFFD1E4FF)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = title,
                    tint = SigbefNavy,
                    modifier = Modifier.size(22.dp)
                )
            }

            Text(
                text = title,
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold,
                color = Color(0xFF1A1A1A),
                lineHeight = 18.sp
            )
        }
    }
}
