param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl
)

$blocked = "huggingface.co/spaces/quynhphuong1209/Rehab-AI-Monitor-2026"
$allowed = "huggingface.co/spaces/quynhphuong1209/Rehab-AI-Monitor-UI-new"

if ($RemoteUrl -like "*$blocked*") {
    Write-Error "Blocked deploy target: $blocked"
    exit 42
}

if ($RemoteUrl -notlike "*$allowed*") {
    Write-Error "Unexpected Hugging Face deploy target. Allowed: $allowed"
    exit 43
}

Write-Host "HF deploy target allowed: $RemoteUrl"
