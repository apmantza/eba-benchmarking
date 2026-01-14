
Write-Host "Checking GitHub Authentication..."
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please log in to GitHub..."
    gh auth login
}

Write-Host "Creating and Pushing Repository..."
# Create private repo, push current source
gh repo create eba-benchmarking --private --source=. --push

if ($LASTEXITCODE -eq 0) {
    Write-Host "Successfully uploaded to GitHub!"
} else {
    Write-Host "Upload failed. Check errors above."
}
