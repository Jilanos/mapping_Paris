package com.jilanos.mappingparis.b2

import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

class B2ApiException(message: String) : Exception(message)

class B2ApiClient(private val baseUrl: String) {
    suspend fun getHealth(): B2Health {
        val json = requestJson(path = "/health", method = "GET")
        return B2JsonParser.health(json)
    }

    suspend fun getAuthStatus(): B2AuthStatus {
        val json = requestJson(path = "/auth/strava/status", method = "GET")
        return B2JsonParser.authStatus(json)
    }

    suspend fun triggerStravaSync(): B2SyncRunSummary {
        val json = requestJson(path = "/sync/strava", method = "POST")
        return B2JsonParser.syncRunSummary(json)
    }

    suspend fun getSyncStatus(): B2SyncStatus {
        val json = requestJson(path = "/sync/status", method = "GET")
        return B2JsonParser.syncStatus(json)
    }

    suspend fun triggerProposalGeneration(): B2ProposalGenerationSummary {
        val json = requestJson(path = "/proposals/generate", method = "POST")
        return B2JsonParser.proposalGenerationSummary(json)
    }

    suspend fun getProposalStatus(): B2ProposalStatus {
        val json = requestJson(path = "/proposals/status", method = "GET")
        return B2JsonParser.proposalStatus(json)
    }

    suspend fun getProposals(status: String = "proposed"): List<B2Proposal> {
        val json = requestJson(path = "/proposals?status=${encodeQueryValue(status)}", method = "GET")
        return B2JsonParser.proposals(json)
    }

    suspend fun acceptProposal(proposalId: Int) {
        requestJson(path = "/proposals/$proposalId/accept", method = "POST")
    }

    suspend fun dismissProposal(proposalId: Int) {
        requestJson(path = "/proposals/$proposalId/dismiss", method = "POST")
    }

    private suspend fun requestJson(path: String, method: String): JSONObject = withContext(Dispatchers.IO) {
        val normalizedBaseUrl = normalizeBackendUrl(baseUrl)
            ?: throw B2ApiException("URL backend invalide")
        val connection = (URL(normalizedBaseUrl + path).openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 10_000
            readTimeout = 20_000
            setRequestProperty("Accept", "application/json")
            if (method == "POST") {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Content-Length", "0")
            }
        }
        try {
            if (method == "POST") {
                connection.outputStream.use { }
            }
            val responseCode = connection.responseCode
            val stream = if (responseCode in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (responseCode !in 200..299) {
                throw B2ApiException("Backend HTTP $responseCode: ${body.take(180)}")
            }
            JSONObject(if (body.isBlank()) "{}" else body)
        } catch (exception: IOException) {
            throw B2ApiException(exception.message ?: "Backend indisponible")
        } finally {
            connection.disconnect()
        }
    }

    private fun encodeQueryValue(value: String): String {
        return java.net.URLEncoder.encode(value, Charsets.UTF_8.name())
    }
}

object B2JsonParser {
    fun health(json: JSONObject): B2Health {
        return B2Health(
            status = json.optString("status"),
            service = json.optString("service"),
            version = json.optString("version")
        )
    }

    fun authStatus(json: JSONObject): B2AuthStatus {
        return B2AuthStatus(
            configured = json.optBoolean("configured"),
            connected = json.optBoolean("connected"),
            expiresAt = json.optNullableString("expires_at"),
            scope = json.optNullableString("scope")
        )
    }

    fun syncStatus(json: JSONObject): B2SyncStatus {
        val latest = json.optJSONObject("latest_sync")?.let(::syncRunSummary)
        return B2SyncStatus(
            connected = json.optBoolean("connected"),
            latestSync = latest,
            storedActivities = json.optInt("stored_activities"),
            storedStreams = json.optInt("stored_streams"),
            activitiesWithStreams = json.optInt("activities_with_streams")
        )
    }

    fun syncRunSummary(json: JSONObject): B2SyncRunSummary {
        return B2SyncRunSummary(
            id = json.optInt("id"),
            status = json.optString("status"),
            startedAt = json.optNullableString("started_at"),
            finishedAt = json.optNullableString("finished_at"),
            activitiesFetched = json.optInt("activities_fetched"),
            activitiesCreated = json.optInt("activities_created"),
            activitiesUpdated = json.optInt("activities_updated"),
            streamsDownloaded = json.optInt("streams_downloaded"),
            errorsCount = json.optInt("errors_count"),
            message = json.optNullableString("message")
        )
    }

    fun proposalGenerationSummary(json: JSONObject): B2ProposalGenerationSummary {
        return B2ProposalGenerationSummary(
            activitiesProcessed = json.optInt("activities_processed"),
            streamsProcessed = json.optInt("streams_processed"),
            candidateSegmentsChecked = json.optInt("candidate_segments_checked"),
            proposalsCreated = json.optInt("proposals_created"),
            proposalsUpdated = json.optInt("proposals_updated"),
            proposalsSkipped = json.optInt("proposals_skipped"),
            errorsCount = json.optInt("errors_count")
        )
    }

    fun proposalStatus(json: JSONObject): B2ProposalStatus {
        return B2ProposalStatus(
            totalProposals = json.optInt("total_proposals"),
            proposedCount = json.optInt("proposed_count"),
            acceptedCount = json.optInt("accepted_count"),
            dismissedCount = json.optInt("dismissed_count"),
            activeDatasetVersionId = json.optNullableInt("active_dataset_version_id"),
            activitiesWithStreamsCount = json.optInt("activities_with_streams_count"),
            latestProposalCreatedAt = json.optNullableString("latest_proposal_created_at")
        )
    }

    fun proposals(json: JSONObject): List<B2Proposal> {
        val array = json.optJSONArray("proposals") ?: JSONArray()
        return buildList {
            for (index in 0 until array.length()) {
                add(proposal(array.getJSONObject(index)))
            }
        }
    }

    private fun proposal(json: JSONObject): B2Proposal {
        return B2Proposal(
            id = json.optInt("id"),
            stravaActivityId = json.optString("strava_activity_id"),
            segmentId = json.optString("segment_id"),
            logicalSegmentId = json.optString("logical_segment_id"),
            streetName = json.optString("street_name"),
            arrondissement = json.optString("arrondissement"),
            segmentLengthMeters = json.optDouble("segment_length_meters"),
            coveredLengthMeters = json.optDouble("covered_length_meters"),
            coverageRatio = json.optDouble("coverage_ratio"),
            avgDistanceMeters = json.optDouble("avg_distance_meters"),
            matchedPointsCount = json.optInt("matched_points_count"),
            confidenceScore = json.optDouble("confidence_score"),
            status = json.optString("status"),
            createdAt = json.optNullableString("created_at")
        )
    }
}

fun normalizeBackendUrl(rawValue: String): String? {
    val trimmed = rawValue.trim().trimEnd('/')
    if (trimmed.isBlank()) return ""
    if (!trimmed.startsWith("http://") && !trimmed.startsWith("https://")) return null
    return trimmed
}

private fun JSONObject.optNullableString(name: String): String? {
    return if (has(name) && !isNull(name)) optString(name) else null
}

private fun JSONObject.optNullableInt(name: String): Int? {
    return if (has(name) && !isNull(name)) optInt(name) else null
}
