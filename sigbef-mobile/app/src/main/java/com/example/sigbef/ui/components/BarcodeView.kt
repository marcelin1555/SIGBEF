package com.example.sigbef.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.abs

@Composable
fun BarcodeView(
    code: String,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(80.dp)
        ) {
            val width = size.width
            val height = size.height
            
            // Deterministic pseudo-barcode generation based on string hash & chars
            val bars = mutableListOf<Float>()
            var isBlack = true
            
            // Start quiet zone & start pattern
            bars.add(3f); bars.add(1f); bars.add(1f); bars.add(2f)
            
            for (char in code) {
                val num = char.code
                val w1 = ((num * 3) % 4 + 1).toFloat()
                val w2 = ((num * 7) % 3 + 1).toFloat()
                val w3 = ((num * 5) % 4 + 1).toFloat()
                bars.add(w1)
                bars.add(w2)
                bars.add(w3)
            }
            // End pattern
            bars.add(2f); bars.add(1f); bars.add(3f)

            val totalWeight = bars.sum()
            val unitWidth = width / totalWeight

            var currentX = 0f
            isBlack = true
            for (w in bars) {
                val barWidth = w * unitWidth
                if (isBlack) {
                    drawRect(
                        color = Color(0xFF1A1A1A),
                        topLeft = Offset(currentX, 0f),
                        size = Size(barWidth, height)
                    )
                }
                currentX += barWidth
                isBlack = !isBlack
            }
        }

        Text(
            text = code,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 4.sp,
            color = Color(0xFF1A1A1A),
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 8.dp)
        )
    }
}
