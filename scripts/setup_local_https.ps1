$hostsPath = "C:\Windows\System32\drivers\etc\hosts"
$entry = "127.0.0.1 miniapp.localhost"

if (-not (Select-String -LiteralPath $hostsPath -Pattern "miniapp\.localhost" -Quiet)) {
    Add-Content -LiteralPath $hostsPath -Value "`r`n$entry"
}

Import-Certificate `
    -FilePath "D:\PythonProject\TraiderBot\artifacts\caddy\data\caddy\pki\authorities\local\root.crt" `
    -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null
