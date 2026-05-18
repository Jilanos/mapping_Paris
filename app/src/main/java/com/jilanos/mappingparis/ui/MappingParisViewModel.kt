package com.jilanos.mappingparis.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.jilanos.mappingparis.data.CompletionStats
import com.jilanos.mappingparis.data.SegmentRepository
import com.jilanos.mappingparis.data.StreetSegment
import com.jilanos.mappingparis.data.completionStats
import com.jilanos.mappingparis.data.completionStatsByArrondissement
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MappingParisUiState(
    val segments: List<StreetSegment> = emptyList(),
    val completionStates: Map<String, Boolean> = emptyMap(),
    val selectedSegmentIds: Set<String> = emptySet()
) {
    val selectedSegmentId: String?
        get() = selectedSegmentIds.firstOrNull()

    val selectedSegment: StreetSegment?
        get() = segments.firstOrNull { it.id == selectedSegmentId }

    val selectedSegments: List<StreetSegment>
        get() = segments.filter { it.id in selectedSegmentIds }

    val selectedLengthMeters: Double
        get() = selectedSegments.sumOf { it.lengthMeters }

    val selectedArrondissementLabel: String
        get() {
            val arrondissements = selectedSegments.map { it.arrondissement }.distinct()
            return when (arrondissements.size) {
                0 -> "Aucun arrondissement"
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
}

class MappingParisViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = SegmentRepository(application)
    private val selectedSegmentIds = MutableStateFlow<Set<String>>(emptySet())
    private val segments = MutableStateFlow(repository.loadSegments())

    val uiState: StateFlow<MappingParisUiState> =
        combine(segments, repository.completionStates, selectedSegmentIds) { loadedSegments, states, selectedIds ->
            MappingParisUiState(
                segments = loadedSegments,
                completionStates = states,
                selectedSegmentIds = selectedIds
            )
        }.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = MappingParisUiState(segments = segments.value)
        )

    fun selectSegment(segmentId: String) {
        selectedSegmentIds.update { current ->
            if (segmentId in current) {
                current - segmentId
            } else {
                current + segmentId
            }
        }
    }

    fun addSegmentToSelection(segmentId: String) {
        selectedSegmentIds.update { current -> current + segmentId }
    }

    fun clearSelection() {
        selectedSegmentIds.update { emptySet() }
    }

    fun toggleSelectedCompletion() {
        val ids = selectedSegmentIds.value
        if (ids.isEmpty()) return
        val completed = !uiState.value.allSelectedCompleted
        viewModelScope.launch {
            repository.setCompleted(segmentIds = ids, completed = completed)
        }
    }

    fun toggleSingleCompletion(segmentId: String) {
        val current = uiState.value.completionStates[segmentId] == true
        viewModelScope.launch {
            repository.setCompleted(segmentId = segmentId, completed = !current)
        }
    }
}
