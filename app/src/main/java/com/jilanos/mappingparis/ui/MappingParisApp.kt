package com.jilanos.mappingparis.ui

import android.Manifest
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ElevatedButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarData
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.zIndex
import androidx.core.content.ContextCompat
import androidx.core.content.ContextCompat.RECEIVER_NOT_EXPORTED
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.jilanos.mappingparis.data.CompletionStats
import com.jilanos.mappingparis.data.StreetSegment
import com.jilanos.mappingparis.location.GpsTrackingService
import java.util.Locale
import kotlin.math.roundToInt
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import org.osmdroid.tileprovider.tilesource.XYTileSource
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.CustomZoomButtonsController
import org.osmdroid.views.MapView

private enum class OverlayPanel {
    NONE,
    MENU,
    SEARCH,
    FILTER,
    SETTINGS,
    STATS
}

@Composable
fun MappingParisApp(viewModel: MappingParisViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val versionLabel = remember { appVersionLabel(context) }
    var activePanel by remember { mutableStateOf(OverlayPanel.NONE) }
    var pendingImportJson by remember { mutableStateOf<String?>(null) }
    var pendingExportJson by remember { mutableStateOf<String?>(null) }
    var showResetConfirmation by remember { mutableStateOf(false) }
    var showBackgroundLocationSettingsPrompt by remember { mutableStateOf(false) }
    var mapViewRef by remember { mutableStateOf<MapView?>(null) }

    val exportLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/json")
    ) { uri: Uri? ->
        val exportJson = pendingExportJson
        pendingExportJson = null
        if (uri != null && exportJson != null) {
            context.contentResolver.openOutputStream(uri)?.bufferedWriter()?.use { writer ->
                writer.write(exportJson)
            }
            scope.launch {
                snackbarHostState.showSnackbar("Export termine")
            }
        }
    }

    val importLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri: Uri? ->
        if (uri != null) {
            pendingImportJson = context.contentResolver.openInputStream(uri)
                ?.bufferedReader()
                ?.use { it.readText() }
        }
    }

    val appSettingsLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {
        if (uiState.gpsAssistedEnabled && hasForegroundLocationPermission(context)) {
            viewModel.onGpsLoading()
        }
    }

    val locationPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        val granted = grants[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
            grants[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        if (granted) {
            viewModel.setGpsAssistedEnabled(true)
            viewModel.onGpsLoading()
            if (requiresManualBackgroundLocationPermission(context)) {
                showBackgroundLocationSettingsPrompt = true
            }
        } else {
            viewModel.onGpsPermissionDenied()
        }
    }

    fun requestGpsUse(recenterIfPossible: Boolean = false) {
        if (!hasForegroundLocationPermission(context)) {
            viewModel.setGpsAssistedEnabled(true)
            locationPermissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                )
            )
            return
        }
        viewModel.setGpsAssistedEnabled(true)
        if (recenterIfPossible) {
            viewModel.recenterOnCurrentLocation()
        } else {
            viewModel.onGpsLoading()
        }
    }

    LaunchedEffect(Unit) {
        val permissions = startupPermissionsToRequest(context)
        if (permissions.isNotEmpty()) {
            viewModel.setGpsAssistedEnabled(true)
            locationPermissionLauncher.launch(permissions.toTypedArray())
        } else if (requiresManualBackgroundLocationPermission(context)) {
            showBackgroundLocationSettingsPrompt = true
        }
    }

    ForegroundLocationTracker(
        enabled = uiState.gpsAssistedEnabled,
        permissionGranted = hasForegroundLocationPermission(context),
        onLoading = viewModel::onGpsLoading,
        onUnavailable = viewModel::onGpsUnavailable,
        onLocation = viewModel::onLocationUpdate
    )

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Box(modifier = Modifier.fillMaxSize()) {
                SegmentMap(
                    segments = uiState.visibleSegments,
                    completionStates = uiState.completionStates,
                    selectedSegmentIds = uiState.selectedSegmentIds,
                    gpsProposedSegmentIds = uiState.gpsProposedSegmentIds,
                    mapMode = uiState.mapMode,
                    mapFocus = uiState.mapFocus,
                    currentLocation = uiState.currentLocation,
                    showDebugOverlay = uiState.showMapDebugOverlay,
                    onSelectSegment = viewModel::selectSegment,
                    onLongPressSegment = viewModel::addSegmentToSelection,
                    onMapReady = { mapViewRef = it },
                    modifier = Modifier.fillMaxSize()
                )

                if (activePanel != OverlayPanel.SETTINGS && activePanel != OverlayPanel.STATS) {
                    MapTopControls(
                        activePanel = activePanel,
                        filterActive = uiState.filter.isActive,
                        gpsActive = uiState.gpsAssistedEnabled,
                        onMenu = { activePanel = if (activePanel == OverlayPanel.MENU) OverlayPanel.NONE else OverlayPanel.MENU },
                        onSearch = { activePanel = if (activePanel == OverlayPanel.SEARCH) OverlayPanel.NONE else OverlayPanel.SEARCH },
                        onFilter = { activePanel = if (activePanel == OverlayPanel.FILTER) OverlayPanel.NONE else OverlayPanel.FILTER },
                        showGps = activePanel == OverlayPanel.NONE,
                        onGps = {
                            if (!uiState.gpsAssistedEnabled || !hasForegroundLocationPermission(context)) {
                                requestGpsUse(recenterIfPossible = true)
                            } else {
                                viewModel.recenterOnCurrentLocation()
                            }
                        },
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .statusBarsPadding()
                            .zIndex(20f)
                    )
                }

                MapZoomControls(
                    onZoomIn = { mapViewRef?.controller?.zoomIn() },
                    onZoomOut = { mapViewRef?.controller?.zoomOut() },
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .navigationBarsPadding()
                        .padding(
                            end = 16.dp,
                            bottom = if (uiState.selectedSegmentIds.isNotEmpty()) 172.dp else 28.dp
                        )
                        .zIndex(18f)
                )

                when (activePanel) {
                    OverlayPanel.MENU -> MainMenu(
                        mapMode = uiState.mapMode,
                        onMapModeChange = viewModel::setMapMode,
                        onSettings = { activePanel = OverlayPanel.SETTINGS },
                        onStats = { activePanel = OverlayPanel.STATS },
                        onClose = { activePanel = OverlayPanel.NONE },
                        modifier = Modifier
                            .align(Alignment.TopStart)
                            .statusBarsPadding()
                            .padding(start = 16.dp, top = 72.dp, end = 16.dp)
                            .zIndex(19f)
                    )

                    OverlayPanel.SEARCH -> SearchPanel(
                        query = uiState.searchQuery,
                        results = uiState.searchResults,
                        onQueryChange = viewModel::updateSearchQuery,
                        onResult = { result ->
                            viewModel.focusSearchResult(result)
                            activePanel = OverlayPanel.NONE
                        },
                        onClose = { activePanel = OverlayPanel.NONE },
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .statusBarsPadding()
                            .padding(start = 16.dp, top = 72.dp, end = 16.dp)
                            .zIndex(19f)
                    )

                    OverlayPanel.FILTER -> FilterPanel(
                        filter = uiState.filter,
                        arrondissements = uiState.availableArrondissements,
                        onFilterChange = viewModel::updateFilter,
                        onClear = viewModel::clearFilter,
                        onClose = { activePanel = OverlayPanel.NONE },
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .statusBarsPadding()
                            .padding(start = 16.dp, top = 72.dp, end = 16.dp)
                            .zIndex(19f)
                    )

                    OverlayPanel.SETTINGS -> SettingsView(
                        onClose = { activePanel = OverlayPanel.MENU },
                        onExport = {
                            pendingExportJson = viewModel.buildExportJson()
                            exportLauncher.launch("mapping-paris-completion-0.3.3.json")
                        },
                        onImport = { importLauncher.launch(arrayOf("application/json", "text/*", "*/*")) },
                        onReset = { showResetConfirmation = true },
                        showDebugOverlay = uiState.showMapDebugOverlay,
                        onDebugOverlayChange = viewModel::setMapDebugOverlayEnabled,
                        gpsAssistedEnabled = uiState.gpsAssistedEnabled,
                        onGpsAssistedChange = { enabled ->
                            if (enabled) requestGpsUse() else viewModel.setGpsAssistedEnabled(false)
                        },
                        gpsMatchingStrictness = uiState.gpsMatchingStrictness,
                        onGpsMatchingStrictnessChange = viewModel::setGpsMatchingStrictness,
                        gpsCoverageThresholdPercent = uiState.gpsCoverageThresholdPercent,
                        onGpsCoverageThresholdChange = viewModel::setGpsCoverageThresholdPercent,
                        gpsAvailability = uiState.gpsAvailability,
                        versionLabel = versionLabel,
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .navigationBarsPadding()
                            .padding(16.dp)
                            .zIndex(19f)
                    )

                    OverlayPanel.STATS -> StatsView(
                        globalStats = uiState.globalStats,
                        arrondissementStats = uiState.arrondissementStats,
                        onClose = { activePanel = OverlayPanel.MENU },
                        modifier = Modifier
                            .align(Alignment.Center)
                            .zIndex(19f)
                    )

                    OverlayPanel.NONE -> Unit
                }

                if (uiState.gpsAssistedEnabled && uiState.gpsAvailability != GpsAvailability.READY) {
                    GpsStatusChip(
                        availability = uiState.gpsAvailability,
                        modifier = Modifier
                            .align(Alignment.TopCenter)
                            .statusBarsPadding()
                            .padding(top = 84.dp)
                            .zIndex(18f)
                    )
                }

                if (uiState.selectedSegmentIds.isNotEmpty()) {
                    SelectionActionBar(
                        selectedSegments = uiState.selectedSegments,
                        selectedLengthMeters = uiState.selectedLengthMeters,
                        selectedArrondissementLabel = uiState.selectedArrondissementLabel,
                        allSelectedCompleted = uiState.allSelectedCompleted,
                        gpsProposedCount = uiState.gpsProposedSegmentIds.size,
                        onToggleCompletion = {
                            val previousStates = uiState.selectedSegmentIds.associateWith {
                                uiState.completionStates[it] == true
                            }
                            val targetCompleted = !uiState.allSelectedCompleted
                            viewModel.setSelectedCompletion(targetCompleted)
                            scope.launch {
                                val result = showUndoSnackbar(
                                    snackbarHostState = snackbarHostState,
                                    message = if (targetCompleted) "Segments marques parcourus" else "Segments marques non parcourus",
                                    actionLabel = "Annuler"
                                )
                                if (result == SnackbarResult.ActionPerformed) {
                                    viewModel.restoreCompletionStates(previousStates)
                                }
                            }
                        },
                        onClearSelection = viewModel::clearSelection,
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .navigationBarsPadding()
                    )
                }

                SnackbarHost(
                    hostState = snackbarHostState,
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(12.dp)
                        .navigationBarsPadding()
                        .zIndex(30f),
                    snackbar = { data -> MappingParisSnackbar(data) }
                )
            }
        }
    }

    pendingImportJson?.let { importJson ->
        AlertDialog(
            onDismissRequest = { pendingImportJson = null },
            title = { Text("Importer la progression") },
            text = { Text("Choisir comment appliquer ce fichier a la progression locale.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        pendingImportJson = null
                        viewModel.importCompletionJson(importJson, replace = false) { result ->
                            scope.launch {
                                snackbarHostState.showSnackbar("${result.importedCount} segments importes")
                            }
                        }
                    }
                ) {
                    Text("Merge")
                }
            },
            dismissButton = {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = {
                        pendingImportJson = null
                        viewModel.importCompletionJson(importJson, replace = true) { result ->
                            scope.launch {
                                snackbarHostState.showSnackbar("${result.importedCount} segments remplaces")
                            }
                        }
                    }) {
                        Text("Replace")
                    }
                    TextButton(onClick = { pendingImportJson = null }) {
                        Text("Cancel")
                    }
                }
            }
        )
    }

    if (showResetConfirmation) {
        AlertDialog(
            onDismissRequest = { showResetConfirmation = false },
            title = { Text("Reinitialiser la progression") },
            text = { Text("Cette action efface toute la progression locale de cet appareil.") },
            confirmButton = {
                TextButton(onClick = {
                    showResetConfirmation = false
                    viewModel.resetProgress()
                    scope.launch { snackbarHostState.showSnackbar("Progression reinitialisee") }
                }) {
                    Text("Reinitialiser")
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetConfirmation = false }) {
                    Text("Annuler")
                }
            }
        )
    }

    if (showBackgroundLocationSettingsPrompt) {
        AlertDialog(
            onDismissRequest = { showBackgroundLocationSettingsPrompt = false },
            title = { Text("Autorisation GPS en arriere-plan") },
            text = {
                Text(
                    "Pour continuer le suivi quand le telephone est verrouille, ouvre les reglages de l'app et autorise la localisation en arriere-plan si l'option est disponible."
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showBackgroundLocationSettingsPrompt = false
                        appSettingsLauncher.launch(
                            Intent(
                                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                                Uri.fromParts("package", context.packageName, null)
                            )
                        )
                    }
                ) {
                    Text("Ouvrir reglages")
                }
            },
            dismissButton = {
                TextButton(onClick = { showBackgroundLocationSettingsPrompt = false }) {
                    Text("Plus tard")
                }
            }
        )
    }
}

