package com.jilanos.mappingparis.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.jilanos.mappingparis.data.CompletionStats
import com.jilanos.mappingparis.data.SegmentRepository
import com.jilanos.mappingparis.data.StreetSegment
import com.jilanos.mappingparis.data.completionStats
import com.jilanos.mappingparis.data.completionStatsByArrondissement
import com.jilanos.mappingparis.data.logicalRepresentatives
import java.text.Normalizer
import java.time.Instant
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

data class MappingParisUiState(
    val segments: List<StreetSegment> = emptyList(),
    val completionStates: Map<String, Boolean> = emptyMap(),
    val selectedSegmentIds: Set<String> = emptySet(),
    val mapMode: MapMode = MapMode.LIGHT,
    val filter: SegmentFilter = SegmentFilter(),
    val searchQuery: String = "",
    val mapFocus: MapFocus? = null,
    val migrationSummary: String? = null,
    val showMapDebugOverlay: Boolean = false
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

    companion object {
        fun normalize(value: String): String {
            val decomposed = Normalizer.normalize(value.lowercase(), Normalizer.Form.NFD)
            return decomposed.replace("\\p{Mn}+".toRegex(), "")
        }
    }
}

class MappingParisViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = SegmentRepository(application)
    private val selectedSegmentIds = MutableStateFlow<Set<String>>(emptySet())
    private val mapMode = MutableStateFlow(MapMode.LIGHT)
    private val filter = MutableStateFlow(SegmentFilter())
    private val searchQuery = MutableStateFlow("")
    private val mapFocus = MutableStateFlow<MapFocus?>(null)
    private val migrationSummary = MutableStateFlow<String?>(null)
    private val showMapDebugOverlay = MutableStateFlow(false)
    private val segments = MutableStateFlow(repository.loadSegments())
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
            showMapDebugOverlay
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
                showMapDebugOverlay = values[8] as Boolean
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
    }

    fun addSegmentToSelection(segmentId: String) {
        val logicalSegmentId = logicalIdFor(segmentId)
        selectedSegmentIds.update { current -> current + logicalSegmentId }
    }

    fun clearSelection() {
        selectedSegmentIds.update { emptySet() }
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
            .put("appVersion", "0.2.4")
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
}
