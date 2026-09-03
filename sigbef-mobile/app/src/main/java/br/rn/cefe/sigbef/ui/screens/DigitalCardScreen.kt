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
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import br.rn.cefe.sigbef.aviso.AvisoDevolucao
import br.rn.cefe.sigbef.model.Screen
import br.rn.cefe.sigbef.model.Usuario
import br.rn.cefe.sigbef.ui.components.BarcodeView
import br.rn.cefe.sigbef.ui.components.SigbefBottomNavigation
import br.rn.cefe.sigbef.ui.components.SigbefTopAppBar
import br.rn.cefe.sigbef.ui.theme.SigbefCores

@Composable
fun DigitalCardScreen(
    usuario: Usuario,
    isOffline: Boolean,
    ultimaSincronizacao: String? = null,
    onNavigate: (Screen) -> Unit,
    onSair: () -> Unit = {},
    onTrocarBiblioteca: () -> Unit = {},
    /** Buscar dados novos na biblioteca. */
    onAtualizar: (() -> Unit)? = null,
    carregando: Boolean = false
) {
    Scaffold(
        topBar = {
            SigbefTopAppBar(
                title = "Cartão digital",
                subtitle = "Apresente este código no balcão",
                isOffline = isOffline,
                ultimaSincronizacao = ultimaSincronizacao,
                onAtualizar = onAtualizar,
                carregando = carregando
            )
        },
        bottomBar = {
            SigbefBottomNavigation(
                currentScreen = Screen.CARD,
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
                .padding(horizontal = 20.dp, vertical = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Digital Card Container
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                color = SigbefCores.atual.superficie,
                shadowElevation = 4.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
            ) {
                Column {
                    // Gold Accent Stripe
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(6.dp)
                            .background(SigbefCores.atual.dourado)
                    )

                    // Navy Header
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(SigbefCores.atual.marca)
                            .padding(vertical = 12.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = usuario.escola.uppercase(),
                            style = MaterialTheme.typography.labelMedium,
                            color = SigbefCores.atual.sobreMarca,
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
                            style = MaterialTheme.typography.headlineSmall,
                            color = SigbefCores.atual.tinta,
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(4.dp))

                        Text(
                            text = "Matrícula: ${usuario.matricula}",
                            style = MaterialTheme.typography.titleSmall,
                            color = SigbefCores.atual.secundario,
                        )

                        Spacer(modifier = Modifier.height(2.dp))

                        Text(
                            text = usuario.turma,
                            style = MaterialTheme.typography.bodySmall,
                            color = SigbefCores.atual.secundario
                        )

                        Spacer(modifier = Modifier.height(24.dp))

                        // Barcode Section
                        Surface(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp),
                            color = SigbefCores.atual.superficie,
                            border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
                        ) {
                            BarcodeView(code = usuario.matricula)
                        }
                    }

                    // Footer Note
                    Surface(
                        color = SigbefCores.atual.superficieAlta,
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
                                tint = SigbefCores.atual.sucesso,
                                modifier = Modifier.size(16.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Funciona mesmo sem internet.",
                                style = MaterialTheme.typography.titleSmall,
                                color = SigbefCores.atual.tinta,
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            AvisoDevolucaoOpcao()

            Spacer(modifier = Modifier.height(20.dp))

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
                Text(
                    "Trocar de biblioteca",
                    color = SigbefCores.atual.secundario,
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

/**
 * Interruptor do aviso de devolução.
 *
 * Fica aqui, junto de "sair da conta", porque é a única tela do app com
 * ajustes do próprio aluno — criar uma tela de configurações inteira
 * para uma opção seria mais navegação do que ajuste.
 *
 * A permissão de notificação é pedida **ao ligar**, não na abertura do
 * app: pedir antes de existir o motivo é o jeito mais rápido de levar
 * um "não" permanente.
 */
@Composable
private fun AvisoDevolucaoOpcao() {
    val contexto = LocalContext.current
    var ligado by remember { mutableStateOf(AvisoDevolucao.ligado(contexto)) }

    val pedirPermissao = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { concedida ->
        // Sem permissão o aviso não teria como aparecer, então o
        // interruptor volta sozinho em vez de ficar ligado mentindo.
        ligado = concedida
        AvisoDevolucao.definir(contexto, concedida)
    }

    Surface(
        shape = RoundedCornerShape(14.dp),
        color = SigbefCores.atual.superficie,
        border = BorderStroke(1.dp, SigbefCores.atual.linha),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "Avisar quando o livro estiver para vencer",
                    style = MaterialTheme.typography.titleSmall
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Um aviso no celular na véspera da devolução. " +
                        "Funciona sem internet.",
                    color = SigbefCores.atual.secundario,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Spacer(modifier = Modifier.width(12.dp))
            Switch(
                checked = ligado,
                onCheckedChange = { querLigar ->
                    if (querLigar && !AvisoDevolucao.temPermissao(contexto)) {
                        pedirPermissao.launch(Manifest.permission.POST_NOTIFICATIONS)
                    } else {
                        ligado = querLigar
                        AvisoDevolucao.definir(contexto, querLigar)
                    }
                }
            )
        }
    }
}