@Composable
private fun ForegroundLocationTracker(
    enabled: Boolean,
    permissionGranted: Boolean,
    onLoading: () -> Unit,
    onUnavailable: () -> Unit,
    onLocation: (Double, Double, Float?) -> Unit
) {
    val context = LocalContext.current
    DisposableEffect(enabled, permissionGranted) {
        if (!enabled || !permissionGranted) {
            GpsTrackingService.stop(context)
            onDispose { }
        } else {
            onLoading()
            GpsTrackingService.consumePersistedLocations(context).forEach { location ->
                onLocation(location.latitude, location.longitude, location.accuracyMeters)
            }
            val receiver = object : BroadcastReceiver() {
                override fun onReceive(context: Context, intent: Intent) {
                    when (intent.action) {
                        GpsTrackingService.ACTION_LOCATION_UPDATE -> {
                            val accuracy = intent.getFloatExtra(GpsTrackingService.EXTRA_ACCURACY, -1f)
                                .takeIf { it >= 0f }
                            onLocation(
                                intent.getDoubleExtra(GpsTrackingService.EXTRA_LATITUDE, 0.0),
                                intent.getDoubleExtra(GpsTrackingService.EXTRA_LONGITUDE, 0.0),
                                accuracy
                            )
                        }
                        GpsTrackingService.ACTION_LOCATION_AVAILABILITY -> {
                            if (!intent.getBooleanExtra(GpsTrackingService.EXTRA_AVAILABLE, false)) {
                                onUnavailable()
                            }
                        }
                    }
                }
            }
            val filter = IntentFilter().apply {
                addAction(GpsTrackingService.ACTION_LOCATION_UPDATE)
                addAction(GpsTrackingService.ACTION_LOCATION_AVAILABILITY)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.registerReceiver(receiver, filter, RECEIVER_NOT_EXPORTED)
            } else {
                @Suppress("DEPRECATION")
                context.registerReceiver(receiver, filter)
            }
            GpsTrackingService.start(context)
            onDispose {
                context.unregisterReceiver(receiver)
            }
        }
    }
}

