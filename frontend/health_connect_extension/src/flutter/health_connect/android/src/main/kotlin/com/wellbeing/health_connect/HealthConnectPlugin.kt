package com.wellbeing.health_connect

import android.app.Activity
import android.content.Context
import android.content.Intent
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.PermissionController
import androidx.health.connect.client.permission.HealthPermission
import androidx.health.connect.client.records.ExerciseSessionRecord
import androidx.health.connect.client.records.HeartRateRecord
import androidx.health.connect.client.records.HydrationRecord
import androidx.health.connect.client.records.SleepSessionRecord
import androidx.health.connect.client.request.ReadRecordsRequest
import androidx.health.connect.client.time.TimeRangeFilter
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.embedding.engine.plugins.activity.ActivityAware
import io.flutter.embedding.engine.plugins.activity.ActivityPluginBinding
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.PluginRegistry
import java.time.Duration
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class HealthConnectPlugin : FlutterPlugin, MethodChannel.MethodCallHandler, ActivityAware,
    PluginRegistry.ActivityResultListener {
    private lateinit var context: Context
    private var activity: Activity? = null
    private var channel: MethodChannel? = null
    private var pendingResult: MethodChannel.Result? = null
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val permissionContract =
        PermissionController.createRequestPermissionResultContract(PROVIDER_PACKAGE)
    private val permissions = setOf(
        HealthPermission.getReadPermission(SleepSessionRecord::class),
        HealthPermission.getReadPermission(ExerciseSessionRecord::class),
        HealthPermission.getReadPermission(HeartRateRecord::class),
        HealthPermission.getReadPermission(HydrationRecord::class),
    )

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        context = binding.applicationContext
        channel = MethodChannel(binding.binaryMessenger, "com.wellbeing.tracker/health_connect")
            .also { it.setMethodCallHandler(this) }
    }

    override fun onMethodCall(call: MethodCall, result: MethodChannel.Result) {
        if (call.method != "sync") {
            result.notImplemented()
            return
        }
        if (pendingResult != null) {
            result.error("SYNC_IN_PROGRESS", "Sinkronisasi masih berlangsung.", null)
            return
        }

        when (HealthConnectClient.getSdkStatus(context, PROVIDER_PACKAGE)) {
            HealthConnectClient.SDK_AVAILABLE -> requestAccessOrRead(result)
            HealthConnectClient.SDK_UNAVAILABLE_PROVIDER_UPDATE_REQUIRED ->
                result.error("PROVIDER_UPDATE_REQUIRED", "Pasang atau perbarui Google Health Connect.", null)
            else -> result.error("PROVIDER_UNAVAILABLE", "Google Health Connect tidak tersedia di perangkat ini.", null)
        }
    }

    private fun requestAccessOrRead(result: MethodChannel.Result) {
        val host = activity
        if (host == null) {
            result.error("NO_ACTIVITY", "Tidak dapat membuka izin Health Connect.", null)
            return
        }

        scope.launch {
            try {
                val client = HealthConnectClient.getOrCreate(context, PROVIDER_PACKAGE)
                val granted = withContext(Dispatchers.IO) {
                    client.permissionController.getGrantedPermissions()
                }
                if (granted.containsAll(permissions)) {
                    readData(result, granted)
                } else {
                    pendingResult = result
                    try {
                        val intent = permissionContract.createIntent(host, permissions)
                        host.startActivityForResult(intent, REQUEST_CODE)
                    } catch (error: Exception) {
                        pendingResult = null
                        result.error("PERMISSION_REQUEST_FAILED", error.message ?: "Gagal membuka izin Health Connect.", null)
                    }
                }
            } catch (error: Exception) {
                result.error("HEALTH_CONNECT_ERROR", error.message ?: "Gagal meminta izin Health Connect.", null)
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Boolean {
        if (requestCode != REQUEST_CODE) return false

        val result = pendingResult
        pendingResult = null
        if (result == null) return true

        val granted = permissionContract.parseResult(resultCode, data)
        if (granted.isEmpty()) {
            result.error("PERMISSION_DENIED", "Izin data kesehatan belum diberikan.", null)
        } else {
            readData(result, granted)
        }
        return true
    }

    private fun readData(result: MethodChannel.Result, granted: Set<String>) {
        scope.launch {
            try {
                val data = withContext(Dispatchers.IO) { queryToday(granted) }
                result.success(data)
            } catch (error: Exception) {
                result.error("READ_FAILED", error.message ?: "Gagal membaca data kesehatan.", null)
            }
        }
    }

    private suspend fun queryToday(granted: Set<String>): Map<String, Any> {
        val client = HealthConnectClient.getOrCreate(context, PROVIDER_PACKAGE)
        val zone = ZoneId.systemDefault()
        val start = LocalDate.now(zone).atStartOfDay(zone).toInstant()
        val end = Instant.now()
        val range = TimeRangeFilter.between(start, end)
        val values = mutableMapOf<String, Any>()

        if (permissionsFor(SleepSessionRecord::class) in granted) {
            val sleepStart = start.minus(Duration.ofHours(6))
            val sleepRange = TimeRangeFilter.between(sleepStart, end)
            val sleep = client.readRecords(ReadRecordsRequest(SleepSessionRecord::class, sleepRange))
                .records.sumOf { session ->
                    val from = maxOf(session.startTime, sleepStart)
                    val to = minOf(session.endTime, end)
                    if (to.isAfter(from)) Duration.between(from, to).toMinutes() else 0L
                }
            if (sleep > 0) values["sleep"] = Math.round(sleep / 60.0 * 10.0) / 10.0
        }

        if (permissionsFor(ExerciseSessionRecord::class) in granted) {
            val exercise = client.readRecords(ReadRecordsRequest(ExerciseSessionRecord::class, range))
                .records.sumOf { session ->
                    val from = maxOf(session.startTime, start)
                    val to = minOf(session.endTime, end)
                    if (to.isAfter(from)) Duration.between(from, to).toMinutes() else 0L
                }
            if (exercise > 0) values["exercise"] = exercise
        }

        if (permissionsFor(HydrationRecord::class) in granted) {
            val hydration = client.readRecords(ReadRecordsRequest(HydrationRecord::class, range))
                .records.sumOf { it.volume.inLiters }
            if (hydration > 0.0) values["water"] = Math.round(hydration * 4.0)
        }

        if (permissionsFor(HeartRateRecord::class) in granted) {
            val heartRates = client.readRecords(ReadRecordsRequest(HeartRateRecord::class, range))
                .records.flatMap { it.samples }.map { it.beatsPerMinute }
            if (heartRates.isNotEmpty()) {
                values["heart_rate"] = heartRates.average().toInt()
            }
        }

        return mapOf("ok" to true, "data" to values)
    }

    private fun permissionsFor(record: kotlin.reflect.KClass<out androidx.health.connect.client.records.Record>) =
        HealthPermission.getReadPermission(record)

    override fun onAttachedToActivity(binding: ActivityPluginBinding) {
        activity = binding.activity
        binding.addActivityResultListener(this)
    }

    override fun onDetachedFromActivityForConfigChanges() {
        activity = null
    }

    override fun onReattachedToActivityForConfigChanges(binding: ActivityPluginBinding) {
        onAttachedToActivity(binding)
    }

    override fun onDetachedFromActivity() {
        activity = null
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel?.setMethodCallHandler(null)
        channel = null
        pendingResult?.error("PLUGIN_DETACHED", "Integrasi Health Connect ditutup.", null)
        pendingResult = null
    }

    companion object {
        private const val REQUEST_CODE = 7462
        private const val PROVIDER_PACKAGE = "com.google.android.apps.healthdata"
    }
}
