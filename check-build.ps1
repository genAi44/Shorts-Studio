Set-Location C:\Users\mhama\Desktop\shorts-studio\remotion
if (Test-Path build) {
  Get-ChildItem build | Select-Object -ExpandProperty Name | Sort-Object | Out-File -FilePath C:\Users\mhama\Desktop\shorts-studio\build-list.txt
  Write-Host 'BUILD DIR contents:'
  Get-Content C:\Users\mhama\Desktop\shorts-studio\build-list.txt
} else {
  Write-Host 'NO BUILD DIR'
}