private fun hasForegroundLocationPermission(context: Context): Boolean {
    val fineGranted = ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.ACCESS_FINE_LOCATION
    ) == PackageManager.PERMISSION_GRANTED
    val coarseGranted = ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.ACCESS_COARSE_LOCATION
    ) == PackageManager.PERMISSION_GRANTED
    return fineGranted || coarseGranted
}

private fun hasNotificationPermission(context: Context): Boolean {
    return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
}

private fun hasBackgroundLocationPermission(context: Context): Boolean {
    return Build.VERSION.SDK_INT < Build.VERSION_CODES.Q ||
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_BACKGROUND_LOCATION
        ) == PackageManager.PERMISSION_GRANTED
}

private fun requiresManualBackgroundLocationPermission(context: Context): Boolean {
    return Build.VERSION.SDK_INT >= Build.VERSION_CODES.R &&
        hasForegroundLocationPermission(context) &&
        !hasBackgroundLocationPermission(context)
}

private fun startupPermissionsToRequest(context: Context): List<String> {
    val permissions = mutableListOf<String>()
    if (ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_FINE_LOCATION
        ) != PackageManager.PERMISSION_GRANTED
    ) {
        permissions += Manifest.permission.ACCESS_FINE_LOCATION
    }
    if (ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.ACCESS_COARSE_LOCATION
        ) != PackageManager.PERMISSION_GRANTED
    ) {
        permissions += Manifest.permission.ACCESS_COARSE_LOCATION
    }
    if (Build.VERSION.SDK_INT == Build.VERSION_CODES.Q && !hasBackgroundLocationPermission(context)) {
        permissions += Manifest.permission.ACCESS_BACKGROUND_LOCATION
    }
    if (!hasNotificationPermission(context)) {
        permissions += Manifest.permission.POST_NOTIFICATIONS
    }
    return permissions.distinct()
}

