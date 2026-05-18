package com.jilanos.mappingparis.data

import android.content.Context
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

data class CompletionMigrationResult(
    val migratedRows: Int,
    val removedRows: Int
)

class SegmentRepository(context: Context) {
    private val appContext = context.applicationContext
    private val dao = AppDatabase.get(appContext).completionDao()
    private val parser = SegmentGeoJsonParser()

    val completionStates: Flow<Map<String, Boolean>> =
        dao.observeAll().map { rows -> rows.associate { it.segmentId to it.completed } }

    fun loadSegments(): List<StreetSegment> {
        val json = appContext.assets.open("paris_segments.geojson")
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

    suspend fun setCompleted(segmentIds: Set<String>, completed: Boolean) {
        val now = System.currentTimeMillis()
        dao.upsertAll(
            segmentIds.map { segmentId ->
                SegmentCompletionEntity(
                    segmentId = segmentId,
                    completed = completed,
                    updatedAtMillis = now
                )
            }
        )
    }

    suspend fun replaceCompleted(segmentIds: Set<String>) {
        val now = System.currentTimeMillis()
        dao.deleteAll()
        dao.upsertAll(
            segmentIds.map { segmentId ->
                SegmentCompletionEntity(
                    segmentId = segmentId,
                    completed = true,
                    updatedAtMillis = now
                )
            }
        )
    }

    suspend fun mergeCompleted(segmentIds: Set<String>) {
        setCompleted(segmentIds = segmentIds, completed = true)
    }

    suspend fun resetProgress() {
        dao.deleteAll()
    }

    suspend fun restoreCompletionStates(states: Map<String, Boolean>) {
        val now = System.currentTimeMillis()
        dao.upsertAll(
            states.map { (segmentId, completed) ->
                SegmentCompletionEntity(
                    segmentId = segmentId,
                    completed = completed,
                    updatedAtMillis = now
                )
            }
        )
    }

    suspend fun migrateVisualRowsToLogicalIds(segments: List<StreetSegment>): CompletionMigrationResult {
        val rows = dao.getAll()
        val logicalIds = segments.map { it.logicalSegmentId }.toSet()
        val visualToLogical = segments.associate { it.id to it.logicalSegmentId }
        val rowsToRemove = mutableListOf<String>()
        val logicalRowsToWrite = mutableSetOf<String>()

        rows.forEach { row ->
            if (row.segmentId in logicalIds) return@forEach
            val logicalId = visualToLogical[row.segmentId] ?: return@forEach
            rowsToRemove += row.segmentId
            if (row.completed) {
                logicalRowsToWrite += logicalId
            }
        }

        if (logicalRowsToWrite.isNotEmpty()) {
            setCompleted(segmentIds = logicalRowsToWrite, completed = true)
        }
        if (rowsToRemove.isNotEmpty()) {
            dao.deleteByIds(rowsToRemove)
        }

        return CompletionMigrationResult(
            migratedRows = logicalRowsToWrite.size,
            removedRows = rowsToRemove.size
        )
    }
}
