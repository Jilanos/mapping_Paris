package com.jilanos.mappingparis.ui

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.Point
import android.view.MotionEvent
import com.jilanos.mappingparis.data.LatLon
import com.jilanos.mappingparis.data.StreetSegment
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Overlay

class SegmentNetworkOverlay(
    private var segments: List<StreetSegment>,
    private var completionStates: Map<String, Boolean>,
    private var selectedSegmentIds: Set<String>,
    private var mapMode: MapMode,
    private var onTapSegment: (String) -> Unit,
    private var onLongPressSegment: (String) -> Unit
) : Overlay() {
    private val path = Path()
    private val point = Point()
    private val nextPoint = Point()
    private val basePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.BUTT
        strokeJoin = Paint.Join.ROUND
    }
    private val selectedPaint = Paint(basePaint).apply {
        color = Color.argb(194, 19, 220, 179)
        strokeWidth = 11f
    }

    fun update(
        segments: List<StreetSegment>,
        completionStates: Map<String, Boolean>,
        selectedSegmentIds: Set<String>,
        mapMode: MapMode,
        onTapSegment: (String) -> Unit,
        onLongPressSegment: (String) -> Unit
    ) {
        this.segments = segments
        this.completionStates = completionStates
        this.selectedSegmentIds = selectedSegmentIds
        this.mapMode = mapMode
        this.onTapSegment = onTapSegment
        this.onLongPressSegment = onLongPressSegment
    }

    override fun draw(canvas: Canvas, mapView: MapView, shadow: Boolean) {
        if (shadow) return

        drawSegments(canvas, mapView, selectedOnly = false)
        drawSegments(canvas, mapView, selectedOnly = true)
    }

    override fun onSingleTapConfirmed(event: MotionEvent, mapView: MapView): Boolean {
        val hitSegmentId = findNearestSegmentId(event.x, event.y, mapView) ?: return false
        onTapSegment(hitSegmentId)
        mapView.invalidate()
        return true
    }

    override fun onLongPress(event: MotionEvent, mapView: MapView): Boolean {
        val hitSegmentId = findNearestSegmentId(event.x, event.y, mapView) ?: return false
        onLongPressSegment(hitSegmentId)
        mapView.invalidate()
        return true
    }

    private fun drawSegments(canvas: Canvas, mapView: MapView, selectedOnly: Boolean) {
        segments.forEach { segment ->
            val logicalSelected = segment.logicalSegmentId in selectedSegmentIds
            if (logicalSelected != selectedOnly) return@forEach

            val paint = if (logicalSelected) {
                selectedPaint
            } else {
                basePaint.apply {
                    color = if (completionStates[segment.logicalSegmentId] == true) {
                        completedColor()
                    } else {
                        pendingColor()
                    }
                    strokeWidth = 9f
                }
            }
            drawPolyline(canvas, mapView, segment.geometry, paint)
        }
    }

    private fun completedColor(): Int {
        return when (mapMode) {
            MapMode.LIGHT -> Color.argb(104, 16, 118, 93)
            MapMode.BLUE -> Color.argb(148, 44, 242, 196)
        }
    }

    private fun pendingColor(): Int {
        return when (mapMode) {
            MapMode.LIGHT -> Color.argb(78, 178, 86, 77)
            MapMode.BLUE -> Color.argb(92, 104, 132, 176)
        }
    }

    private fun drawPolyline(canvas: Canvas, mapView: MapView, geometry: List<LatLon>, paint: Paint) {
        if (geometry.size < 2) return
        path.rewind()
        geometry.forEachIndexed { index, coordinate ->
            mapView.projection.toPixels(GeoPoint(coordinate.latitude, coordinate.longitude), point)
            if (index == 0) {
                path.moveTo(point.x.toFloat(), point.y.toFloat())
            } else {
                path.lineTo(point.x.toFloat(), point.y.toFloat())
            }
        }
        canvas.drawPath(path, paint)
    }

    private fun findNearestSegmentId(x: Float, y: Float, mapView: MapView): String? {
        var nearestId: String? = null
        var nearestDistance = HIT_TOLERANCE_PX

        segments.forEach { segment ->
            val geometry = segment.geometry
            if (geometry.size < 2) return@forEach

            for (index in 0 until geometry.lastIndex) {
                val start = geometry[index]
                val end = geometry[index + 1]
                mapView.projection.toPixels(GeoPoint(start.latitude, start.longitude), point)
                mapView.projection.toPixels(GeoPoint(end.latitude, end.longitude), nextPoint)

                if (!pointIsNearBounds(x, y, point, nextPoint, HIT_TOLERANCE_PX)) continue

                val distance = distanceToLineSegment(
                    x = x,
                    y = y,
                    x1 = point.x.toFloat(),
                    y1 = point.y.toFloat(),
                    x2 = nextPoint.x.toFloat(),
                    y2 = nextPoint.y.toFloat()
                )
                if (distance <= nearestDistance) {
                    nearestDistance = distance
                    nearestId = segment.id
                }
            }
        }

        return nearestId
    }

    private fun pointIsNearBounds(x: Float, y: Float, start: Point, end: Point, tolerance: Float): Boolean {
        return x >= min(start.x, end.x) - tolerance &&
            x <= max(start.x, end.x) + tolerance &&
            y >= min(start.y, end.y) - tolerance &&
            y <= max(start.y, end.y) + tolerance
    }

    private fun distanceToLineSegment(
        x: Float,
        y: Float,
        x1: Float,
        y1: Float,
        x2: Float,
        y2: Float
    ): Float {
        val dx = x2 - x1
        val dy = y2 - y1
        if (abs(dx) < 0.001f && abs(dy) < 0.001f) {
            return hypot((x - x1).toDouble(), (y - y1).toDouble()).toFloat()
        }

        val t = (((x - x1) * dx) + ((y - y1) * dy)) / ((dx * dx) + (dy * dy))
        val clamped = t.coerceIn(0f, 1f)
        val projectedX = x1 + clamped * dx
        val projectedY = y1 + clamped * dy
        return hypot((x - projectedX).toDouble(), (y - projectedY).toDouble()).toFloat()
    }

    private companion object {
        const val HIT_TOLERANCE_PX = 28f
    }
}