private fun gpsAvailabilityLabel(availability: GpsAvailability): String {
    return when (availability) {
        GpsAvailability.OFF -> "Desactive"
        GpsAvailability.LOADING -> "Recherche position"
        GpsAvailability.READY -> "Position active"
        GpsAvailability.PERMISSION_DENIED -> "Autorisation refusee"
        GpsAvailability.UNAVAILABLE -> "GPS indisponible"
    }
}

@Composable
private fun GpsStatusChip(
    availability: GpsAvailability,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(999.dp),
        color = Color(0xFF071F48).copy(alpha = 0.94f),
        contentColor = Color.White,
        tonalElevation = 6.dp,
        shadowElevation = 8.dp
    ) {
        Text(
            gpsAvailabilityLabel(availability),
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.SemiBold
        )
    }
}

private suspend fun showUndoSnackbar(
    snackbarHostState: SnackbarHostState,
    message: String,
    actionLabel: String
): SnackbarResult {
    return withTimeoutOrNull(3000) {
        snackbarHostState.showSnackbar(
            message = message,
            actionLabel = actionLabel,
            duration = SnackbarDuration.Indefinite
        )
    } ?: SnackbarResult.Dismissed
}

@Composable
private fun MappingParisSnackbar(data: SnackbarData) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = Color(0xFF071F48).copy(alpha = 0.96f),
        contentColor = Color.White,
        tonalElevation = 8.dp,
        shadowElevation = 10.dp
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                data.visuals.message,
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.bodyMedium
            )
            data.visuals.actionLabel?.let { action ->
                TextButton(onClick = data::performAction) {
                    Text(action, color = Color(0xFF2FF3C5), fontWeight = FontWeight.SemiBold)
                }
            }
        }
    }
}

@Composable
private fun MapTopControls(
    activePanel: OverlayPanel,
    filterActive: Boolean,
    gpsActive: Boolean,
    onMenu: () -> Unit,
    onSearch: () -> Unit,
    onFilter: () -> Unit,
    showGps: Boolean,
    onGps: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Row(
            modifier = Modifier.align(Alignment.TopStart),
            horizontalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            MapControlButton(
                kind = MapControlKind.MENU,
                active = activePanel == OverlayPanel.MENU,
                onClick = onMenu
            )
            MapControlButton(
                kind = MapControlKind.SEARCH,
                active = activePanel == OverlayPanel.SEARCH,
                onClick = onSearch
            )
        }
        Column(
            modifier = Modifier.align(Alignment.TopEnd),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            MapControlButton(
                kind = MapControlKind.FILTER,
                active = activePanel == OverlayPanel.FILTER || filterActive,
                onClick = onFilter
            )
            if (showGps) {
                MapControlButton(
                    kind = MapControlKind.GPS,
                    active = gpsActive,
                    onClick = onGps
                )
            }
        }
    }
}

