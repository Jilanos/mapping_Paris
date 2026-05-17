package com.jilanos.mappingparis

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import com.jilanos.mappingparis.ui.MappingParisApp
import com.jilanos.mappingparis.ui.MappingParisViewModel

class MainActivity : ComponentActivity() {
    private val viewModel: MappingParisViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MappingParisApp(viewModel = viewModel)
        }
    }
}
