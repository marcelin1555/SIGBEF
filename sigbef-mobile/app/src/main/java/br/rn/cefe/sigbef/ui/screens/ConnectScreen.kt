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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.ui.components.LeitorQr
import br.rn.cefe.sigbef.ui.theme.SigbefCores
import br.rn.cefe.sigbef.ui.theme.SigbefFixo

@Composable
fun ConnectScreen(
    onConnected: (String) -> Unit,
    carregando: Boolean = false,
    erro: String? = null
) {
    // Abre o diálogo já com a mensagem de erro quando a última tentativa
    // falhou, para o aluno corrigir o endereço sem se perder.
    var showManualDialog by remember(erro) { mutableStateOf(erro != null) }
    // Sem valor de exemplo: cada escola tem o seu endereço.
    var ipInput by remember { mutableStateOf("") }
    var escaneando by remember { mutableStateOf(false) }

    // A câmera ocupa a tela inteira enquanto está ativa: mirar um código
    // pequeno numa janelinha é frustrante.
    if (escaneando) {
        Box(modifier = Modifier.fillMaxSize().background(SigbefFixo.TintaPreta)) {
            LeitorQr(
                modifier = Modifier.fillMaxSize(),
                aoLer = { conteudo ->
                    escaneando = false
                    onConnected(conteudo)
                },
                aoCancelar = {
                    escaneando = false
                    showManualDialog = true
                }
            )
            TextButton(
                onClick = { escaneando = false },
                modifier = Modifier.align(Alignment.TopStart).padding(8.dp)
            ) {
                Text("Cancelar", color = SigbefFixo.SobreCamera)
            }
        }
        return
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = SigbefCores.atual.fundo
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header Top
            Surface(
                color = SigbefCores.atual.superficie,
                shadowElevation = 1.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.MenuBook,
                        contentDescription = null,
                        tint = SigbefCores.atual.navy,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        text = "SIGBEF",
                        style = MaterialTheme.typography.headlineSmall,
                        color = SigbefCores.atual.navy
                    )
                }
            }

            // Main Illustration & Instructions
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Graphic Illustration Card
                Box(
                    modifier = Modifier
                        .size(180.dp)
                        .clip(CircleShape)
                        .background(SigbefCores.atual.azulFundo)
                        .border(1.dp, SigbefCores.atual.linha, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.QrCodeScanner,
                        contentDescription = "QR Code Illustration",
                        tint = SigbefCores.atual.navy,
                        modifier = Modifier.size(88.dp)
                    )
                }

                Spacer(modifier = Modifier.height(28.dp))

                Text(
                    text = "Conectar à biblioteca da escola",
                    style = MaterialTheme.typography.headlineMedium,
                    color = SigbefCores.atual.tinta,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Peça à bibliotecária para abrir Configurações → " +
                        "Integrações → Parear celular, e aponte a câmera " +
                        "para o QR que aparecer na tela.",
                    style = MaterialTheme.typography.bodyLarge,
                    color = SigbefCores.atual.secundario,
                    textAlign = TextAlign.Center,
                    lineHeight = 22.sp,
                    modifier = Modifier.padding(horizontal = 16.dp)
                )

                Spacer(modifier = Modifier.height(32.dp))

                Button(
                    onClick = { escaneando = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = SigbefCores.atual.marca,
                        contentColor = SigbefCores.atual.sobreMarca,
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.QrCodeScanner,
                        contentDescription = null,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        text = "Ler o QR da biblioteca",
                        style = MaterialTheme.typography.titleMedium,
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                // Sempre disponível: aparelho sem câmera, câmera quebrada
                // ou QR ilegível não podem deixar o aluno sem saída.
                OutlinedButton(
                    onClick = { showManualDialog = true },
                    modifier = Modifier.fillMaxWidth().height(48.dp),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "Digitar o endereço",
                        style = MaterialTheme.typography.bodyMedium,
                        color = SigbefCores.atual.navy
                    )
                }
            }

            // Footer Privacy Notice
            Surface(
                color = SigbefCores.atual.superficieAlta,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Default.Lock,
                        contentDescription = "Privacidade",
                        tint = SigbefCores.atual.secundario,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        text = "Seus dados ficam na escola. Nada vai para a internet.",
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario
                    )
                }
            }
        }
    }

    if (showManualDialog) {
        AlertDialog(
            onDismissRequest = { showManualDialog = false },
            title = {
                Text(
                    "Endereço da Biblioteca",
                    style = MaterialTheme.typography.titleMedium,
                )
            },
            text = {
                Column {
                    Text(
                        "Informe o IP e a porta exibidos no SIGBEF do computador da biblioteca:",
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    OutlinedTextField(
                        value = ipInput,
                        onValueChange = { ipInput = it },
                        label = { Text("IP e Porta (ex: 192.168.1.100:8765)") },
                        singleLine = true,
                        isError = erro != null,
                        modifier = Modifier.fillMaxWidth()
                    )
                    if (erro != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(erro, style = MaterialTheme.typography.bodySmall, color = SigbefCores.atual.erro)
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = { onConnected(ipInput) },
                    enabled = ipInput.isNotBlank() && !carregando,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = SigbefCores.atual.marca,
                        contentColor = SigbefCores.atual.sobreMarca,
                    )
                ) {
                    Text(if (carregando) "Conectando…" else "Conectar")
                }
            },
            dismissButton = {
                TextButton(onClick = { showManualDialog = false }) {
                    Text("Cancelar")
                }
            }
        )
    }
}
