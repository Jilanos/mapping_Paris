package com.jilanos.mappingparis.data

import org.json.JSONObject

class SegmentGeoJsonParser {
    fun parse(rawJson: String): List<StreetSegment> {
        val root = JSONObject(rawJson)
        val features = root.getJSONArray("features")
        return buildList {
            for (index in 0 until features.length()) {
                val feature = features.getJSONObject(index)
                val properties = feature.getJSONObject("properties")
                val geometry = feature.getJSONObject("geometry")
                val coordinates = geometry.getJSONArray("coordinates")

                add(
                    StreetSegment(
                        id = properties.getString("id"),
                        streetName = properties.getString("street_name"),
                        arrondissement = properties.getString("arrondissement"),
                        lengthMeters = properties.getDouble("length_meters"),
                        accessibility = if (properties.has("accessibility")) {
                            properties.getString("accessibility")
                        } else {
                            null
                        },
                        geometry = buildList {
                            for (pointIndex in 0 until coordinates.length()) {
                                val point = coordinates.getJSONArray(pointIndex)
                                add(
                                    LatLon(
                                        latitude = point.getDouble(1),
                                        longitude = point.getDouble(0)
                                    )
                                )
                            }
                        }
                    )
                )
            }
        }
    }
}
