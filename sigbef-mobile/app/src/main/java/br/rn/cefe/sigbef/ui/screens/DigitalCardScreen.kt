package br.rn.cefe.sigbef.ui.screens

import androidx.compose.foundation.background
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.Icon
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.TextButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.model.Usuario
import br.rn.cefe.sigbef.ui.components.BarcodeView
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefGold
import br.rn.cefe.sigbef.ui.theme.SigbefLine
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefSuccess

@Composable
fun DigitalCardScreen(
    usuario: Usuario,
    isOffline: Boolean,
    onNavigate: (Screen) -> Unit,
    onSair: () -> Unit = {},
    onTrocarBiblioteca: () -> Unit = {}
) {
    Scaffold(
        topBar = {
            SigbefTopAppBar(isOffline = isOffline)
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.CARD,
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
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Cartão digital",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1A1A1A)
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Apresente este código no balcão",
                fontSize = 14.sp,
                color = SigbefMuted
            )

            Spacer(modifier = Modifier.height(28.dp))

            // Digital Card Container
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = Color.White,
                shadowElevation = 4.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
            ) {
                Column {
                    // Gold Accent Stripe
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(6.dp)
                            .background(SigbefGold)
                    )

                    // Navy Header
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(SigbefNavy)
                            .padding(vertical = 12.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = usuario.escola.uppercase(),
                            fontSize = 12.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = Color.White,
                            letterSpacing = 2.sp
                        )
                    }

                    // Card Body
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = usuario.nome,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFF1A1A1A),
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(4.dp))

                        Text(
                            text = "Matrícula: ${usuario.matricula}",
                            fontSize = 14.sp,
                            color = SigbefMuted,
                            fontWeight = FontWeight.Medium
                        )

                        Spacer(modifier = Modifier.height(2.dp))

                        Text(
                            text = usuario.turma,
                            fontSize = 13.sp,
                            color = SigbefMuted
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        // Barcode Section
                        Surface(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp),
                            color = Color(0xFFFFFFFF),
                            border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
                        ) {
                            BarcodeView(code = usuario.matricula)
                        }
                    }

                    // Footer Note
                    Surface(
                        color = Color(0xFFF2F4F7),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(12.dp),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = SigbefSuccess,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Funciona mesmo sem internet.",
                                fontSize = 13.sp,
                                color = Color(0xFF42474F),
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            // Encerrar a sessão neste aparelho. Antes não havia como sair:
            // o acesso do aluno ficava para sempre e, num celular
            // compartilhado, o próximo via os dados do anterior.
            OutlinedButton(
                onClick = onSair,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.Logout,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Sair da minha conta")
            }

            Spacer(modifier = Modifier.height(8.dp))

            TextButton(
                onClick = onTrocarBiblioteca,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Trocar de biblioteca", color = SigbefMuted, fontSize = 13.sp)
            }
        }
    }
}
