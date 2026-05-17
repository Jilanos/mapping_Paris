package com.jilanos.mappingparis.ui

import android.graphics.Color
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
import org.osmdroid.tileprovider.tilesource.TileSourceFactory
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Polyline

@Composable
fun MappingParisApp(viewModel: MappingParisViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Box(modifier = Modifier.fillMaxSize()) {
                SegmentMap(
                    segments = uiState.segments,
                    completionStates = uiState.completionStates,
                    selectedSegmentId = uiState.selectedSegmentId,
                    onSelectSegment = viewModel::selectSegment,
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
                        selectedSegment = uiState.selectedSegment,
                        isCompleted = uiState.selectedSegmentId?.let { uiState.completionStates[it] == true } == true,
                        onToggleCompletion = viewModel::toggleSelectedCompletion
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
    selectedSegmentId: String?,
    onSelectSegment: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    AndroidView(
        modifier = modifier,
        factory = {
            MapView(context).apply {
                setTileSource(TileSourceFactory.MAPNIK)
                setMultiTouchControls(true)
                controller.setZoom(13.2)
                controller.setCenter(GeoPoint(48.8566, 2.3522))
            }
        },
        update = { mapView ->
            mapView.overlays.clear()
            segments.forEach { segment ->
                val completed = completionStates[segment.id] == true
                val selected = segment.id == selectedSegmentId
                val polyline = Polyline().apply {
                    setPoints(segment.geometry.map { GeoPoint(it.latitude, it.longitude) })
                    outlinePaint.color = when {
                        selected -> Color.rgb(25, 92, 184)
                        completed -> Color.rgb(34, 139, 89)
                        else -> Color.rgb(191, 79, 64)
                    }
                    outlinePaint.strokeWidth = if (selected) 12f else 7f
                    setOnClickListener { _, _, _ ->
                        onSelectSegment(segment.id)
                        true
                    }
                }
                mapView.overlays.add(polyline)
            }
            mapView.invalidate()
        }
    )

    DisposableEffect(Unit) {
        onDispose {
            // MapView lifecycle is owned by AndroidView; no extra teardown required for this MVP.
        }
    }
}

@Composable
private fun SelectedSegmentPanel(
    selectedSegment: StreetSegment?,
    isCompleted: Boolean,
    onToggleCompletion: () -> Unit
) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            text = selectedSegment?.streetName ?: "Aucun segment selectionne",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.SemiBold
        )
        if (selectedSegment != null) {
            Text(
                text = "${selectedSegment.arrondissement} - ${formatMeters(selectedSegment.lengthMeters)} - ${selectedSegment.id}",
                style = MaterialTheme.typography.bodyMedium
            )
            Button(onClick = onToggleCompletion) {
                Text(if (isCompleted) "Marquer non parcouru" else "Marquer parcouru")
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
