package com.jilanos.mappingparis

import android.app.Application
import org.osmdroid.config.Configuration

class MappingParisApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        Configuration.getInstance().userAgentValue = packageName
    }
}
