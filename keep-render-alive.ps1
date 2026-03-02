# Render Keep-Alive Bot
# This script makes periodic requests to prevent Render from spinning down

$websiteUrl = "https://cardiff-forms.onrender.com"  # Change to your Render URL
$checkInterval = 900  # 15 minutes in seconds
$logFile = "C:\TempApp\Cardiff Forms\keep-alive.log"

# Create/clear log
if (Test-Path $logFile) {
    Remove-Item $logFile
}

Write-Host "🤖 Render Keep-Alive Bot Started" -ForegroundColor Green
Write-Host "URL: $websiteUrl" -ForegroundColor Cyan
Write-Host "Check interval: $(($checkInterval / 60)) minutes" -ForegroundColor Cyan
Write-Host "Log file: $logFile" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

$requestCount = 0

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $requestCount++
    
    try {
        Write-Host "[$timestamp] Request #$requestCount to $websiteUrl..." -ForegroundColor Cyan
        
        # Make the request
        $response = Invoke-WebRequest -Uri $websiteUrl `
            -Method GET `
            -TimeoutSec 10 `
            -UserAgent "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" `
            -ErrorAction Stop
        
        $statusCode = $response.StatusCode
        $responseTime = $response.ResponseTime
        
        $logMessage = "[$timestamp] ✓ Success - Status $statusCode - Response: ${responseTime}ms"
        Add-Content -Path $logFile -Value $logMessage
        Write-Host "✓ Success - Status $statusCode - Response: ${responseTime}ms" -ForegroundColor Green
        
    } catch {
        $errorMsg = $_.Exception.Message
        $logError = "[$timestamp] ✗ Failed - Error: $errorMsg"
        Add-Content -Path $logFile -Value $logError
        Write-Host "✗ Failed - Error: $errorMsg" -ForegroundColor Red
    }
    
    Write-Host "💤 Sleeping for $($checkInterval / 60) minutes until next check...`n" -ForegroundColor Yellow
    Start-Sleep -Seconds $checkInterval
}
