package com.jilanos.mappingparis.b2

data class B2Health(
    val status: String,
    val service: String,
    val version: String
)

data class B2AuthStatus(
    val configured: Boolean,
    val connected: Boolean,
    val expiresAt: String?,
    val scope: String?
)

data class B2SyncRunSummary(
    val id: Int,
    val status: String,
    val startedAt: String?,
    val finishedAt: String?,
    val activitiesFetched: Int,
    val activitiesCreated: Int,
    val activitiesUpdated: Int,
    val streamsDownloaded: Int,
    val pagesRequested: Int,
    val skippedExistingActivities: Int,
    val errorsCount: Int,
    val message: String?
)

data class B2SyncStatus(
    val connected: Boolean,
    val latestSync: B2SyncRunSummary?,
    val storedActivities: Int,
    val storedStreams: Int,
    val activitiesWithStreams: Int
)

data class B2ProposalGenerationSummary(
    val activitiesWithStreamsTotal: Int,
    val activitiesAlreadyHadProposals: Int,
    val activitiesWithoutExistingProposals: Int,
    val activitiesProcessed: Int,
    val streamsProcessed: Int,
    val activitiesSkippedAlreadyProcessed: Int,
    val candidateSegmentsChecked: Int,
    val proposalsCreated: Int,
    val proposalsUpdated: Int,
    val proposalsSkipped: Int,
    val errorsCount: Int
)

data class B2ProposalStatus(
    val totalProposals: Int,
    val proposedCount: Int,
    val acceptedCount: Int,
    val dismissedCount: Int,
    val activeDatasetVersionId: Int?,
    val activitiesWithStreamsCount: Int,
    val latestProposalCreatedAt: String?
)

data class B2Proposal(
    val id: Int,
    val stravaActivityId: String,
    val segmentId: String,
    val logicalSegmentId: String,
    val streetName: String,
    val arrondissement: String,
    val segmentLengthMeters: Double,
    val coveredLengthMeters: Double,
    val coverageRatio: Double,
    val avgDistanceMeters: Double,
    val matchedPointsCount: Int,
    val confidenceScore: Double,
    val status: String,
    val createdAt: String?
)

data class B2ProposalsPage(
    val proposals: List<B2Proposal>,
    val total: Int,
    val limit: Int,
    val offset: Int,
    val returned: Int,
    val hasMore: Boolean,
    val nextOffset: Int?
)
