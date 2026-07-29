package br.rn.cefe.sigbef.aviso

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import br.rn.cefe.sigbef.MainActivity
import br.rn.cefe.sigbef.R
import br.rn.cefe.sigbef.data.local.EmprestimoEntity
import br.rn.cefe.sigbef.data.local.SigbefDatabase
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.concurrent.TimeUnit

/**
 * Aviso de que o livro está para vencer.
 *
 * A verificação é **local**: o app já guarda os prazos no cache, então
 * não precisa de rede nem do servidor da escola ligado. Isso importa
 * porque o aviso útil chega em casa, à noite ou no fim de semana --
 * um aviso que só aparecesse dentro da escola chegaria quando o aluno
 * já está lá, tarde demais para servir.
 *
 * O preço dessa escolha: se o aluno renovar no balcão, o app só
 * descobre na próxima sincronização e pode avisar sem necessidade.
 * Avisar demais é melhor que avisar tarde.
 *
 * Nasce desligado, como toda função opcional do SIGBEF.
 */
object AvisoDevolucao {

    private const val CANAL = "sigbef_devolucao"
    private const val TRABALHO = "sigbef_aviso_devolucao"
    const val PREFS = "sigbef_aviso_prefs"
    const val CHAVE_LIGADO = "aviso_ligado"
    const val CHAVE_DIAS_ANTES = "aviso_dias_antes"

    /** Padrão: avisa na véspera. */
    const val DIAS_ANTES_PADRAO = 1

    fun ligado(context: Context): Boolean =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getBoolean(CHAVE_LIGADO, false)

    fun diasAntes(context: Context): Int =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getInt(CHAVE_DIAS_ANTES, DIAS_ANTES_PADRAO)

