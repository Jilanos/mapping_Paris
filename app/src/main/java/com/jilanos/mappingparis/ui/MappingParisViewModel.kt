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
    val selectedSegmentId: String? = null
) {
    val selectedSegment: StreetSegment?
        get() = segments.firstOrNull { it.id == selectedSegmentId }

    val globalStats: CompletionStats
        get() = segments.completionStats(completionStates)

    val arrondissementStats: Map<String, CompletionStats>
        get() = segments.completionStatsByArrondissement(completionStates)
}

class MappingParisViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = SegmentRepository(application)
    private val selectedSegmentId = MutableStateFlow<String?>(null)
    private val segments = MutableStateFlow(repository.loadSegments())

    val uiState: StateFlow<MappingParisUiState> =
        combine(segments, repository.completionStates, selectedSegmentId) { loadedSegments, states, selectedId ->
            MappingParisUiState(
                segments = loadedSegments,
                completionStates = states,
                selectedSegmentId = selectedId
            )
        }.stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = MappingParisUiState(segments = segments.value)
        )

    fun selectSegment(segmentId: String) {
        selectedSegmentId.update { segmentId }
    }

    fun toggleSelectedCompletion() {
        val id = selectedSegmentId.value ?: return
        val current = uiState.value.completionStates[id] == true
        viewModelScope.launch {
            repository.setCompleted(segmentId = id, completed = !current)
        }
    }
}
