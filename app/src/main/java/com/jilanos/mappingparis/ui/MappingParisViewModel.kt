package com.jilanos.mappingparis.ui

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.jilanos.mappingparis.b2.B2ApiClient
import com.jilanos.mappingparis.b2.B2ApiException
import com.jilanos.mappingparis.b2.B2AuthStatus
import com.jilanos.mappingparis.b2.B2Health
import com.jilanos.mappingparis.b2.B2Proposal
import com.jilanos.mappingparis.b2.B2ProposalGenerationSummary
import com.jilanos.mappingparis.b2.B2ProposalStatus
import com.jilanos.mappingparis.b2.B2SyncRunSummary
import com.jilanos.mappingparis.b2.B2SyncStatus
import com.jilanos.mappingparis.b2.normalizeBackendUrl
import com.jilanos.mappingparis.data.CompletionStats
import com.jilanos.mappingparis.data.LatLon
import com.jilanos.mappingparis.data.SegmentRepository
import com.jilanos.mappingparis.data.StreetSegment
import com.jilanos.mappingparis.data.completionStats
import com.jilanos.mappingparis.data.completionStatsByArrondissement
import com.jilanos.mappingparis.data.logicalRepresentatives
import java.text.Normalizer
import java.time.Instant
import kotlin.math.cos
import kotlin.math.hypot
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

enum class MapMode {
    LIGHT,
    BLUE
}

data class MapFocus(
    val key: Int,
    val latitude: Double,
    val longitude: Double,
    val zoom: Double = 16.0
)

data class UserLocation(
    val latitude: Double,
    val longitude: Double,
    val accuracyMeters: Float?
)

enum class GpsAvailability {
    OFF,
    LOADING,
    READY,
    PERMISSION_DENIED,
    UNAVAILABLE
}

enum class GpsMatchingStrictness(val label: String, val maxDistanceMeters: Double) {
    STRICT("18 m", 18.0),
    BALANCED("28 m", 28.0),
    WIDE("42 m", 42.0)
}

data class SegmentFilter(
    val showCompleted: Boolean = false,
    val showNotCompleted: Boolean = false,
    val showSelected: Boolean = false,
    val arrondissements: Set<String> = emptySet()
) {
    val isActive: Boolean
        get() = showCompleted || showNotCompleted || showSelected ||
            arrondissements.isNotEmpty()
}

data class StreetSearchResult(
    val streetName: String,
    val arrondissementLabel: String,
    val segmentCount: Int,
    val latitude: Double,
    val longitude: Double
)

data class ImportResult(
    val importedCount: Int,
    val totalCount: Int,
    val replaced: Boolean
)

data class B2IntegrationState(
    val loading: Boolean = false,
    val error: String? = null,
    val message: String? = null,
    val health: B2Health? = null,
    val authStatus: B2AuthStatus? = null,
    val syncStatus: B2SyncStatus? = null,
    val proposalStatus: B2ProposalStatus? = null,
    val lastSyncRun: B2SyncRunSummary? = null,
    val lastProposalGeneration: B2ProposalGenerationSummary? = null
)