@Composable
private fun MapZoomControls(
    onZoomIn: () -> Unit,
    onZoomOut: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(10.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        MapZoomButton(symbol = "+", onClick = onZoomIn)
        MapZoomButton(symbol = "-", onClick = onZoomOut)
    }
}

@Composable
private fun MapZoomButton(symbol: String, onClick: () -> Unit) {
    Surface(
        modifier = Modifier
            .size(48.dp)
            .clip(CircleShape)
            .clickable(onClick = onClick),
        shape = CircleShape,
        color = Color.White.copy(alpha = 0.96f),
        contentColor = Color(0xFF17324D),
        border = BorderStroke(1.dp, Color(0x33496DA6)),
        tonalElevation = 6.dp,
        shadowElevation = 8.dp
    ) {
        Box(contentAlignment = Alignment.Center) {
            Text(symbol, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun MapControlButton(
    kind: MapControlKind,
    active: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .size(52.dp)
            .clip(CircleShape)
            .clickable(onClick = onClick),
        shape = CircleShape,
        color = if (active) Color(0xFF071F48) else Color.White.copy(alpha = 0.96f),
        contentColor = if (active) Color.White else Color(0xFF17324D),
        border = BorderStroke(1.dp, if (active) Color(0xFF2FF3C5) else Color(0x33496DA6)),
        tonalElevation = 6.dp,
        shadowElevation = 8.dp
    ) {
        MapControlIcon(kind = kind, active = active)
    }
}

@Composable
private fun MapControlIcon(kind: MapControlKind, active: Boolean) {
    val color = if (active) Color.White else Color(0xFF17324D)
    val accent = if (active) Color(0xFF2FF3C5) else Color(0xFF496DA6)
    Canvas(modifier = Modifier.fillMaxSize().padding(14.dp)) {
        val stroke = 3.2f
        when (kind) {
            MapControlKind.MENU -> {
                listOf(0.25f, 0.5f, 0.75f).forEach { y ->
                    drawLine(
                        color = color,
                        start = Offset(size.width * 0.16f, size.height * y),
                        end = Offset(size.width * 0.84f, size.height * y),
                        strokeWidth = stroke,
                        cap = StrokeCap.Round
                    )
                }
            }

            MapControlKind.SEARCH -> {
                drawCircle(
                    color = color,
                    radius = size.minDimension * 0.28f,
                    center = Offset(size.width * 0.43f, size.height * 0.42f),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = stroke)
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.62f, size.height * 0.62f),
                    end = Offset(size.width * 0.86f, size.height * 0.86f),
                    strokeWidth = stroke,
                    cap = StrokeCap.Round
                )
            }

            MapControlKind.FILTER -> {
                val widths = listOf(0.68f, 0.52f, 0.36f)
                listOf(0.28f, 0.5f, 0.72f).forEachIndexed { index, y ->
                    val halfWidth = size.width * widths[index] / 2f
                    val centerX = size.width * 0.5f
                    drawLine(
                        color = if (index == 0) accent else color,
                        start = Offset(centerX - halfWidth, size.height * y),
                        end = Offset(centerX + halfWidth, size.height * y),
                        strokeWidth = stroke,
                        cap = StrokeCap.Round
                    )
                }
            }

            MapControlKind.GPS -> {
                drawCircle(
                    color = accent,
                    radius = size.minDimension * 0.08f,
                    center = Offset(size.width * 0.5f, size.height * 0.5f)
                )
                drawCircle(
                    color = color,
                    radius = size.minDimension * 0.28f,
                    center = Offset(size.width * 0.5f, size.height * 0.5f),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = stroke)
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.5f, size.height * 0.05f),
                    end = Offset(size.width * 0.5f, size.height * 0.23f),
                    strokeWidth = stroke,
                    cap = StrokeCap.Round
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.5f, size.height * 0.77f),
                    end = Offset(size.width * 0.5f, size.height * 0.95f),
                    strokeWidth = stroke,
                    cap = StrokeCap.Round
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.05f, size.height * 0.5f),
                    end = Offset(size.width * 0.23f, size.height * 0.5f),
                    strokeWidth = stroke,
                    cap = StrokeCap.Round
                )
                drawLine(
                    color = color,
                    start = Offset(size.width * 0.77f, size.height * 0.5f),
                    end = Offset(size.width * 0.95f, size.height * 0.5f),
                    strokeWidth = stroke,
                    cap = StrokeCap.Round
                )
            }
        }
    }
}

private enum class MapControlKind {
    MENU,
    SEARCH,
    FILTER,
    GPS
}

