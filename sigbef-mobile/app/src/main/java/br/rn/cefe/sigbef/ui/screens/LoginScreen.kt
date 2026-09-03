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
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import br.rn.cefe.sigbef.ui.theme.SigbefCores

@Composable
fun LoginScreen(
    onEntrar: (matricula: String, senha: String) -> Unit,
    carregando: Boolean = false,
    erro: String? = null
) {
    // Campos vazios: antes vinham preenchidos com uma matrícula e senha
    // de exemplo, e o botão só avançava de tela sem validar nada.
    var matricula by remember { mutableStateOf("") }
    var senha by remember { mutableStateOf("") }

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = SigbefCores.atual.fundo
    ) {
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Surface(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                shape = RoundedCornerShape(16.dp),
                color = SigbefCores.atual.superficie,
                shadowElevation = 6.dp,
                border = androidx.compose.foundation.BorderStroke(1.dp, SigbefCores.atual.linha)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Logo Badge
                    Box(
                        modifier = Modifier
                            .size(72.dp)
                            .clip(CircleShape)
                            .background(SigbefCores.atual.marca),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.MenuBook,
                            contentDescription = "SIGBEF Logo",
                            tint = SigbefCores.atual.sobreMarca,
                            modifier = Modifier.size(36.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    Text(
                        text = "SIGBEF",
                        style = MaterialTheme.typography.displaySmall,
                        color = SigbefCores.atual.navy,
                        letterSpacing = (-0.5).sp
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Sistema Integrado de Gestão de Biblioteca Escolar",
                        style = MaterialTheme.typography.bodySmall,
                        color = SigbefCores.atual.secundario,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(28.dp))

                    // Input Matrícula
                    OutlinedTextField(
                        value = matricula,
                        onValueChange = { matricula = it },
                        placeholder = { Text("Matrícula") },
                        leadingIcon = {
                            Box(
                                modifier = Modifier
                                    .padding(start = 8.dp)
                                    .size(32.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(SigbefCores.atual.azulFundo),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Badge,
                                    contentDescription = null,
                                    tint = SigbefCores.atual.navy,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(8.dp)
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    // Input Senha
                    OutlinedTextField(
                        value = senha,
                        onValueChange = { senha = it },
                        placeholder = { Text("Senha") },
                        visualTransformation = PasswordVisualTransformation(),
                        leadingIcon = {
                            Box(
                                modifier = Modifier
                                    .padding(start = 8.dp)
                                    .size(32.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(SigbefCores.atual.azulFundo),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Lock,
                                    contentDescription = null,
                                    tint = SigbefCores.atual.navy,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(8.dp)
                    )

                    Spacer(modifier = Modifier.height(28.dp))

                    // Mensagem de erro devolvida pela biblioteca
                    if (erro != null) {
                        Surface(
                            modifier = Modifier.fillMaxWidth(),
                            color = SigbefCores.atual.erroFundo,
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = erro,
                                modifier = Modifier.padding(12.dp),
                                style = MaterialTheme.typography.bodySmall,
                                color = SigbefCores.atual.erro
                            )
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                    }

                    Button(
                        onClick = { onEntrar(matricula, senha) },
                        enabled = !carregando &&
                            matricula.isNotBlank() && senha.isNotBlank(),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(50.dp),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = SigbefCores.atual.marca,
                            contentColor = SigbefCores.atual.sobreMarca,
                        ),
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Text(
                            text = if (carregando) "Entrando…" else "Entrar",
                            style = MaterialTheme.typography.titleMedium,
                            color = SigbefCores.atual.sobreMarca
                        )
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    // Warning Text Box
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = SigbefCores.atual.superficieAlta,
                        shape = RoundedCornerShape(8.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.Info,
                                contentDescription = "Info",
                                tint = SigbefCores.atual.secundario,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.size(8.dp))
                            Text(
                                text = "Use a mesma matrícula e senha do sistema da biblioteca.\nEsqueceu? Procure a bibliotecária.",
                                style = MaterialTheme.typography.bodySmall,
                                color = SigbefCores.atual.secundario,
                                lineHeight = 16.sp
                            )
                        }
                    }
                }
            }
        }
    }
}
