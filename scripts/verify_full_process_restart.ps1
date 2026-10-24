# ==============================================================================
# verify_full_process_restart.ps1
# Phase 2 Mandatory Verification: Real Java Process Stop & Restart Persistence Test
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "======================================================================"
Write-Host "PHASE 2: FULL JAVA PROCESS RESTART PERSISTENCE AUDIT"
Write-Host "======================================================================"

$backendDir = "C:\Users\sunka\OneDrive\coding\where-is-my-ferry\backend"
$baseUrl = "http://localhost:8080"

function Wait-For-Health {
    param([int]$maxAttempts = 40)
    Write-Host "Waiting for backend health endpoint at $baseUrl/actuator/health..."
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $resp = Invoke-RestMethod -Uri "$baseUrl/actuator/health" -Method Get -TimeoutSec 3 -ErrorAction SilentlyContinue
            if ($resp.status -eq "UP") {
                Write-Host "Backend is UP and healthy on attempt $i!" -ForegroundColor Green
                return $true
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "Backend failed to become healthy within timeout."
}

# 1. Start initial backend process
Write-Host "`nSTEP 1: Starting Spring Boot application process (PID tracking)..."
Get-Process -Name "java" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
$proc1 = Start-Process -FilePath "mvn" -ArgumentList "spring-boot:run" -WorkingDirectory $backendDir -PassThru -NoNewWindow
Write-Host "Spawned maven runner PID: $($proc1.Id)"

Wait-For-Health

# 2. Authenticate as Passenger
Write-Host "`nSTEP 2: Authenticating as passenger via /api/v1/auth/demo/login..."
$loginBody = @{ username = "passenger"; password = "123" } | ConvertTo-Json
$authResp = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/demo/login" -Method Post -ContentType "application/json" -Body $loginBody
$token = $authResp.token
if (-not $token) { throw "Authentication failed, no token returned!" }
Write-Host "Obtained JWT token for passenger (length: $($token.Length))"

# 3. Create a real reservation via API
Write-Host "`nSTEP 3: Creating real reservation on SAIL-BRE-LCQ-0830..."
$uniqueKey = "restart-test-" + [System.Guid]::NewGuid().ToString()
$bookingPayload = @{
    sailingId = "SAIL-BRE-LCQ-0830"
    passengerCount = 2
    passengers = @(
        @{ fullName = "Restart Test Lead"; category = "ADULT"; accessibilityNotes = "None" },
        @{ fullName = "Restart Test Guest"; category = "ADULT"; accessibilityNotes = "None" }
    )
    assignedSeats = @("Deck A - Row 1, Seat 1", "Deck A - Row 1, Seat 2")
    optionalServices = @("Standard Crossing", "Bicycle Transport")
    idempotencyKey = $uniqueKey
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$createdBooking = Invoke-RestMethod -Uri "$baseUrl/api/v1/passenger/bookings" -Method Post -Headers $headers -Body $bookingPayload
$bookingRef = $createdBooking.bookingReference
Write-Host "Created Booking Reference: $bookingRef" -ForegroundColor Cyan
Write-Host "Initial Status: $($createdBooking.status), Payment: $($createdBooking.paymentStatus), Ticket: $($createdBooking.ticketStatus)"
Write-Host "Ticket Barcode (Hold): $($createdBooking.ticketBarcode)"

if ($createdBooking.status -ne "RESERVED") { throw "Expected status RESERVED" }
if ($createdBooking.totalPaidEur -ne 0) { throw "Expected totalPaidEur 0.00" }

# 4. FULL PROCESS TERMINATION: Kill all java processes
Write-Host "`nSTEP 4: KILLING Java backend process to simulate complete application shutdown..."
Get-Process -Name "java" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Verify backend is down
Write-Host "Verifying backend is offline..."
$isDown = $false
try {
    Invoke-RestMethod -Uri "$baseUrl/actuator/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
} catch {
    $isDown = $true
}
if (-not $isDown) { throw "Process kill failed: backend is still responding!" }
Write-Host "Backend process successfully stopped. Port 8080 is offline." -ForegroundColor Yellow

# 5. RESTART: Start a completely new Java backend process
Write-Host "`nSTEP 5: RESTARTING Spring Boot process from scratch..."
$proc2 = Start-Process -FilePath "mvn" -ArgumentList "spring-boot:run" -WorkingDirectory $backendDir -PassThru -NoNewWindow
Write-Host "Spawned restarted maven runner PID: $($proc2.Id)"

Wait-For-Health

# 6. Re-authenticate on restarted process
Write-Host "`nSTEP 6: Re-authenticating on restarted backend..."
$authResp2 = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/demo/login" -Method Post -ContentType "application/json" -Body $loginBody
$token2 = $authResp2.token

# 7. Retrieve booking by reference from restarted backend
Write-Host "`nSTEP 7: Retrieving booking $bookingRef from restarted process..."
$headers2 = @{
    "Authorization" = "Bearer $token2"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

$reloadedBooking = Invoke-RestMethod -Uri "$baseUrl/api/v1/passenger/bookings/$bookingRef" -Method Get -Headers $headers2
Write-Host "Reloaded Booking Ref: $($reloadedBooking.bookingReference)" -ForegroundColor Green
Write-Host "Status after restart: $($reloadedBooking.status)" -ForegroundColor Green
Write-Host "Payment Status: $($reloadedBooking.paymentStatus)" -ForegroundColor Green
Write-Host "Ticket Status: $($reloadedBooking.ticketStatus)" -ForegroundColor Green
Write-Host "Manifest count: $($reloadedBooking.passengers.Count)" -ForegroundColor Green
Write-Host "Lead passenger name: $($reloadedBooking.passengers[0].fullName)" -ForegroundColor Green

if ($reloadedBooking.bookingReference -ne $bookingRef) { throw "Booking reference mismatch after restart!" }
if ($reloadedBooking.status -ne "RESERVED") { throw "Status mismatch after restart!" }
if ($reloadedBooking.passengers.Count -ne 2) { throw "Manifest count mismatch after restart!" }

# 8. Cancel booking on restarted backend
Write-Host "`nSTEP 8: Cancelling booking on restarted backend..."
$cancelBody = @{ reason = "Restart test verified complete" } | ConvertTo-Json
$cancelledBooking = Invoke-RestMethod -Uri "$baseUrl/api/v1/passenger/bookings/$bookingRef/cancel" -Method Post -Headers $headers2 -Body $cancelBody
Write-Host "Booking cancellation confirmed. New Status: $($cancelledBooking.status), Ticket: $($cancelledBooking.ticketStatus)" -ForegroundColor Green

if ($cancelledBooking.status -ne "CANCELLED") { throw "Expected status CANCELLED" }
if ($cancelledBooking.ticketStatus -ne "VOIDED") { throw "Expected ticketStatus VOIDED" }

Write-Host "`n======================================================================"
Write-Host "EVIDENCE: FULL-PROCESS RESTART PERSISTENCE VERIFICATION PASSED!" -ForegroundColor Green
Write-Host "======================================================================"