@Composable
private fun MainMenu(
    mapMode: MapMode,
    onMapModeChange: (MapMode) -> Unit,
    onSettings: () -> Unit,
    onStats: () -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Menu", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                TextButton(onClick = onClose) { Text("Fermer") }
            }
            Text("Mode carte", style = MaterialTheme.typography.labelLarge)
            Row(verticalAlignment = Alignment.CenterVertically) {
                RadioButton(selected = mapMode == MapMode.LIGHT, onClick = { onMapModeChange(MapMode.LIGHT) })
                Text("Light")
                Spacer(Modifier.width(18.dp))
                RadioButton(selected = mapMode == MapMode.BLUE, onClick = { onMapModeChange(MapMode.BLUE) })
                Text("Blue")
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onSettings) { Text("Parametres") }
                OutlinedButton(onClick = onStats) { Text("Statistiques") }
            }
        }
    }
}

@Composable
private fun SearchPanel(
    query: String,
    results: List<StreetSearchResult>,
    onQueryChange: (String) -> Unit,
    onResult: (StreetSearchResult) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Recherche rue", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                TextButton(onClick = onClose) { Text("Fermer") }
            }
            OutlinedTextField(
                value = query,
                onValueChange = onQueryChange,
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text("Nom de rue") }
            )
            Column(
                modifier = Modifier.heightIn(max = 280.dp).verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                results.forEach { result ->
                    OutlinedButton(
                        onClick = { onResult(result) },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.fillMaxWidth()) {
                            Text(result.streetName, fontWeight = FontWeight.SemiBold)
                            Text(
                                "${result.segmentCount} segments - ${result.arrondissementLabel}",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FilterPanel(
    filter: SegmentFilter,
    arrondissements: List<String>,
    onFilterChange: (SegmentFilter) -> Unit,
    onClear: () -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp).verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Filtres", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                TextButton(onClick = onClose) { Text("Fermer") }
            }
            Text("Statut", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold)
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                FilterCheckbox(
                    checked = filter.showCompleted,
                    label = "Parcourus",
                    onCheckedChange = { onFilterChange(filter.copy(showCompleted = it)) }
                )
                FilterCheckbox(
                    checked = filter.showNotCompleted,
                    label = "Non parcourus",
                    onCheckedChange = { onFilterChange(filter.copy(showNotCompleted = it)) }
                )
                FilterCheckbox(
                    checked = filter.showSelected,
                    label = "Selection",
                    onCheckedChange = { onFilterChange(filter.copy(showSelected = it)) }
                )
            }
            Text("Arrondissements", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold)
            val arrondissementOptions = (1..20).map { it.toString() }
            arrondissementOptions.chunked(5).forEach { rowItems ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    rowItems.forEach { arrondissement ->
                        CompactArrondissementCheckbox(
                            arrondissement = arrondissement,
                            checked = arrondissement in filter.arrondissements,
                            onCheckedChange = { checked ->
                                val next = if (checked) {
                                    filter.arrondissements + arrondissement
                                } else {
                                    filter.arrondissements - arrondissement
                                }
                                onFilterChange(filter.copy(arrondissements = next))
                            }
                        )
                    }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onClear) { Text("Effacer") }
                Button(onClick = onClose) { Text("Appliquer") }
            }
        }
    }
}

@Composable
private fun FilterCheckbox(
    checked: Boolean,
    label: String,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Checkbox(checked = checked, onCheckedChange = onCheckedChange)
        Text(label)
    }
}

@Composable
private fun CompactArrondissementCheckbox(
    arrondissement: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Checkbox(checked = checked, onCheckedChange = onCheckedChange)
        Text(arrondissement, style = MaterialTheme.typography.bodyMedium)
    }
}

