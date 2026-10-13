<#
.SYNOPSIS
    CampusFix load generator (PowerShell equivalent of scripts/load-test.sh).

.DESCRIPTION
    Sends real HTTP traffic at the CampusFix API so that:
      * the Prometheus/Grafana panels have something to plot, and
      * the Horizontal Pod Autoscaler has CPU pressure to react to.

.PARAMETER Url
    Target URL. Defaults to the backend API.

.PARAMETER Requests
    Number of sequential requests to send.

.EXAMPLE
    .\scripts\load-test.ps1
.EXAMPLE
    .\scripts\load-test.ps1 -Url http://localhost:3000/api/tickets -Requests 500
#>
[CmdletBinding()]
param(
    [string]$Url      = 'http://127.0.0.1:8000/api/tickets',
    [ValidateRange(1, 100000)]
    [int]$Requests    = 200
)

$ErrorActionPreference = 'Stop'

Write-Host 'CampusFix load test'
Write-Host "  target   : $Url"
Write-Host "  requests : $Requests"

$results = [System.Collections.Generic.List[object]]::new()
$timer   = [System.Diagnostics.Stopwatch]::StartNew()

for ($i = 1; $i -le $Requests; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = 0
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        $status = [int]$resp.StatusCode
    } catch {
        # A 4xx/5xx still produced a real response, so read its status code.
        if ($_.Exception.Response) { $status = [int]$_.Exception.Response.StatusCode }
        else { $status = 0 }
    }
    $sw.Stop()
    $results.Add([pscustomobject]@{ Status = $status; Seconds = $sw.Elapsed.TotalSeconds })
}
$timer.Stop()

$success = @($results | Where-Object { $_.Status -ge 200 -and $_.Status -lt 400 })
$failed  = $results.Count - $success.Count
$avg     = if ($results.Count) { ($results | Measure-Object -Property Seconds -Average).Average } else { 0 }
$max     = if ($results.Count) { ($results | Measure-Object -Property Seconds -Maximum).Maximum } else { 0 }

Write-Host ''
Write-Host ('  elapsed    : {0:N1}s' -f $timer.Elapsed.TotalSeconds)
Write-Host "  successful : $($success.Count)"
Write-Host "  failed     : $failed"
Write-Host ('  avg latency: {0:N4}s' -f $avg)
Write-Host ('  max latency: {0:N4}s' -f $max)

if ($failed -gt 0) {
    Write-Host ''
    Write-Host 'Non-2xx responses seen:'
    $results |
        Where-Object { $_.Status -lt 200 -or $_.Status -ge 400 } |
        Group-Object Status |
        Sort-Object Count -Descending |
        Select-Object Count, @{ n = 'Status'; e = { $_.Name } } |
        Format-Table -AutoSize | Out-String | Write-Host
    exit 1
}

Write-Host ''
Write-Host 'Load test completed successfully.'