data class MappingParisUiState(
    val segments: List<StreetSegment> = emptyList(),
    val completionStates: Map<String, Boolean> = emptyMap(),
    val selectedSegmentIds: Set<String> = emptySet(),
    val mapMode: MapMode = MapMode.LIGHT,
    val filter: SegmentFilter = SegmentFilter(),
    val searchQuery: String = "",
    val mapFocus: MapFocus? = null,
    val migrationSummary: String? = null,
    val showMapDebugOverlay: Boolean = false,
    val gpsAssistedEnabled: Boolean = false,
    val gpsAvailability: GpsAvailability = GpsAvailability.OFF,
    val gpsMatchingStrictness: GpsMatchingStrictness = GpsMatchingStrictness.BALANCED,
    val gpsCoverageThresholdPercent: Int = 70,
    val currentLocation: UserLocation? = null,
    val gpsProposedSegmentIds: Set<String> = emptySet(),
    val backendBaseUrl: String = "",
    val b2State: B2IntegrationState = B2IntegrationState(),
    val b2Proposals: List<B2Proposal> = emptyList()
) {
    val selectedSegments: List<StreetSegment>
        get() = segments
            .filter { it.logicalSegmentId in selectedSegmentIds }
            .logicalRepresentatives()

    val selectedLengthMeters: Double
        get() = selectedSegments.sumOf { it.lengthMeters }

    val selectedArrondissementLabel: String
        get() {
            val arrondissements = selectedSegments.map { it.arrondissement }.distinct()
            return when (arrondissements.size) {
                0 -> ""
                1 -> arrondissements.first()
                else -> "Arrondissements mixtes"
            }
        }

    val allSelectedCompleted: Boolean
        get() = selectedSegmentIds.isNotEmpty() &&
            selectedSegmentIds.all { completionStates[it] == true }

    val globalStats: CompletionStats
        get() = segments.completionStats(completionStates)

    val arrondissementStats: Map<String, CompletionStats>
        get() = segments.completionStatsByArrondissement(completionStates)

    val completedLogicalIds: Set<String>
        get() = completionStates.filterValues { it }.keys

    val visibleSegments: List<StreetSegment>
        get() {
            if (!filter.isActive) return segments
            val applyCompletionFilter = filter.showCompleted xor filter.showNotCompleted
            return segments.filter { segment ->
                val completed = completionStates[segment.logicalSegmentId] == true
                val completionOk = !applyCompletionFilter ||
                    (filter.showCompleted && completed) ||
                    (filter.showNotCompleted && !completed)
                val selectedOk = !filter.showSelected || segment.logicalSegmentId in selectedSegmentIds
                val arrondissementOk = filter.arrondissements.isEmpty() ||
                    segment.arrondissement in filter.arrondissements
                completionOk && selectedOk && arrondissementOk
            }
        }

    val searchResults: List<StreetSearchResult>
        get() {
            val query = normalize(searchQuery)
            if (query.length < 2) return emptyList()
            return segments
                .groupBy { it.streetName }
                .filterKeys { normalize(it).contains(query) }
                .map { (streetName, streetSegments) ->
                    val representativeSegments = streetSegments.logicalRepresentatives()
                    val allCoordinates = representativeSegments.flatMap { it.geometry }
                    val latitude = allCoordinates.map { it.latitude }.average()
                    val longitude = allCoordinates.map { it.longitude }.average()
                    val arrondissements = representativeSegments.map { it.arrondissement }.distinct().sorted()
                    StreetSearchResult(
                        streetName = streetName,
                        arrondissementLabel = if (arrondissements.size == 1) {
                            arrondissements.first()
                        } else {
                            arrondissements.take(3).joinToString(", ")
                        },
                        segmentCount = representativeSegments.size,
                        latitude = latitude,
                        longitude = longitude
                    )
                }
                .sortedWith(
                    compareBy<StreetSearchResult> { !normalize(it.streetName).startsWith(query) }
                        .thenBy { it.streetName.length }
                        .thenBy { it.streetName }
                )
                .take(12)
        }

    val availableArrondissements: List<String>
        get() = segments.map { it.arrondissement }.distinct().sortedBy { it.toIntOrNull() ?: 999 }

    val b2ProposedSegmentIds: Set<String>
        get() {
            if (b2Proposals.isEmpty()) return emptySet()
            val logicalIds = segments.map { it.logicalSegmentId }.toSet()
            val visualToLogical = segments.associate { it.id to it.logicalSegmentId }
            return b2Proposals
                .filter { it.status == "proposed" }
                .mapNotNull { proposal ->
                    when {
                        proposal.logicalSegmentId in logicalIds -> proposal.logicalSegmentId
                        proposal.segmentId in visualToLogical -> visualToLogical[proposal.segmentId]
                        else -> null
                    }
                }
                .toSet()
        }

    companion object {
        fun normalize(value: String): String {
            val decomposed = Normalizer.normalize(value.lowercase(), Normalizer.Form.NFD)
            return decomposed.replace("\\p{Mn}+".toRegex(), "")
        }
    }
}

class MappingParisViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = SegmentRepository(application)
    private val preferences = application.getSharedPreferences("mapping-paris-settings", Context.MODE_PRIVATE)
    private val selectedSegmentIds = MutableStateFlow<Set<String>>(emptySet())
    private val mapMode = MutableStateFlow(MapMode.LIGHT)
    private val filter = MutableStateFlow(SegmentFilter())
    private val searchQuery = MutableStateFlow("")
    private val mapFocus = MutableStateFlow<MapFocus?>(null)
    private val migrationSummary = MutableStateFlow<String?>(null)
    private val showMapDebugOverlay = MutableStateFlow(false)
    private val gpsAssistedEnabled = MutableStateFlow(preferences.getBoolean(KEY_GPS_ASSISTED_ENABLED, false))
    private val gpsAvailability = MutableStateFlow(
        if (gpsAssistedEnabled.value) GpsAvailability.LOADING else GpsAvailability.OFF
    )
    private val gpsMatchingStrictness = MutableStateFlow(
        GpsMatchingStrictness.entries.firstOrNull {
            it.name == preferences.getString(KEY_GPS_MATCHING_STRICTNESS, null)
        } ?: GpsMatchingStrictness.BALANCED
    )
    private val gpsCoverageThresholdPercent = MutableStateFlow(
        preferences.getInt(KEY_GPS_COVERAGE_THRESHOLD_PERCENT, DEFAULT_GPS_COVERAGE_THRESHOLD_PERCENT)
            .coerceIn(MIN_GPS_COVERAGE_THRESHOLD_PERCENT, MAX_GPS_COVERAGE_THRESHOLD_PERCENT)
    )
    private val currentLocation = MutableStateFlow<UserLocation?>(null)
    private val gpsProposedSegmentIds = MutableStateFlow<Set<String>>(emptySet())
    private val backendBaseUrl = MutableStateFlow(preferences.getString(KEY_BACKEND_BASE_URL, "").orEmpty())
    private val b2State = MutableStateFlow(B2IntegrationState())
    private val b2Proposals = MutableStateFlow<List<B2Proposal>>(emptyList())
    private val segments = MutableStateFlow(repository.loadSegments())
    private val gpsPath = mutableListOf<LatLon>()
    private val dismissedGpsProposalIds = mutableSetOf<String>()
    private var focusCounter = 0

    val uiState: StateFlow<MappingParisUiState> =
        combine(
            segments,
            repository.completionStates,
            selectedSegmentIds,
            mapMode,
            filter,
            searchQuery,
            mapFocus,
            migrationSummary,
            showMapDebugOverlay,
            gpsAssistedEnabled,
            gpsAvailability,
            gpsMatchingStrictness,
            gpsCoverageThresholdPercent,
            currentLocation,
            gpsProposedSegmentIds,
            backendBaseUrl,
            b2State,
            b2Proposals
        ) { values ->
            @Suppress("UNCHECKED_CAST")
            MappingParisUiState(
                segments = values[0] as List<StreetSegment>,
                completionStates = values[1] as Map<String, Boolean>,
                selectedSegmentIds = values[2] as Set<String>,
                mapMode = values[3] as MapMode,
                filter = values[4] as SegmentFilter,
                searchQuery = values[5] as String,
                mapFocus = values[6] as MapFocus?,
                migrationSummary = values[7] as String?,
                showMapDebugOverlay = values[8] as Boolean,
                gpsAssistedEnabled = values[9] as Boolean,
                gpsAvailability = values[10] as GpsAvailability,
                gpsMatchingStrictness = values[11] as GpsMatchingStrictness,
                gpsCoverageThresholdPercent = values[12] as Int,
                currentLocation = values[13] as UserLocation?,
                gpsProposedSegmentIds = values[14] as Set<String>,
                backendBaseUrl = values[15] as String,
                b2State = values[16] as B2IntegrationState,
                b2Proposals = values[17] as List<B2Proposal>
            )
        }.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = MappingParisUiState(segments = segments.value)
        )

    init {
        viewModelScope.launch {
            val result = repository.migrateVisualRowsToLogicalIds(segments.value)
            if (result.migratedRows > 0 || result.removedRows > 0) {
                migrationSummary.value =
                    "Migration: ${result.migratedRows} groupes logiques restaures"
            }
        }
    }

    fun selectSegment(segmentId: String) {
        val logicalSegmentId = logicalIdFor(segmentId)
        selectedSegmentIds.update { current ->
            if (logicalSegmentId in current) current - logicalSegmentId else current + logicalSegmentId
        }
        if (logicalSegmentId in gpsProposedSegmentIds.value) {
            dismissedGpsProposalIds += logicalSegmentId
            gpsProposedSegmentIds.update { it - logicalSegmentId }
        }
    }

    fun addSegmentToSelection(segmentId: String) {
        val logicalSegmentId = logicalIdFor(segmentId)
        selectedSegmentIds.update { current -> current + logicalSegmentId }
    }

    fun clearSelection() {
        selectedSegmentIds.update { emptySet() }
        gpsProposedSegmentIds.update { emptySet() }
        dismissedGpsProposalIds.clear()
    }

    fun setSelectedCompletion(completed: Boolean) {
        val ids = selectedSegmentIds.value
        if (ids.isEmpty()) return
        viewModelScope.launch {
            repository.setCompleted(segmentIds = ids, completed = completed)
            clearSelection()
        }
    }

    fun restoreCompletionStates(states: Map<String, Boolean>) {
        viewModelScope.launch {
            repository.restoreCompletionStates(states)
        }
    }

    fun setMapMode(mode: MapMode) {
        mapMode.value = mode
    }

    fun setMapDebugOverlayEnabled(enabled: Boolean) {
        showMapDebugOverlay.value = enabled
    }

    fun setGpsAssistedEnabled(enabled: Boolean) {
        preferences.edit().putBoolean(KEY_GPS_ASSISTED_ENABLED, enabled).apply()
        gpsAssistedEnabled.value = enabled
        if (enabled) {
            gpsAvailability.value = GpsAvailability.LOADING
        } else {
            gpsAvailability.value = GpsAvailability.OFF
            currentLocation.value = null
            gpsPath.clear()
            dismissedGpsProposalIds.clear()
            gpsProposedSegmentIds.value = emptySet()
        }
    }

    fun setGpsMatchingStrictness(strictness: GpsMatchingStrictness) {
        preferences.edit().putString(KEY_GPS_MATCHING_STRICTNESS, strictness.name).apply()
        gpsMatchingStrictness.value = strictness
        rebuildGpsProposals()
    }

    fun setGpsCoverageThresholdPercent(percent: Int) {
        val normalized = percent.coerceIn(
            MIN_GPS_COVERAGE_THRESHOLD_PERCENT,
            MAX_GPS_COVERAGE_THRESHOLD_PERCENT
        )
        preferences.edit().putInt(KEY_GPS_COVERAGE_THRESHOLD_PERCENT, normalized).apply()
        gpsCoverageThresholdPercent.value = normalized
        rebuildGpsProposals()
    }

    fun onGpsPermissionDenied() {
        gpsAvailability.value = GpsAvailability.PERMISSION_DENIED
        currentLocation.value = null
    }

    fun onGpsUnavailable() {
        gpsAvailability.value = GpsAvailability.UNAVAILABLE
        currentLocation.value = null
    }

    fun onGpsLoading() {
        if (gpsAssistedEnabled.value) gpsAvailability.value = GpsAvailability.LOADING
    }

    fun onLocationUpdate(latitude: Double, longitude: Double, accuracyMeters: Float?) {
        if (!gpsAssistedEnabled.value) return
        currentLocation.value = UserLocation(latitude, longitude, accuracyMeters)
        gpsAvailability.value = GpsAvailability.READY
        val point = LatLon(latitude, longitude)
        val previous = gpsPath.lastOrNull()
        if (previous == null || distanceMeters(previous, point) >= GPS_PATH_MIN_STEP_METERS) {
            gpsPath += point
            rebuildGpsProposals()
        }
    }

    fun recenterOnCurrentLocation() {
        val location = currentLocation.value
        if (location == null) {
            gpsAvailability.value = if (gpsAssistedEnabled.value) GpsAvailability.LOADING else GpsAvailability.OFF
            return
        }
        focusCounter += 1
        mapFocus.value = MapFocus(
            key = focusCounter,
            latitude = location.latitude,
            longitude = location.longitude,
            zoom = 17.0
        )
    }

    fun updateFilter(newFilter: SegmentFilter) {
        filter.value = newFilter
    }

    fun clearFilter() {
        filter.value = SegmentFilter()
    }

    fun updateSearchQuery(query: String) {
        searchQuery.value = query
    }

    fun focusSearchResult(result: StreetSearchResult) {
        focusCounter += 1
        mapFocus.value = MapFocus(
            key = focusCounter,
            latitude = result.latitude,
            longitude = result.longitude
        )
    }

    fun buildExportJson(): String {
        val completedIds = uiState.value.completedLogicalIds.sorted()
        return JSONObject()
            .put("schema", "mapping-paris-completion-v1")
            .put("appVersion", "0.3.3")
            .put("exportedAt", Instant.now().toString())
            .put("completedLogicalSegmentIds", JSONArray(completedIds))
            .put("completedCount", completedIds.size)
            .toString(2)
    }

    fun importCompletionJson(rawJson: String, replace: Boolean, onResult: (ImportResult) -> Unit) {
        val importedIds = parseImportedIds(rawJson)
        viewModelScope.launch {
            if (replace) {
                repository.replaceCompleted(importedIds)
            } else {
                repository.mergeCompleted(importedIds)
            }
            onResult(
                ImportResult(
                    importedCount = importedIds.size,
                    totalCount = uiState.value.completedLogicalIds.size,
                    replaced = replace
                )
            )
        }
    }

    fun resetProgress() {
        viewModelScope.launch {
            repository.resetProgress()
            clearSelection()
        }
    }

    fun setBackendBaseUrl(rawUrl: String) {
        val normalized = normalizeBackendUrl(rawUrl)
        if (normalized == null) {
            b2State.update { it.copy(error = "URL invalide: utiliser http:// ou https://") }
            return
        }
        preferences.edit().putString(KEY_BACKEND_BASE_URL, normalized).apply()
        backendBaseUrl.value = normalized
        b2State.update { it.copy(error = null, message = if (normalized.isBlank()) "Backend B2 non configure" else "URL backend enregistree") }
    }

    fun refreshB2Status() {
        viewModelScope.launch {
            runB2Operation("Statut B2 actualise") { client ->
                val health = client.getHealth()
                val authStatus = client.getAuthStatus()
                val syncStatus = client.getSyncStatus()
                val proposalStatus = client.getProposalStatus()
                b2State.update {
                    it.copy(
                        health = health,
                        authStatus = authStatus,
                        syncStatus = syncStatus,
                        proposalStatus = proposalStatus
                    )
                }
            }
        }
    }

    fun testB2Backend() {
        viewModelScope.launch {
            runB2Operation("Backend B2 joignable") { client ->
                val health = client.getHealth()
                b2State.update { it.copy(health = health) }
            }
        }
    }

    fun triggerB2StravaSync() {
        viewModelScope.launch {
            runB2Operation("Synchronisation Strava terminee") { client ->
                val syncRun = client.triggerStravaSync()
                val syncStatus = client.getSyncStatus()
                b2State.update { it.copy(lastSyncRun = syncRun, syncStatus = syncStatus) }
            }
        }
    }

    fun triggerB2ProposalGeneration() {
        viewModelScope.launch {
            runB2Operation("Generation des propositions terminee") { client ->
                val summary = client.triggerProposalGeneration()
                val proposalStatus = client.getProposalStatus()
                b2State.update { it.copy(lastProposalGeneration = summary, proposalStatus = proposalStatus) }
            }
        }
    }

    fun loadB2Proposals() {
        viewModelScope.launch {
            runB2Operation("Propositions chargees") { client ->
                val proposals = client.getProposals(status = "proposed")
                b2Proposals.value = proposals
                b2State.update { it.copy(proposalStatus = client.getProposalStatus()) }
            }
        }
    }

    fun acceptB2Proposal(proposalId: Int) {
        viewModelScope.launch {
            runB2Operation("Proposition acceptee cote backend") { client ->
                client.acceptProposal(proposalId)
                b2Proposals.value = client.getProposals(status = "proposed")
                b2State.update { it.copy(proposalStatus = client.getProposalStatus()) }
            }
        }
    }

    fun dismissB2Proposal(proposalId: Int) {
        viewModelScope.launch {
            runB2Operation("Proposition ignoree") { client ->
                client.dismissProposal(proposalId)
                b2Proposals.value = client.getProposals(status = "proposed")
                b2State.update { it.copy(proposalStatus = client.getProposalStatus()) }
            }
        }
    }

    private suspend fun runB2Operation(
        successMessage: String,
        block: suspend (B2ApiClient) -> Unit
    ) {
        val client = b2ClientOrNull()
        if (client == null) {
            b2State.update { it.copy(loading = false, error = "Configure d'abord l'URL backend B2", message = null) }
            return
        }
        b2State.update { it.copy(loading = true, error = null, message = null) }
        try {
            block(client)
            b2State.update { it.copy(loading = false, error = null, message = successMessage) }
        } catch (exception: B2ApiException) {
            b2State.update { it.copy(loading = false, error = exception.message ?: "Erreur backend B2", message = null) }
        } catch (exception: Exception) {
            b2State.update { it.copy(loading = false, error = exception.message ?: "Erreur inattendue B2", message = null) }
        }
    }

    private fun b2ClientOrNull(): B2ApiClient? {
        val normalized = normalizeBackendUrl(backendBaseUrl.value) ?: return null
        return normalized.takeIf { it.isNotBlank() }?.let(::B2ApiClient)
    }

    private fun parseImportedIds(rawJson: String): Set<String> {
        val root = JSONObject(rawJson)
        val array = when {
            root.has("completedLogicalSegmentIds") -> root.getJSONArray("completedLogicalSegmentIds")
            root.has("validatedSegmentIds") -> root.getJSONArray("validatedSegmentIds")
            else -> JSONArray()
        }
        return buildSet {
            for (index in 0 until array.length()) {
                val value = array.optString(index)
                if (value.isNotBlank()) add(value)
            }
        }
    }

    private fun logicalIdFor(segmentId: String): String {
        return segments.value.firstOrNull { it.id == segmentId }?.logicalSegmentId ?: segmentId
    }

    private fun rebuildGpsProposals() {
        if (!gpsAssistedEnabled.value || gpsPath.isEmpty()) {
            gpsProposedSegmentIds.value = emptySet()
            return
        }

        val previousProposals = gpsProposedSegmentIds.value
        val maxDistance = gpsMatchingStrictness.value.maxDistanceMeters
        val thresholdRatio = gpsCoverageThresholdPercent.value / 100.0
        val proposed = segments.value
            .logicalRepresentatives()
            .filter { segment ->
                completionStatesSnapshot()[segment.logicalSegmentId] != true &&
                    segment.logicalSegmentId !in dismissedGpsProposalIds &&
                    segment.geometry.size >= 2 &&
                    segmentHasRequiredGpsCoverage(
                        segment = segment,
                        gpsPoints = gpsPath,
                        maxDistanceMeters = maxDistance,
                        thresholdRatio = thresholdRatio
                    )
            }
            .map { it.logicalSegmentId }
            .toSet()

        gpsProposedSegmentIds.value = proposed
        selectedSegmentIds.update { current -> (current - previousProposals) + proposed }
    }

    private fun completionStatesSnapshot(): Map<String, Boolean> = uiState.value.completionStates

    override fun onCleared() {
        gpsPath.clear()
        dismissedGpsProposalIds.clear()
        super.onCleared()
    }

    private companion object {
        const val KEY_GPS_ASSISTED_ENABLED = "gps_assisted_enabled"
        const val KEY_GPS_MATCHING_STRICTNESS = "gps_matching_strictness"
        const val KEY_GPS_COVERAGE_THRESHOLD_PERCENT = "gps_coverage_threshold_percent"
        const val KEY_BACKEND_BASE_URL = "b2_backend_base_url"
        const val GPS_PATH_MIN_STEP_METERS = 12.0
        const val DEFAULT_GPS_COVERAGE_THRESHOLD_PERCENT = 70
        const val MIN_GPS_COVERAGE_THRESHOLD_PERCENT = 30
        const val MAX_GPS_COVERAGE_THRESHOLD_PERCENT = 95
    }
}