    /**
     * Liga ou desliga o aviso. Ao ligar, agenda a verificação diária;
     * ao desligar, cancela — nada fica rodando em segundo plano de quem
     * não quer o aviso.
     */
    fun definir(context: Context, ligado: Boolean, diasAntes: Int = DIAS_ANTES_PADRAO) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putBoolean(CHAVE_LIGADO, ligado)
            .putInt(CHAVE_DIAS_ANTES, diasAntes.coerceIn(0, 7))
            .apply()
        if (ligado) agendar(context) else cancelar(context)
    }

    private fun agendar(context: Context) {
        // Uma vez por dia basta: o prazo é contado em dias, e verificar
        // de hora em hora só gastaria bateria para dar a mesma resposta.
        val trabalho = PeriodicWorkRequestBuilder<AvisoWorker>(1, TimeUnit.DAYS)
            .setConstraints(
                Constraints.Builder()
                    .setRequiresBatteryNotLow(true)
                    .build()
            )
            .build()
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            TRABALHO, ExistingPeriodicWorkPolicy.KEEP, trabalho)
    }

    private fun cancelar(context: Context) {
        WorkManager.getInstance(context).cancelUniqueWork(TRABALHO)
    }

    /** Recria o agendamento na abertura, se o aviso estiver ligado. */
    fun restaurarSeLigado(context: Context) {
        if (ligado(context)) agendar(context)
    }

    fun criarCanal(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val canal = NotificationChannel(
            CANAL,
            "Devolução de livros",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "Aviso de que o prazo de devolução está chegando"
        }
        context.getSystemService(NotificationManager::class.java)
            ?.createNotificationChannel(canal)
    }

    fun temPermissao(context: Context): Boolean =
        Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            ContextCompat.checkSelfPermission(
                context, Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED

    fun notificar(context: Context, titulo: String, texto: String) {
        if (!temPermissao(context)) return
        criarCanal(context)
        val abrir = PendingIntent.getActivity(
            context, 0,
            Intent(context, MainActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_IMMUTABLE
        )
        val n = NotificationCompat.Builder(context, CANAL)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(titulo)
            .setContentText(texto)
            .setStyle(NotificationCompat.BigTextStyle().bigText(texto))
            .setContentIntent(abrir)
            .setAutoCancel(true)
            .build()
        try {
            NotificationManagerCompat.from(context).notify(1, n)
        } catch (e: SecurityException) {
            // Permissão revogada entre a checagem e o envio. Sem aviso,
            // sem crash: o app continua funcionando normalmente.
        }
    }
}

/**
 * A decisão de avisar, separada do Android.
 *
 * Fica aqui fora do Worker para ser testável na JVM: a regra de quem
 * entra no aviso e o texto que o aluno lê são a parte que pode errar de
 * verdade, e um teste que precise de emulador acaba não sendo rodado.
 */
object AvisoRegras {

    data class Aviso(val titulo: String, val texto: String)

    /**
     * Escolhe os empréstimos que merecem aviso hoje.
     *
     * Entra o que vence dentro de `diasAntes` **e também o que já está
     * atrasado**: quem esqueceu ontem precisa mais do lembrete que quem
     * vence amanhã.
     */
    fun aVencer(
        abertos: List<EmprestimoEntity>,
        hoje: LocalDate,
        diasAntes: Int
    ): List<Pair<EmprestimoEntity, LocalDate>> {
        val limite = hoje.plusDays(diasAntes.toLong())
        return abertos.mapNotNull { emp ->
            val prazo = interpretarData(emp.dataDevolucao) ?: return@mapNotNull null
            if (!prazo.isAfter(limite)) emp to prazo else null
        }
    }

    /**
     * Um livro: diz qual, porque cabe e é mais útil. Vários: diz
     * quantos, porque a notificação não comporta a lista e o aluno vai
     * abrir o app de qualquer jeito.
     */
    fun montarMensagem(
        vencendo: List<Pair<EmprestimoEntity, LocalDate>>,
        hoje: LocalDate
    ): Aviso? {
        if (vencendo.isEmpty()) return null
        if (vencendo.size == 1) {
            val (emp, prazo) = vencendo.first()
            val quando = when {
                prazo.isBefore(hoje) -> "está atrasado"
                prazo == hoje -> "vence hoje"
                prazo == hoje.plusDays(1) -> "vence amanhã"
                else -> "vence em ${java.time.temporal.ChronoUnit.DAYS.between(hoje, prazo)} dias"
            }
            return Aviso("Devolução de livro", "\"${emp.livroTitulo}\" $quando.")
        }
        // Os três casos precisam de frases diferentes. Dizer "prazo
        // chegando" com um livro já vencido no meio subestima o
        // problema, e foi o que apareceu no teste em aparelho: o título
        // avisava "Livros atrasados" e o texto falava em prazo chegando.
        val atrasados = vencendo.count { (_, prazo) -> prazo.isBefore(hoje) }
        val aVencer = vencendo.size - atrasados
        return when {
            atrasados == 0 -> Aviso(
                "Devolução de livros",
                "${vencendo.size} livros com prazo chegando. Toque para ver.")
            aVencer == 0 -> Aviso(
                "Livros atrasados",
                "${vencendo.size} livros estão atrasados. Passe na biblioteca.")
            else -> Aviso(
                "Livros atrasados",
                "${plural(atrasados, "livro atrasado", "livros atrasados")} " +
                    "e ${plural(aVencer, "outro vencendo", "outros vencendo")}. " +
                    "Passe na biblioteca.")
        }
    }

    private fun plural(n: Int, singular: String, plural: String) =
        if (n == 1) "$n $singular" else "$n $plural"

    /** O cache guarda a data como texto; aceita os formatos que aparecem. */
    fun interpretarData(texto: String): LocalDate? {
        if (texto.isBlank()) return null
        val formatos = listOf(
            DateTimeFormatter.ISO_LOCAL_DATE,
            DateTimeFormatter.ofPattern("dd/MM/yyyy")
        )
        for (f in formatos) {
            try {
                return LocalDate.parse(texto.take(10), f)
            } catch (_: Exception) {
            }
        }
        return null
    }
}

/**
 * Roda uma vez por dia e olha o cache local à procura de prazo
 * chegando. Nunca falha de forma a atrapalhar: erro devolve `success`,
 * porque um aviso perdido não justifica o WorkManager ficar tentando.
 */
class AvisoWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val ctx = applicationContext
        if (!AvisoDevolucao.ligado(ctx)) return Result.success()

        return try {
            val hoje = LocalDate.now()
            val abertos = SigbefDatabase.getDatabase(ctx)
                .emprestimoDao().listarAbertosUmaVez()
            val vencendo = AvisoRegras.aVencer(
                abertos, hoje, AvisoDevolucao.diasAntes(ctx))
            AvisoRegras.montarMensagem(vencendo, hoje)?.let {
                AvisoDevolucao.notificar(ctx, it.titulo, it.texto)
            }
            Result.success()
        } catch (e: Exception) {
            Result.success()
        }
    }
}
