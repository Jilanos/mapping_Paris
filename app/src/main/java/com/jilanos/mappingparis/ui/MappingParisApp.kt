package com.jilanos.mappingparis.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.jilanos.mappingparis.data.CompletionStats
import com.jilanos.mappingparis.data.StreetSegment
import java.util.Locale
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView

@Composable
fun MappingParisApp(viewModel: MappingParisViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Box(modifier = Modifier.fillMaxSize()) {
                SegmentMap(
                    segments = uiState.segments,
                    completionStates = uiState.completionStates,
                    selectedSegmentIds = uiState.selectedSegmentIds,
                    onSelectSegment = viewModel::selectSegment,
                    onLongPressSegment = viewModel::addSegmentToSelection,
                    modifier = Modifier.fillMaxSize()
                )

                Column(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .fillMaxWidth()
                        .background(
                            Brush.verticalGradient(
                                0f to androidx.compose.ui.graphics.Color.Transparent,
                                0.18f to androidx.compose.ui.graphics.Color.White.copy(alpha = 0.94f),
                                1f to androidx.compose.ui.graphics.Color.White
                            )
                        )
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    SelectedSegmentPanel(
                        selectedSegments = uiState.selectedSegments,
                        selectedLengthMeters = uiState.selectedLengthMeters,
                        selectedArrondissementLabel = uiState.selectedArrondissementLabel,
                        allSelectedCompleted = uiState.allSelectedCompleted,
                        onToggleCompletion = viewModel::toggleSelectedCompletion,
                        onClearSelection = viewModel::clearSelection
                    )
                    StatsPanel(
                        globalStats = uiState.globalStats,
                        arrondissementStats = uiState.arrondissementStats
                    )
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
    onSelectSegment: (String) -> Unit,
    onLongPressSegment: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    AndroidView(
        modifier = modifier,
        factory = {
            MapView(context).apply {
                setMultiTouchControls(true)
                setUseDataConnection(false)
                overlayManager.tilesOverlay.isEnabled = false
                controller.setZoom(13.2)
                controller.setCenter(GeoPoint(48.8566, 2.3522))
                val segmentOverlay = SegmentNetworkOverlay(
                    segments = segments,
                    completionStates = completionStates,
                    selectedSegmentIds = selectedSegmentIds,
                    onTapSegment = onSelectSegment,
                    onLongPressSegment = onLongPressSegment
                )
                overlays.add(ParisBasemapOverlay())
                overlays.add(segmentOverlay)
                tag = SegmentMapOverlayHolder(segmentOverlay)
            }
        },
        update = { mapView ->
            val holder = mapView.tag as? SegmentMapOverlayHolder ?: return@AndroidView
            holder.segmentOverlay.update(
                segments = segments,
                completionStates = completionStates,
                selectedSegmentIds = selectedSegmentIds,
                onTapSegment = onSelectSegment,
                onLongPressSegment = onLongPressSegment
            )
            mapView.invalidate()
        }
    )

    DisposableEffect(Unit) {
        onDispose {
            // MapView lifecycle is owned by AndroidView; no extra teardown required for this MVP.
        }
    }
}

private data class SegmentMapOverlayHolder(
    val segmentOverlay: SegmentNetworkOverlay
)

@Composable
private fun SelectedSegmentPanel(
    selectedSegments: List<StreetSegment>,
    selectedLengthMeters: Double,
    selectedArrondissementLabel: String,
    allSelectedCompleted: Boolean,
    onToggleCompletion: () -> Unit,
    onClearSelection: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        val selectedCount = selectedSegments.size
        Text(
            text = if (selectedCount == 0) {
                "Aucun segment selectionne"
            } else {
                "$selectedCount segment${if (selectedCount > 1) "s" else ""} selectionne${if (selectedCount > 1) "s" else ""}"
            },
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold
        )
        if (selectedCount > 0) {
            val segmentNames = selectedSegments
                .map { it.streetName }
                .distinct()
                .take(3)
                .joinToString(", ")
            Text(
                text = "$selectedArrondissementLabel - ${formatMeters(selectedLengthMeters)} - $segmentNames",
                style = MaterialTheme.typography.bodyMedium
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = onToggleCompletion) {
                    Text(if (allSelectedCompleted) "Marquer non parcouru" else "Marquer parcouru")
                }
                OutlinedButton(onClick = onClearSelection) {
                    Text("Deselectionner")
                }
            }
        }
    }
}

@Composable
private fun StatsPanel(
    globalStats: CompletionStats,
    arrondissementStats: Map<String, CompletionStats>
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(max = 230.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Text(
            text = "Progression globale: ${formatMeters(globalStats.completedMeters)} / ${formatMeters(globalStats.totalMeters)} (${formatPercent(globalStats.percent)})",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium
        )
        arrondissementStats.forEach { (arrondissement, stats) ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(text = arrondissement, style = MaterialTheme.typography.bodySmall)
                Text(
                    text = "${formatMeters(stats.completedMeters)} / ${formatMeters(stats.totalMeters)} (${formatPercent(stats.percent)})",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}

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
