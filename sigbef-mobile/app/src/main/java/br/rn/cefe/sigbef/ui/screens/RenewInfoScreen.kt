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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefBackground
import br.rn.cefe.sigbef.ui.theme.SigbefBlue
import br.rn.cefe.sigbef.ui.theme.SigbefBlueFundo
import br.rn.cefe.sigbef.ui.theme.SigbefGold
import br.rn.cefe.sigbef.ui.theme.SigbefInk
import br.rn.cefe.sigbef.ui.theme.SigbefLine
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefWarning
import br.rn.cefe.sigbef.ui.theme.SigbefWarningFundo
import br.rn.cefe.sigbef.ui.theme.SigbefWarningInk

@Composable
fun RenewInfoScreen(
    isOffline: Boolean,
    onBackClick: () -> Unit,
    onNavigate: (Screen) -> Unit
) {
    Scaffold(
        topBar = {
            SigbefTopAppBar(
                title = "Como renovar",
                showBack = true,
                onBackClick = onBackClick,
                isOffline = isOffline
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.RENEW_INFO,
                onNavigate = onNavigate
            )
        },
        containerColor = SigbefBackground
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Soft Blue Notice Box
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                color = SigbefBlueFundo,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefBlue)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.Info,
                        contentDescription = null,
                        tint = SigbefBlue,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = "Você renova pelo próprio app, em \"Meus " +
                            "empréstimos\", enquanto o prazo não vencer.",
                        fontSize = 14.sp,
                        color = SigbefNavy,
                        lineHeight = 20.sp
                    )
                }
            }

            // Numbered Steps List
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = Color.White,
                shadowElevation = 2.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefLine)
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(20.dp)
                ) {
                    StepItem(number = "1", title = "Conecte-se ao Wi-Fi da escola")
                    StepItem(number = "2", title = "Abra 'Meus empréstimos'")
                    StepItem(number = "3", title = "Toque em 'Renovar' no livro que quiser")
                    StepItem(number = "4", title = "O novo prazo aparece ali mesmo")
                }
            }

            // Warning Box
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                color = SigbefWarningFundo,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefGold)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.Warning,
                        contentDescription = null,
                        tint = SigbefWarning,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = "Não dá para renovar se o prazo já venceu, " +
                            "se outro estudante está na fila de espera ou " +
                            "se você já renovou o livro várias vezes. " +
                            "Nesses casos, procure o balcão.",
                        fontSize = 14.sp,
                        color = SigbefWarningInk,
                        lineHeight = 20.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Action Button
            Button(
                onClick = { onNavigate(Screen.LOANS) },
                colors = ButtonDefaults.buttonColors(containerColor = SigbefNavy),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Badge,
                    contentDescription = null,
                    modifier = Modifier.size(20.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "IR PARA MEUS EMPRÉSTIMOS",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
            }
        }
    }
}

@Composable
private fun StepItem(number: String, title: String) {
    Row(
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(32.dp)
                .clip(CircleShape)
                .background(SigbefNavy),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = number,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Color.White
            )
        }
        Spacer(modifier = Modifier.width(16.dp))
        Text(
            text = title,
            fontSize = 15.sp,
            fontWeight = FontWeight.Medium,
            color = SigbefInk
        )
    }
}
