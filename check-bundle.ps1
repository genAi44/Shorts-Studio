Set-Location C:\Users\mhama\Desktop\shorts-studio\remotion
Write-Host '=== main bundle.js size ==='
$js = Get-Content (Join-Path 'build' 'bundle.js') -Raw -Encoding UTF8
Write-Host ('CHAR COUNT: {0}' -f $js.Length)
Write-Host ('LINE COUNT: {0}' -f ($js -split '\r?\n').Count)
Write-Host '=== tail 300 chars ==='
Write-Host $js.Substring($js.Length - 300)