class ParisBasemapOverlay : Overlay() {
    private val linePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }
    private val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = Color.rgb(226, 238, 250)
    }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        textSize = 28f
        color = Color.rgb(26, 72, 126)
        typeface = android.graphics.Typeface.create(android.graphics.Typeface.SANS_SERIF, android.graphics.Typeface.BOLD)
    }
    private val labelHaloPaint = Paint(labelPaint).apply {
        style = Paint.Style.STROKE
        strokeWidth = 5f
        color = Color.argb(220, 239, 247, 255)
    }
    private val path = Path()
    private val point = Point()

    override fun draw(canvas: Canvas, mapView: MapView, shadow: Boolean) {
        if (shadow) return
        canvas.drawColor(Color.rgb(207, 226, 243))
        drawPolygon(canvas, mapView, PARIS_OUTLINE, fillPaint)

        linePaint.color = Color.rgb(64, 132, 194)
        linePaint.strokeWidth = 20f
        drawLine(canvas, mapView, SEINE, linePaint)

        linePaint.color = Color.rgb(82, 154, 207)
        linePaint.strokeWidth = 12f
        drawLine(canvas, mapView, CANAL_SAINT_MARTIN, linePaint)
        drawLine(canvas, mapView, CANAL_OURCQ, linePaint)

        linePaint.color = Color.rgb(143, 191, 180)
        linePaint.strokeWidth = 6f
        PARKS.forEach { drawPolygon(canvas, mapView, it.points, Paint(fillPaint).apply { color = it.color }) }

        LABELS.forEach { label ->
            mapView.projection.toPixels(GeoPoint(label.latitude, label.longitude), point)
            canvas.drawText(label.text, point.x.toFloat(), point.y.toFloat(), labelHaloPaint)
            canvas.drawText(label.text, point.x.toFloat(), point.y.toFloat(), labelPaint)
        }
    }

    private fun drawLine(canvas: Canvas, mapView: MapView, points: List<LatLon>, paint: Paint) {
        if (points.size < 2) return
        path.rewind()
        points.forEachIndexed { index, coordinate ->
            mapView.projection.toPixels(GeoPoint(coordinate.latitude, coordinate.longitude), point)
            if (index == 0) path.moveTo(point.x.toFloat(), point.y.toFloat()) else path.lineTo(point.x.toFloat(), point.y.toFloat())
        }
        canvas.drawPath(path, paint)
    }

    private fun drawPolygon(canvas: Canvas, mapView: MapView, points: List<LatLon>, paint: Paint) {
        if (points.size < 3) return
        path.rewind()
        points.forEachIndexed { index, coordinate ->
            mapView.projection.toPixels(GeoPoint(coordinate.latitude, coordinate.longitude), point)
            if (index == 0) path.moveTo(point.x.toFloat(), point.y.toFloat()) else path.lineTo(point.x.toFloat(), point.y.toFloat())
        }
        path.close()
        canvas.drawPath(path, paint)
    }

    private data class Label(val text: String, val latitude: Double, val longitude: Double)
    private data class Park(val points: List<LatLon>, val color: Int = Color.rgb(188, 219, 200))

    private companion object {
        val PARIS_OUTLINE = listOf(
            LatLon(48.9021, 2.2790), LatLon(48.9000, 2.3920), LatLon(48.8785, 2.4140),
            LatLon(48.8350, 2.4140), LatLon(48.8155, 2.3650), LatLon(48.8170, 2.2700),
            LatLon(48.8420, 2.2520), LatLon(48.8840, 2.2550)
        )
        val SEINE = listOf(
            LatLon(48.8347, 2.2520), LatLon(48.8460, 2.2860), LatLon(48.8582, 2.2945),
            LatLon(48.8635, 2.3180), LatLon(48.8584, 2.3370), LatLon(48.8518, 2.3520),
            LatLon(48.8462, 2.3715), LatLon(48.8335, 2.3860), LatLon(48.8250, 2.4120)
        )
        val CANAL_SAINT_MARTIN = listOf(
            LatLon(48.8702, 2.3650), LatLon(48.8764, 2.3666), LatLon(48.8841, 2.3697),
            LatLon(48.8895, 2.3755)
        )
        val CANAL_OURCQ = listOf(
            LatLon(48.8895, 2.3755), LatLon(48.8925, 2.3840), LatLon(48.8955, 2.3975)
        )
        val PARKS = listOf(
            Park(listOf(LatLon(48.8780, 2.3000), LatLon(48.8870, 2.3090), LatLon(48.8840, 2.3270), LatLon(48.8738, 2.3180))),
            Park(listOf(LatLon(48.8455, 2.2510), LatLon(48.8520, 2.2700), LatLon(48.8420, 2.2810), LatLon(48.8335, 2.2610))),
            Park(listOf(LatLon(48.8235, 2.3370), LatLon(48.8332, 2.3500), LatLon(48.8260, 2.3650), LatLon(48.8178, 2.3520))),
            Park(listOf(LatLon(48.8780, 2.3770), LatLon(48.8840, 2.3850), LatLon(48.8770, 2.3960), LatLon(48.8700, 2.3880)))
        )
        val LABELS = listOf(
            Label("Tour Eiffel", 48.8584, 2.2945),
            Label("Louvre", 48.8606, 2.3376),
            Label("Notre-Dame", 48.8530, 2.3499),
            Label("Elysee", 48.8706, 2.3166),
            Label("Sacré-Coeur", 48.8867, 2.3431),
            Label("Gare du Nord", 48.8809, 2.3553),
            Label("Gare de Lyon", 48.8443, 2.3730),
            Label("Montparnasse", 48.8406, 2.3199),
            Label("Bastille", 48.8530, 2.3690),
            Label("La Villette", 48.8896, 2.3938),
            Label("Luxembourg", 48.8462, 2.3371),
            Label("Parc Monceau", 48.8797, 2.3090)
        )
    }
}