private fun segmentHasRequiredGpsCoverage(
    segment: StreetSegment,
    gpsPoints: List<LatLon>,
    maxDistanceMeters: Double,
    thresholdRatio: Double
): Boolean {
    if (gpsPoints.size < 2 || segment.geometry.size < 2) return false
    val projections = gpsPoints.mapNotNull { point ->
        projectPointOnPolylineMeters(point, segment.geometry)
            ?.takeIf { it.distanceToLineMeters <= maxDistanceMeters }
            ?.projectedDistanceMeters
    }
    if (projections.size < 2) return false
    val minProjection = projections.minOrNull() ?: return false
    val maxProjection = projections.maxOrNull() ?: return false
    val segmentLength = maxOf(segment.lengthMeters, polylineLengthMeters(segment.geometry))
    if (segmentLength <= 0.0) return false
    return (maxProjection - minProjection) / segmentLength >= thresholdRatio
}

private fun projectPointOnPolylineMeters(point: LatLon, geometry: List<LatLon>): PolylineProjection? {
    var nearest: PolylineProjection? = null
    var distanceBeforeSegment = 0.0
    for (index in 0 until geometry.lastIndex) {
        val start = geometry[index]
        val end = geometry[index + 1]
        val segmentLength = distanceMeters(start, end)
        val projection = projectPointOnSegmentMeters(
            point = point,
            start = start,
            end = end,
            distanceBeforeSegment = distanceBeforeSegment
        )
        if (nearest == null || projection.distanceToLineMeters < nearest.distanceToLineMeters) {
            nearest = projection
        }
        distanceBeforeSegment += segmentLength
    }
    return nearest
}

