package com.jilanos.mappingparis.ui

import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.Point
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.view.MotionEvent
import com.jilanos.mappingparis.data.LatLon
import com.jilanos.mappingparis.data.StreetSegment
import java.util.Locale
import kotlin.math.abs
import kotlin.math.cos
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
    private var gpsProposedSegmentIds: Set<String>,
    private var mapMode: MapMode,
    private var showDebugOverlay: Boolean,
    private var onTapSegment: (String) -> Unit,
    private var onLongPressSegment: (String) -> Unit
) : Overlay() {
    private val path = Path()
    private val point = Point()
    private val nextPoint = Point()
    private val basePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }
    private val selectedPaint = Paint(basePaint)
    private val selectedHaloPaint = Paint(basePaint).apply {
        strokeCap = Paint.Cap.ROUND
    }
    private val proposedPaint = Paint(basePaint)
    private val proposedHaloPaint = Paint(basePaint).apply {
        strokeCap = Paint.Cap.ROUND
    }
    private val debugTextPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 30f
        typeface = android.graphics.Typeface.create(android.graphics.Typeface.MONOSPACE, android.graphics.Typeface.BOLD)
    }
    private val debugBackgroundPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(185, 7, 31, 72)
        style = Paint.Style.FILL
    }
    private val debugRulerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.argb(230, 47, 243, 197)
        strokeWidth = 5f
        strokeCap = Paint.Cap.BUTT
    }
    private val replaceXfermode = PorterDuffXfermode(PorterDuff.Mode.SRC)

    fun update(
        segments: List<StreetSegment>,
        completionStates: Map<String, Boolean>,
        selectedSegmentIds: Set<String>,
        gpsProposedSegmentIds: Set<String>,
        mapMode: MapMode,
        showDebugOverlay: Boolean,
        onTapSegment: (String) -> Unit,
        onLongPressSegment: (String) -> Unit
    ) {
        this.segments = segments
        this.completionStates = completionStates
        this.selectedSegmentIds = selectedSegmentIds
        this.gpsProposedSegmentIds = gpsProposedSegmentIds
        this.mapMode = mapMode
        this.showDebugOverlay = showDebugOverlay
        this.onTapSegment = onTapSegment
        this.onLongPressSegment = onLongPressSegment
    }

    override fun draw(canvas: Canvas, mapView: MapView, shadow: Boolean) {
        if (shadow) return

        drawUnselectedSegments(canvas, mapView)
        drawSelectedSegments(canvas, mapView)
        if (showDebugOverlay) drawDebugOverlay(canvas, mapView)
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

    private fun drawUnselectedSegments(canvas: Canvas, mapView: MapView) {
        val layerId = canvas.saveLayer(
            0f,
            0f,
            mapView.width.toFloat(),
            mapView.height.toFloat(),
            null
        )
        basePaint.xfermode = replaceXfermode
        drawUnselectedSegmentGroup(canvas, mapView, completed = false)
        drawUnselectedSegmentGroup(canvas, mapView, completed = true)
        basePaint.xfermode = null
        canvas.restoreToCount(layerId)
    }

    private fun drawUnselectedSegmentGroup(canvas: Canvas, mapView: MapView, completed: Boolean) {
        val style = if (completed) {
            completedStyle(mapView.zoomLevelDouble)
        } else {
            unvisitedStyle(mapView.zoomLevelDouble)
        }
        val paint = basePaint.apply {
            color = style.color
            strokeWidth = style.strokeWidth
        }
        segments.forEach { segment ->
            if (segment.logicalSegmentId in selectedSegmentIds) return@forEach
            val segmentCompleted = completionStates[segment.logicalSegmentId] == true
            if (segmentCompleted != completed) return@forEach
            if (!segmentIntersectsViewport(segment, mapView)) return@forEach
            drawPolyline(canvas, mapView, segment.geometry, paint)
        }
    }

    private fun drawSelectedSegments(canvas: Canvas, mapView: MapView) {
        segments.forEach { segment ->
            if (segment.logicalSegmentId in selectedSegmentIds) {
                if (!segmentIntersectsViewport(segment, mapView)) return@forEach
                drawSelectedSegment(canvas, mapView, segment)
            }
        }
    }

    private fun drawSelectedSegment(canvas: Canvas, mapView: MapView, segment: StreetSegment) {
        if (segment.logicalSegmentId in gpsProposedSegmentIds) {
            drawProposedSegment(canvas, mapView, segment)
            return
        }
        val style = selectedStyle(mapView.zoomLevelDouble)
        selectedHaloPaint.apply {
            color = style.haloColor
            strokeWidth = style.haloWidth
        }
        drawPolyline(canvas, mapView, segment.geometry, selectedHaloPaint)

        selectedPaint.apply {
            color = style.color
            strokeWidth = style.strokeWidth
        }
        drawPolyline(canvas, mapView, segment.geometry, selectedPaint)
    }

    private fun drawProposedSegment(canvas: Canvas, mapView: MapView, segment: StreetSegment) {
        val style = proposedStyle(mapView.zoomLevelDouble)
        proposedHaloPaint.apply {
            color = style.haloColor
            strokeWidth = style.haloWidth
        }
        drawPolyline(canvas, mapView, segment.geometry, proposedHaloPaint)

        proposedPaint.apply {
            color = style.color
            strokeWidth = style.strokeWidth
        }
        drawPolyline(canvas, mapView, segment.geometry, proposedPaint)
    }

    private fun completedStyle(zoom: Double): SegmentPaintStyle {
        val alpha = segmentOverlayAlpha(zoom)
        val width = ribbonStrokeWidth(zoom)
        return when (mapMode) {
            MapMode.LIGHT -> SegmentPaintStyle(
                color = Color.argb(alpha, 13, 139, 112),
                strokeWidth = width
            )
            MapMode.BLUE -> SegmentPaintStyle(
                color = Color.argb(alpha, 44, 242, 196),
                strokeWidth = width
            )
        }
    }

    private fun unvisitedStyle(zoom: Double): SegmentPaintStyle {
        val alpha = segmentOverlayAlpha(zoom)
        val width = ribbonStrokeWidth(zoom)
        return when (mapMode) {
            MapMode.LIGHT -> SegmentPaintStyle(
                color = Color.argb(alpha, 220, 54, 66),
                strokeWidth = width
            )
            MapMode.BLUE -> SegmentPaintStyle(
                color = Color.argb(alpha, 224, 70, 82),
                strokeWidth = width
            )
        }
    }

    private fun selectedStyle(zoom: Double): SegmentPaintStyle {
        return when (mapMode) {
            MapMode.LIGHT -> SegmentPaintStyle(
                color = Color.argb(224, 114, 70, 230),
                strokeWidth = segmentStrokeWidth(zoom, base = 7.6f, highZoom = 9.6f),
                haloColor = Color.argb(150, 255, 255, 255),
                haloWidth = segmentStrokeWidth(zoom, base = 12.2f, highZoom = 15.2f)
            )
            MapMode.BLUE -> SegmentPaintStyle(
                color = Color.argb(232, 120, 232, 255),
                strokeWidth = segmentStrokeWidth(zoom, base = 7.8f, highZoom = 9.8f),
                haloColor = Color.argb(116, 7, 31, 72),
                haloWidth = segmentStrokeWidth(zoom, base = 12.6f, highZoom = 15.6f)
            )
        }
    }

    private fun proposedStyle(zoom: Double): SegmentPaintStyle {
        return when (mapMode) {
            MapMode.LIGHT -> SegmentPaintStyle(
                color = Color.argb(236, 0, 132, 255),
                strokeWidth = segmentStrokeWidth(zoom, base = 7.8f, highZoom = 9.8f),
                haloColor = Color.argb(170, 255, 255, 255),
                haloWidth = segmentStrokeWidth(zoom, base = 13.6f, highZoom = 16.6f)
            )
            MapMode.BLUE -> SegmentPaintStyle(
                color = Color.argb(242, 255, 214, 64),
                strokeWidth = segmentStrokeWidth(zoom, base = 7.8f, highZoom = 9.8f),
                haloColor = Color.argb(150, 7, 31, 72),
                haloWidth = segmentStrokeWidth(zoom, base = 13.6f, highZoom = 16.6f)
            )
        }
    }

    private fun segmentStrokeWidth(zoom: Double, base: Float, highZoom: Float): Float {
        val zoomFactor = zoomBlend(zoom, start = 12.5, end = 17.0)
        return base + ((highZoom - base) * zoomFactor)
    }

    private fun ribbonStrokeWidth(zoom: Double): Float {
        val cityZoom = zoomBlend(zoom, start = 12.5, end = 15.0)
        val streetZoom = zoomBlend(zoom, start = 15.0, end = 18.0)
        val closeZoom = zoomBlend(zoom, start = 18.0, end = 20.0)
        return 7.0f + (16.0f * cityZoom) + (20.0f * streetZoom) + (10.0f * closeZoom)
    }

    private fun segmentOverlayAlpha(zoom: Double): Int {
        val highZoomBlend = zoomBlend(zoom, start = 14.0, end = 18.5)
        return lerpInt(62, 122, highZoomBlend)
    }

    private fun zoomBlend(zoom: Double, start: Double, end: Double): Float {
        return ((zoom - start) / (end - start)).coerceIn(0.0, 1.0).toFloat()
    }

    private fun lerpInt(start: Int, end: Int, factor: Float): Int {
        return (start + ((end - start) * factor)).toInt()
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

    private fun drawDebugOverlay(canvas: Canvas, mapView: MapView) {
        val x = 24f
        val y = mapView.height - 170f
        canvas.drawRoundRect(x - 12f, y - 54f, x + 370f, y + 58f, 18f, 18f, debugBackgroundPaint)
        val zoomLabel = String.format(Locale.US, "zoom %.2f", mapView.zoomLevelDouble)
        canvas.drawText(zoomLabel, x, y - 18f, debugTextPaint)
        canvas.drawText("${mapView.width} x ${mapView.height}px", x, y + 18f, debugTextPaint)
        canvas.drawLine(x, y + 42f, x + 48f, y + 42f, debugRulerPaint)
        canvas.drawText("48px", x + 62f, y + 50f, debugTextPaint)
    }

    private fun segmentIntersectsViewport(segment: StreetSegment, mapView: MapView): Boolean {
        val box = mapView.boundingBox
        val margin = viewportMarginDegrees(mapView.zoomLevelDouble)
        val north = box.latNorth + margin
        val south = box.latSouth - margin
        val east = box.lonEast + margin
        val west = box.lonWest - margin
        return segment.geometry.any { coordinate ->
            coordinate.latitude in south..north &&
                coordinate.longitude in west..east
        }
    }

    private fun viewportMarginDegrees(zoom: Double): Double {
        val cityZoom = zoomBlend(zoom, start = 11.5, end = 15.0)
        return 0.025 - (0.018 * cityZoom)
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

    private data class SegmentPaintStyle(
        val color: Int,
        val strokeWidth: Float,
        val haloColor: Int = Color.TRANSPARENT,
        val haloWidth: Float = 0f
    )
}

class CurrentLocationOverlay(
    private var location: UserLocation?,
    private var mapMode: MapMode
) : Overlay() {
    private val point = Point()
    private val accuracyPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }
    private val haloPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
        color = Color.WHITE
    }
    private val markerPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.FILL
    }
    private val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        style = Paint.Style.STROKE
        strokeWidth = 4.5f
    }

    fun update(location: UserLocation?, mapMode: MapMode) {
        this.location = location
        this.mapMode = mapMode
    }

    override fun draw(canvas: Canvas, mapView: MapView, shadow: Boolean) {
        if (shadow) return
        val current = location ?: return
        mapView.projection.toPixels(GeoPoint(current.latitude, current.longitude), point)
        current.accuracyMeters?.takeIf { it > 0f }?.let { accuracy ->
            val radius = metersToPixels(accuracy.toDouble(), current.latitude, mapView).coerceIn(18f, 170f)
            accuracyPaint.color = when (mapMode) {
                MapMode.LIGHT -> Color.argb(42, 0, 132, 255)
                MapMode.BLUE -> Color.argb(54, 47, 243, 197)
            }
            canvas.drawCircle(point.x.toFloat(), point.y.toFloat(), radius, accuracyPaint)
        }

        val markerColor = when (mapMode) {
            MapMode.LIGHT -> Color.rgb(0, 100, 255)
            MapMode.BLUE -> Color.rgb(47, 243, 197)
        }
        markerPaint.color = markerColor
        ringPaint.color = Color.argb(230, 7, 31, 72)
        canvas.drawCircle(point.x.toFloat(), point.y.toFloat(), 13.5f, haloPaint)
        canvas.drawCircle(point.x.toFloat(), point.y.toFloat(), 9.0f, markerPaint)
        canvas.drawCircle(point.x.toFloat(), point.y.toFloat(), 15.5f, ringPaint)
    }

    private fun metersToPixels(meters: Double, latitude: Double, mapView: MapView): Float {
        val projection = mapView.projection
        val base = GeoPoint(latitude, 0.0)
        val shifted = GeoPoint(latitude, meters / (111_320.0 * cos(Math.toRadians(latitude))))
        val start = projection.toPixels(base, Point())
        val end = projection.toPixels(shifted, Point())
        return hypot((end.x - start.x).toDouble(), (end.y - start.y).toDouble()).toFloat()
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
