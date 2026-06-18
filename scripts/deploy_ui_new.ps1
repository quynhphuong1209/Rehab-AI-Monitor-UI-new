param(
    [string]$Message = "Update Rehab AI Monitor professional UI"
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$hfRemote = (git remote get-url --push hf-new).Trim()
& "$PSScriptRoot\guard_hf_deploy.ps1" -RemoteUrl $hfRemote

git add .
git commit -m $Message
git push gh-new main
git push hf-new main

Write-Host "Deployed to GitHub gh-new and Hugging Face hf-new."
