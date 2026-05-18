package com.jilanos.mappingparis.data

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "segment_completion")
data class SegmentCompletionEntity(
    @PrimaryKey val segmentId: String,
    val completed: Boolean,
    val updatedAtMillis: Long
)

@Dao
interface SegmentCompletionDao {
    @Query("SELECT * FROM segment_completion")
    fun observeAll(): Flow<List<SegmentCompletionEntity>>

    @Query("SELECT * FROM segment_completion")
    suspend fun getAll(): List<SegmentCompletionEntity>

    @Upsert
    suspend fun upsert(entity: SegmentCompletionEntity)

    @Upsert
    suspend fun upsertAll(entities: List<SegmentCompletionEntity>)

    @Query("DELETE FROM segment_completion")
    suspend fun deleteAll()

    @Query("DELETE FROM segment_completion WHERE segmentId IN (:segmentIds)")
    suspend fun deleteByIds(segmentIds: List<String>)
}