@Composable
private fun SettingsView(
    onClose: () -> Unit,
    onExport: () -> Unit,
    onImport: () -> Unit,
    onReset: () -> Unit,
    showDebugOverlay: Boolean,
    onDebugOverlayChange: (Boolean) -> Unit,
    gpsAssistedEnabled: Boolean,
    onGpsAssistedChange: (Boolean) -> Unit,
    gpsMatchingStrictness: GpsMatchingStrictness,
    onGpsMatchingStrictnessChange: (GpsMatchingStrictness) -> Unit,
    gpsCoverageThresholdPercent: Int,
    onGpsCoverageThresholdChange: (Int) -> Unit,
    gpsAvailability: GpsAvailability,
    versionLabel: String,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(22.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            HeaderRow(title = "Progression locale", onClose = onClose)
            Button(onClick = onExport, modifier = Modifier.fillMaxWidth()) { Text("Exporter la progression") }
            OutlinedButton(onClick = onImport, modifier = Modifier.fillMaxWidth()) { Text("Importer la progression") }
            OutlinedButton(onClick = onReset, modifier = Modifier.fillMaxWidth()) { Text("Reinitialiser la progression") }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("GPS assiste", fontWeight = FontWeight.SemiBold)
                    Text(gpsAvailabilityLabel(gpsAvailability), style = MaterialTheme.typography.bodySmall, color = Color(0xFF52606D))
                }
                Switch(checked = gpsAssistedEnabled, onCheckedChange = onGpsAssistedChange)
            }
            if (gpsAssistedEnabled) {
                Text("Distance max proposition", style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.SemiBold)
                GpsMatchingStrictness.entries.forEach { strictness ->
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        RadioButton(
                            selected = gpsMatchingStrictness == strictness,
                            onClick = { onGpsMatchingStrictnessChange(strictness) }
                        )
                        Text(strictness.label)
                    }
                }
                Text(
                    "Couverture minimale: $gpsCoverageThresholdPercent%",
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold
                )
                Slider(
                    value = gpsCoverageThresholdPercent.toFloat(),
                    onValueChange = { value ->
                        val stepped = (value / 5f).roundToInt() * 5
                        onGpsCoverageThresholdChange(stepped)
                    },
                    valueRange = 30f..95f,
                    steps = 12,
                    modifier = Modifier.fillMaxWidth()
                )
                Text(
                    "Un segment est propose apres deux positions couvrant au moins cette part de sa longueur.",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF52606D)
                )
            }
            FilterCheckbox(
                checked = showDebugOverlay,
                label = "Reperes zoom carte",
                onCheckedChange = onDebugOverlayChange
            )
            Text(
                versionLabel,
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF6E7885),
                modifier = Modifier.align(Alignment.End)
            )
        }
    }
}

@Composable
private fun StatsView(
    globalStats: CompletionStats,
    arrondissementStats: Map<String, CompletionStats>,
    onClose: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxSize(),
        color = Color(0xFFF3F7FA)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            HeaderRow(title = "Statistiques", onClose = onClose)
            StatsSummaryCard(globalStats)
            Text("Par arrondissement", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                arrondissementStats
                    .toList()
                    .sortedBy { (arrondissement, _) -> arrondissement.toIntOrNull() ?: 999 }
                    .forEach { (arrondissement, stats) ->
                        ArrondissementStatsRow(arrondissement = arrondissement, stats = stats)
                    }
            }
        }
    }
}

@Composable
private fun StatsSummaryCard(stats: CompletionStats) {
    Card(shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Global", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Text(formatPercent(stats.percent), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            }
            LinearProgressIndicator(
                progress = { (stats.percent / 100.0).toFloat().coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth().height(8.dp),
                color = Color(0xFF0D8B70),
                trackColor = Color(0xFFD9E3EA)
            )
            Text(
                "${formatMeters(stats.completedMeters)} / ${formatMeters(stats.totalMeters)}",
                style = MaterialTheme.typography.bodyMedium
            )
            Text(
                "Restant: ${formatMeters((stats.totalMeters - stats.completedMeters).coerceAtLeast(0.0))}",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF52606D)
            )
        }
    }
}

@Composable
private fun ArrondissementStatsRow(arrondissement: String, stats: CompletionStats) {
    Card(shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("${arrondissement}e", fontWeight = FontWeight.SemiBold)
                Text(formatPercent(stats.percent), fontWeight = FontWeight.SemiBold)
            }
            LinearProgressIndicator(
                progress = { (stats.percent / 100.0).toFloat().coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth().height(5.dp),
                color = Color(0xFF0D8B70),
                trackColor = Color(0xFFE0E7EC)
            )
            Text(
                "${formatMeters(stats.completedMeters)} / ${formatMeters(stats.totalMeters)}",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF52606D)
            )
        }
    }
}

private fun appVersionLabel(context: Context): String {
    return try {
        val packageInfo = context.packageManager.getPackageInfo(context.packageName, 0)
        val versionName = packageInfo.versionName ?: "unknown"
        val versionCode = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
            packageInfo.longVersionCode
        } else {
            @Suppress("DEPRECATION")
            packageInfo.versionCode.toLong()
        }
        "Version $versionName, build $versionCode"
    } catch (_: Exception) {
        "Version inconnue"
    }
}

@Composable
private fun HeaderRow(title: String, onClose: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(title, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        TextButton(onClick = onClose) { Text("Retour") }
    }
}

@Composable
private fun SelectionActionBar(
    selectedSegments: List<StreetSegment>,
    selectedLengthMeters: Double,
    selectedArrondissementLabel: String,
    allSelectedCompleted: Boolean,
    gpsProposedCount: Int,
    onToggleCompletion: () -> Unit,
    onClearSelection: () -> Unit,
    modifier: Modifier = Modifier
) {
    val selectedCount = selectedSegments.size
    val segmentNames = selectedSegments
        .map { it.streetName }
        .distinct()
        .take(2)
        .joinToString(", ")
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .padding(12.dp)
            .clip(RoundedCornerShape(14.dp)),
        color = Color.White.copy(alpha = 0.96f),
        tonalElevation = 4.dp,
        shadowElevation = 4.dp
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                "$selectedCount segment${if (selectedCount > 1) "s" else ""} - ${formatMeters(selectedLengthMeters)}",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold
            )
            Text(
                "$selectedArrondissementLabel${if (segmentNames.isNotBlank()) " - $segmentNames" else ""}",
                style = MaterialTheme.typography.bodySmall
            )
            if (gpsProposedCount > 0) {
                Text(
                    "Proposition GPS: $gpsProposedCount segment${if (gpsProposedCount > 1) "s" else ""} a verifier",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF0064D6),
                    fontWeight = FontWeight.SemiBold
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onToggleCompletion) {
                    Text(if (allSelectedCompleted) "Non parcouru" else "Parcouru")
                }
                OutlinedButton(onClick = onClearSelection) {
                    Text("Deselectionner")
                }
            }
        }
    }
}

