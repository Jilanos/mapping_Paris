package com.jilanos.mappingparis.location

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.jilanos.mappingparis.R
import org.json.JSONArray
import org.json.JSONObject

class GpsTrackingService : Service() {
    private var locationManager: LocationManager? = null
    private val listener = LocationListener { location -> handleLocation(location) }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification())
        startLocationUpdates()
        return START_STICKY
    }

    override fun onDestroy() {
        locationManager?.removeUpdates(listener)
        locationManager = null
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun startLocationUpdates() {
        if (!hasLocationPermission()) {
            stopSelf()
            return
        }

        val manager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        locationManager = manager
        val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
            .filter { provider -> runCatching { manager.isProviderEnabled(provider) }.getOrDefault(false) }

        if (providers.isEmpty()) {
            sendAvailability(false)
            return
        }

        var started = false
        providers.forEach { provider ->
            runCatching {
                @Suppress("MissingPermission")
                manager.requestLocationUpdates(
                    provider,
                    LOCATION_MIN_TIME_MS,
                    LOCATION_MIN_DISTANCE_METERS,
                    listener
                )
            }.onSuccess {
                started = true
            }
            runCatching {
                @Suppress("MissingPermission")
                manager.getLastKnownLocation(provider)
            }.getOrNull()?.let(::handleLocation)
        }

        sendAvailability(started)
        if (!started) stopSelf()
    }

    private fun handleLocation(location: Location) {
        val payload = LocationPayload(
            latitude = location.latitude,
            longitude = location.longitude,
            accuracyMeters = location.accuracy.takeIf { location.hasAccuracy() },
            capturedAtMillis = System.currentTimeMillis()
        )
        persistLocation(payload)
        sendBroadcast(
            Intent(ACTION_LOCATION_UPDATE)
                .setPackage(packageName)
                .putExtra(EXTRA_LATITUDE, payload.latitude)
                .putExtra(EXTRA_LONGITUDE, payload.longitude)
                .putExtra(EXTRA_ACCURACY, payload.accuracyMeters ?: -1f)
                .putExtra(EXTRA_CAPTURED_AT, payload.capturedAtMillis)
        )
    }

    private fun persistLocation(payload: LocationPayload) {
        val preferences = getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)
        val existing = preferences.getString(KEY_RECENT_LOCATIONS, null)
        val array = runCatching { if (existing == null) JSONArray() else JSONArray(existing) }.getOrDefault(JSONArray())
        array.put(
            JSONObject()
                .put("latitude", payload.latitude)
                .put("longitude", payload.longitude)
                .put("accuracyMeters", payload.accuracyMeters ?: JSONObject.NULL)
                .put("capturedAtMillis", payload.capturedAtMillis)
        )
        while (array.length() > MAX_RECENT_LOCATION_COUNT) {
            array.remove(0)
        }
        preferences.edit().putString(KEY_RECENT_LOCATIONS, array.toString()).apply()
    }

    private fun sendAvailability(available: Boolean) {
        sendBroadcast(
            Intent(ACTION_LOCATION_AVAILABILITY)
                .setPackage(packageName)
                .putExtra(EXTRA_AVAILABLE, available)
        )
    }

    private fun hasLocationPermission(): Boolean {
        val fineGranted = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
        val coarseGranted = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
        return fineGranted || coarseGranted
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Suivi GPS",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Suivi GPS actif pour proposer les segments parcourus."
        }
        manager.createNotificationChannel(channel)
    }

    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle("mapping Paris")
            .setContentText("Suivi GPS actif")
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private data class LocationPayload(
        val latitude: Double,
        val longitude: Double,
        val accuracyMeters: Float?,
        val capturedAtMillis: Long
    )

    companion object {
        const val ACTION_LOCATION_UPDATE = "com.jilanos.mappingparis.location.LOCATION_UPDATE"
        const val ACTION_LOCATION_AVAILABILITY = "com.jilanos.mappingparis.location.LOCATION_AVAILABILITY"
        const val EXTRA_LATITUDE = "latitude"
        const val EXTRA_LONGITUDE = "longitude"
        const val EXTRA_ACCURACY = "accuracy"
        const val EXTRA_CAPTURED_AT = "captured_at"
        const val EXTRA_AVAILABLE = "available"
        const val PREFERENCES_NAME = "mapping-paris-location"
        const val KEY_RECENT_LOCATIONS = "recent_locations"

        private const val CHANNEL_ID = "mapping_paris_gps_tracking"
        private const val NOTIFICATION_ID = 3001
        private const val LOCATION_MIN_TIME_MS = 2_500L
        private const val LOCATION_MIN_DISTANCE_METERS = 5f
        private const val MAX_RECENT_LOCATION_COUNT = 300

        fun start(context: Context) {
            val intent = Intent(context, GpsTrackingService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, GpsTrackingService::class.java))
        }

        fun consumePersistedLocations(context: Context): List<PersistedLocation> {
            val preferences = context.getSharedPreferences(PREFERENCES_NAME, Context.MODE_PRIVATE)
            val raw = preferences.getString(KEY_RECENT_LOCATIONS, null) ?: return emptyList()
            preferences.edit().remove(KEY_RECENT_LOCATIONS).apply()
            val array = runCatching { JSONArray(raw) }.getOrNull() ?: return emptyList()
            return buildList {
                for (index in 0 until array.length()) {
                    val item = array.optJSONObject(index) ?: continue
                    add(
                        PersistedLocation(
                            latitude = item.optDouble("latitude"),
                            longitude = item.optDouble("longitude"),
                            accuracyMeters = if (item.isNull("accuracyMeters")) null else item.optDouble("accuracyMeters").toFloat(),
                            capturedAtMillis = item.optLong("capturedAtMillis")
                        )
                    )
                }
            }
        }
    }
}

data class PersistedLocation(
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Float?,
    val capturedAtMillis: Long
)
