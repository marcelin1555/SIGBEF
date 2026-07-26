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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.ui.components.LeitorQr
import br.rn.cefe.sigbef.ui.theme.SigbefBackground
import br.rn.cefe.sigbef.ui.theme.SigbefBlue
import br.rn.cefe.sigbef.ui.theme.SigbefBlueFundo
import br.rn.cefe.sigbef.ui.theme.SigbefError
import br.rn.cefe.sigbef.ui.theme.SigbefInk
import br.rn.cefe.sigbef.ui.theme.SigbefLine
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import br.rn.cefe.sigbef.ui.theme.SigbefSurfaceContainerLow

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
        Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
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
                Text("Cancelar", color = Color.White)
            }
        }
        return
    }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = SigbefBackground
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            verticalArrangement = Arrangement.SpaceBetween,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header Top
            Surface(
                color = Color.White,
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
                        tint = SigbefNavy,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        text = "SIGBEF",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = SigbefNavy
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
                        .background(SigbefBlueFundo)
                        .border(1.dp, SigbefLine, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.QrCodeScanner,
                        contentDescription = "QR Code Illustration",
                        tint = SigbefNavy,
                        modifier = Modifier.size(88.dp)
                    )
                }

                Spacer(modifier = Modifier.height(28.dp))

                Text(
                    text = "Conectar à biblioteca da escola",
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    color = SigbefInk,
                    textAlign = TextAlign.Center
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Peça à bibliotecária para abrir Configurações → " +
                        "Integrações → Parear celular, e aponte a câmera " +
                        "para o QR que aparecer na tela.",
                    fontSize = 15.sp,
                    color = SigbefMuted,
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
                    colors = ButtonDefaults.buttonColors(containerColor = SigbefNavy),
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
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
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
                        fontSize = 14.sp,
                        color = SigbefNavy
                    )
                }
            }

            // Footer Privacy Notice
            Surface(
                color = SigbefSurfaceContainerLow,
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
                        tint = SigbefMuted,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.size(8.dp))
                    Text(
                        text = "Seus dados ficam na escola. Nada vai para a internet.",
                        fontSize = 13.sp,
                        color = SigbefMuted
                    )
                }
            }
        }
    }

    if (showManualDialog) {
        AlertDialog(
            onDismissRequest = { showManualDialog = false },
            title = {
                Text("Endereço da Biblioteca", fontWeight = FontWeight.Bold)
            },
            text = {
                Column {
                    Text(
                        "Informe o IP e a porta exibidos no SIGBEF do computador da biblioteca:",
                        fontSize = 13.sp,
                        color = SigbefMuted
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
                        Text(erro, fontSize = 12.sp, color = SigbefError)
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = { onConnected(ipInput) },
                    enabled = ipInput.isNotBlank() && !carregando,
                    colors = ButtonDefaults.buttonColors(containerColor = SigbefNavy)
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