@Composable
private fun SegmentMap(
    segments: List<StreetSegment>,
    completionStates: Map<String, Boolean>,
    selectedSegmentIds: Set<String>,
    gpsProposedSegmentIds: Set<String>,
    mapMode: MapMode,
    mapFocus: MapFocus?,
    currentLocation: UserLocation?,
    showDebugOverlay: Boolean,
    onSelectSegment: (String) -> Unit,
    onLongPressSegment: (String) -> Unit,
    onMapReady: (MapView) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    AndroidView(
        modifier = modifier.navigationBarsPadding(),
        factory = {
            MapView(context).apply {
                setTileSource(CartoLightTileSource)
                setMultiTouchControls(true)
                zoomController.setVisibility(CustomZoomButtonsController.Visibility.NEVER)
                isTilesScaledToDpi = true
                setUseDataConnection(true)
                setPadding(0, 0, 0, 96)
                controller.setZoom(13.2)
                controller.setCenter(GeoPoint(48.8566, 2.3522))
                val basemapOverlay = ParisBasemapOverlay()
                val segmentOverlay = SegmentNetworkOverlay(
                    segments = segments,
                    completionStates = completionStates,
                    selectedSegmentIds = selectedSegmentIds,
                    gpsProposedSegmentIds = gpsProposedSegmentIds,
                    mapMode = mapMode,
                    showDebugOverlay = showDebugOverlay,
                    onTapSegment = onSelectSegment,
                    onLongPressSegment = onLongPressSegment
                )
                val locationOverlay = CurrentLocationOverlay(
                    location = currentLocation,
                    mapMode = mapMode
                )
                overlays.add(segmentOverlay)
                overlays.add(locationOverlay)
                tag = SegmentMapOverlayHolder(segmentOverlay, locationOverlay, basemapOverlay)
                onMapReady(this)
            }
        },
        update = { mapView ->
            val holder = mapView.tag as? SegmentMapOverlayHolder ?: return@AndroidView
            if (mapMode == MapMode.BLUE && !mapView.overlays.contains(holder.basemapOverlay)) {
                mapView.overlays.add(0, holder.basemapOverlay)
                mapView.setUseDataConnection(false)
            }
            if (mapMode == MapMode.LIGHT && mapView.overlays.contains(holder.basemapOverlay)) {
                mapView.overlays.remove(holder.basemapOverlay)
                mapView.setUseDataConnection(true)
            }
            holder.segmentOverlay.update(
                segments = segments,
                completionStates = completionStates,
                selectedSegmentIds = selectedSegmentIds,
                gpsProposedSegmentIds = gpsProposedSegmentIds,
                mapMode = mapMode,
                showDebugOverlay = showDebugOverlay,
                onTapSegment = onSelectSegment,
                onLongPressSegment = onLongPressSegment
            )
            holder.locationOverlay.update(currentLocation, mapMode)
            if (mapFocus != null && holder.lastFocusKey != mapFocus.key) {
                holder.lastFocusKey = mapFocus.key
                mapView.controller.setZoom(mapFocus.zoom)
                mapView.controller.animateTo(GeoPoint(mapFocus.latitude, mapFocus.longitude))
            }
            mapView.invalidate()
        }
    )

    DisposableEffect(Unit) {
        onDispose {
            // MapView lifecycle is owned by AndroidView for this local-first app.
        }
    }
}

private data class SegmentMapOverlayHolder(
    val segmentOverlay: SegmentNetworkOverlay,
    val locationOverlay: CurrentLocationOverlay,
    val basemapOverlay: ParisBasemapOverlay,
    var lastFocusKey: Int? = null
)

private val CartoLightTileSource = XYTileSource(
    "CartoLight",
    0,
    20,
    256,
    ".png",
    arrayOf(
        "https://a.basemaps.cartocdn.com/light_all/",
        "https://b.basemaps.cartocdn.com/light_all/",
        "https://c.basemaps.cartocdn.com/light_all/"
    )
)

private fun formatMeters(value: Double): String {
    return if (value >= 1000.0) {
        String.format(Locale.FRANCE, "%.2f km", value / 1000.0)
    } else {
        String.format(Locale.FRANCE, "%.0f m", value)
    }
}

private fun formatPercent(value: Double): String {
    return String.format(Locale.FRANCE, "%.1f %%", value)
}
