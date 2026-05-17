package com.jilanos.mappingparis.data

data class LatLon(
    val latitude: Double,
    val longitude: Double
)

data class StreetSegment(
    val id: String,
    val streetName: String,
    val arrondissement: String,
    val lengthMeters: Double,
    val geometry: List<LatLon>,
    val accessibility: String?
)

data class CompletionStats(
    val completedMeters: Double,
    val totalMeters: Double,
    val percent: Double
)

fun List<StreetSegment>.completionStats(completionStates: Map<String, Boolean>): CompletionStats {
    val total = sumOf { it.lengthMeters }
    val completed = filter { completionStates[it.id] == true }.sumOf { it.lengthMeters }
    return CompletionStats(
        completedMeters = completed,
        totalMeters = total,
        percent = if (total == 0.0) 0.0 else completed / total * 100.0
    )
}

fun List<StreetSegment>.completionStatsByArrondissement(
    completionStates: Map<String, Boolean>
): Map<String, CompletionStats> {
    return groupBy { it.arrondissement }
        .toSortedMap()
        .mapValues { (_, segments) -> segments.completionStats(completionStates) }
}
