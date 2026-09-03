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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefCores

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
        containerColor = SigbefCores.atual.fundo
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
                color = SigbefCores.atual.azulFundo,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.azul)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.Info,
                        contentDescription = null,
                        tint = SigbefCores.atual.azul,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = "Você renova pelo próprio app, em \"Meus " +
                            "empréstimos\", enquanto o prazo não vencer.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SigbefCores.atual.navy,
                        lineHeight = 20.sp
                    )
                }
            }

            // Numbered Steps List
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = SigbefCores.atual.superficie,
                shadowElevation = 2.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
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
                color = SigbefCores.atual.avisoFundo,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.dourado)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.Warning,
                        contentDescription = null,
                        tint = SigbefCores.atual.aviso,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = "Não dá para renovar se o prazo já venceu, " +
                            "se outro estudante está na fila de espera ou " +
                            "se você já renovou o livro várias vezes. " +
                            "Nesses casos, procure o balcão.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SigbefCores.atual.avisoTinta,
                        lineHeight = 20.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Action Button
            Button(
                onClick = { onNavigate(Screen.LOANS) },
                colors = ButtonDefaults.buttonColors(
                    containerColor = SigbefCores.atual.marca,
                    contentColor = SigbefCores.atual.sobreMarca,
                ),
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
                    style = MaterialTheme.typography.titleSmall,
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
                .background(SigbefCores.atual.marca),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = number,
                style = MaterialTheme.typography.titleSmall,
                color = SigbefCores.atual.sobreMarca
            )
        }
        Spacer(modifier = Modifier.width(16.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = SigbefCores.atual.tinta
        )
    }
}
