package com.jilanos.mappingparis.data

import android.content.Context
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class SegmentRepository(context: Context) {
    private val appContext = context.applicationContext
    private val dao = AppDatabase.get(appContext).completionDao()
    private val parser = SegmentGeoJsonParser()

    val completionStates: Flow<Map<String, Boolean>> =
        dao.observeAll().map { rows -> rows.associate { it.segmentId to it.completed } }

    fun loadSegments(): List<StreetSegment> {
        val json = appContext.assets.open("paris_segments_seed.geojson")
            .bufferedReader()
            .use { it.readText() }
        return parser.parse(json)
    }

    suspend fun setCompleted(segmentId: String, completed: Boolean) {
        dao.upsert(
            SegmentCompletionEntity(
                segmentId = segmentId,
                completed = completed,
                updatedAtMillis = System.currentTimeMillis()
            )
        )
    }
}