private fun projectPointOnSegmentMeters(
    point: LatLon,
    start: LatLon,
    end: LatLon,
    distanceBeforeSegment: Double
): PolylineProjection {
    val originLat = point.latitude
    val originLon = point.longitude
    val px = 0.0
    val py = 0.0
    val sx = longitudeMeters(start.longitude - originLon, originLat)
    val sy = latitudeMeters(start.latitude - originLat)
    val ex = longitudeMeters(end.longitude - originLon, originLat)
    val ey = latitudeMeters(end.latitude - originLat)
    val dx = ex - sx
    val dy = ey - sy
    val segmentLength = hypot(dx, dy)
    if (segmentLength < 0.001) {
        return PolylineProjection(
            distanceToLineMeters = hypot(sx - px, sy - py),
            projectedDistanceMeters = distanceBeforeSegment
        )
    }
    val t = (((px - sx) * dx) + ((py - sy) * dy)) / ((dx * dx) + (dy * dy))
    val clamped = t.coerceIn(0.0, 1.0)
    val projectedX = sx + clamped * dx
    val projectedY = sy + clamped * dy
    return PolylineProjection(
        distanceToLineMeters = hypot(projectedX - px, projectedY - py),
        projectedDistanceMeters = distanceBeforeSegment + (segmentLength * clamped)
    )
}

private fun polylineLengthMeters(geometry: List<LatLon>): Double {
    var length = 0.0
    for (index in 0 until geometry.lastIndex) {
        length += distanceMeters(geometry[index], geometry[index + 1])
    }
    return length
}

private fun distanceMeters(start: LatLon, end: LatLon): Double {
    val dy = latitudeMeters(end.latitude - start.latitude)
    val dx = longitudeMeters(end.longitude - start.longitude, (start.latitude + end.latitude) / 2.0)
    return hypot(dx, dy)
}

private fun latitudeMeters(deltaLatitude: Double): Double = deltaLatitude * 111_320.0

private fun longitudeMeters(deltaLongitude: Double, latitude: Double): Double {
    return deltaLongitude * 111_320.0 * cos(Math.toRadians(latitude))
}

private data class PolylineProjection(
    val distanceToLineMeters: Double,
    val projectedDistanceMeters: Double
)
