package br.rn.cefe.sigbef.ui.components

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.annotation.OptIn
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.NoPhotography
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.LocalLifecycleOwner
import br.rn.cefe.sigbef.ui.theme.SigbefGold
import br.rn.cefe.sigbef.ui.theme.SigbefMuted
import br.rn.cefe.sigbef.ui.theme.SigbefNavy
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import java.util.concurrent.Executors

/**
 * Lê o QR de pareamento que o SIGBEF mostra na tela do computador da
 * biblioteca (Configurações → Integrações → Parear celular).
 *
 * A imagem é analisada quadro a quadro em memória e descartada: nada é
 * gravado no aparelho nem enviado para lugar nenhum. O QR carrega só o
 * endereço da biblioteca (`sigbef://ip:porta`) — nunca uma credencial,
 * porque ele fica exposto na tela e qualquer um poderia fotografá-lo.
 *
 * @param aoLer chamado uma única vez, com o conteúdo do primeiro código
 *              reconhecido.
 */
@Composable
fun LeitorQr(
    aoLer: (String) -> Unit,
    aoCancelar: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var temPermissao by remember { mutableStateOf(temPermissaoCamera(context)) }
    var negouPermissao by remember { mutableStateOf(false) }

    val pedirPermissao = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { concedida ->
        temPermissao = concedida
        negouPermissao = !concedida
    }

    LaunchedEffect(Unit) {
        if (!temPermissao) pedirPermissao.launch(Manifest.permission.CAMERA)
    }

    when {
        temPermissao -> CameraDoQr(aoLer = aoLer, modifier = modifier)

        negouPermissao -> SemCamera(
            texto = "Sem acesso à câmera não dá para ler o QR. Você pode " +
                "liberar nas configurações do celular, ou digitar o " +
                "endereço da biblioteca.",
            aoCancelar = aoCancelar,
            modifier = modifier
        )

        else -> SemCamera(
            texto = "Pedindo acesso à câmera…",
            aoCancelar = aoCancelar,
            modifier = modifier
        )
    }
}

private fun temPermissaoCamera(context: Context): Boolean =
    context.checkSelfPermission(Manifest.permission.CAMERA) ==
        PackageManager.PERMISSION_GRANTED

@Composable
private fun SemCamera(
    texto: String,
    aoCancelar: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.NoPhotography,
            contentDescription = null,
            tint = SigbefMuted,
            modifier = Modifier.size(48.dp)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = texto,
            fontSize = 14.sp,
            color = SigbefMuted,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(16.dp))
        TextButton(onClick = aoCancelar) {
            Text("Digitar o endereço")
        }
    }
}

/**
 * A câmera em si.
 *
 * O `ImageAnalysis` roda numa thread própria e usa
 * KEEP_ONLY_LATEST: se a análise de um quadro demorar, os quadros
 * seguintes são descartados em vez de acumularem uma fila crescente.
 */
@Composable
private fun CameraDoQr(
    aoLer: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val executor = remember { Executors.newSingleThreadExecutor() }
    val leitor = remember {
        BarcodeScanning.getClient(
            BarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                .build()
        )
    }
    // Guarda para o callback não disparar de novo a cada quadro enquanto
    // a tela seguinte ainda não substituiu esta.
    var jaLeu by remember { mutableStateOf(false) }

    DisposableEffect(Unit) {
        onDispose {
            leitor.close()
            executor.shutdown()
        }
    }

    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        AndroidView(
            modifier = Modifier.fillMaxSize(),
            factory = { ctx ->
                val previewView = PreviewView(ctx)
                val futuro = ProcessCameraProvider.getInstance(ctx)
                futuro.addListener({
                    val provider = futuro.get()
                    val preview = Preview.Builder().build().also {
                        it.surfaceProvider = previewView.surfaceProvider
                    }
                    val analise = ImageAnalysis.Builder()
                        .setBackpressureStrategy(
                            ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST
                        )
                        .build()
                    analise.setAnalyzer(executor) { imagem ->
                        analisar(imagem, leitor) { texto ->
                            if (!jaLeu) {
                                jaLeu = true
                                aoLer(texto)
                            }
                        }
                    }
                    runCatching {
                        provider.unbindAll()
                        provider.bindToLifecycle(
                            lifecycleOwner,
                            CameraSelector.DEFAULT_BACK_CAMERA,
                            preview,
                            analise
                        )
                    }
                }, androidx.core.content.ContextCompat.getMainExecutor(ctx))
                previewView
            }
        )

        // Moldura que mostra onde encaixar o código.
        Box(
            modifier = Modifier
                .size(220.dp)
                .border(3.dp, SigbefGold, RoundedCornerShape(16.dp))
        )

        Text(
            text = "Aponte para o QR na tela da biblioteca",
            color = Color.White,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(24.dp)
                .background(SigbefNavy.copy(alpha = 0.85f),
                            RoundedCornerShape(8.dp))
                .padding(horizontal = 16.dp, vertical = 10.dp)
        )
    }
}

/**
 * Analisa um quadro. `imagem.close()` é obrigatório em todo caminho,
 * senão a câmera trava depois de alguns quadros.
 */
@OptIn(ExperimentalGetImage::class)
private fun analisar(
    imagem: ImageProxy,
    leitor: com.google.mlkit.vision.barcode.BarcodeScanner,
    aoLer: (String) -> Unit
) {
    val bruta = imagem.image
    if (bruta == null) {
        imagem.close()
        return
    }
    val entrada = InputImage.fromMediaImage(
        bruta, imagem.imageInfo.rotationDegrees
    )
    leitor.process(entrada)
        .addOnSuccessListener { codigos ->
            codigos.firstNotNullOfOrNull { it.rawValue }?.let(aoLer)
        }
        .addOnCompleteListener { imagem.close() }
}
