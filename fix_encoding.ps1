$scriptPath = "E:\Sky毕业设计\4.系统源代码\SDPJ-System\start.ps1"
$content = Get-Content $scriptPath -Raw
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText($scriptPath, $content, $utf8Bom)
Write-Host "Done. BOM added."