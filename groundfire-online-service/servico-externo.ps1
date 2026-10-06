$target = Join-Path $PSScriptRoot 'groundfire-online-service.ps1'
& $target @args
exit $LASTEXITCODE
