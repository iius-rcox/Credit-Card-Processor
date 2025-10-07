#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy frontend to AKS with cleanup and image rebuild
.DESCRIPTION
    Builds new Docker image, pushes to ACR, and redeploys to AKS
    Deletes existing pods to force fresh deployment
#>

param(
    [string]$ImageTag = "v1.0.1",
    [string]$ACRName = "iiusacr",
    [string]$Namespace = "credit-card-processor"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Frontend Deployment Script ===" -ForegroundColor Cyan
Write-Host "Image Tag: $ImageTag" -ForegroundColor Yellow
Write-Host "ACR: $ACRName" -ForegroundColor Yellow
Write-Host "Namespace: $Namespace" -ForegroundColor Yellow
Write-Host ""

# Step 1: Build Docker image
Write-Host "[1/5] Building Docker image..." -ForegroundColor Green
docker build -t "$ACRName.azurecr.io/expense-frontend:$ImageTag" .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed"
    exit 1
}

# Step 2: Login to ACR
Write-Host "[2/5] Logging into Azure Container Registry..." -ForegroundColor Green
az acr login --name $ACRName
if ($LASTEXITCODE -ne 0) {
    Write-Error "ACR login failed"
    exit 1
}

# Step 3: Push image to ACR
Write-Host "[3/5] Pushing image to ACR..." -ForegroundColor Green
docker push "$ACRName.azurecr.io/expense-frontend:$ImageTag"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed"
    exit 1
}

# Step 4: Delete existing frontend pods
Write-Host "[4/5] Deleting existing frontend pods..." -ForegroundColor Green
kubectl delete pods -l app=frontend -n $Namespace
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to delete pods (may not exist yet)"
}

# Step 5: Update deployment with new image
Write-Host "[5/5] Updating deployment with new image..." -ForegroundColor Green
kubectl set image deployment/frontend "frontend=$ACRName.azurecr.io/expense-frontend:$ImageTag" -n $Namespace
if ($LASTEXITCODE -ne 0) {
    Write-Error "Deployment update failed"
    exit 1
}

# Watch rollout status
Write-Host ""
Write-Host "Watching rollout status..." -ForegroundColor Cyan
kubectl rollout status deployment/frontend -n $Namespace --timeout=5m

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=== Deployment Successful ===" -ForegroundColor Green
    Write-Host "Frontend deployed: $ACRName.azurecr.io/expense-frontend:$ImageTag" -ForegroundColor Green

    # Show pod status
    Write-Host ""
    Write-Host "Current pods:" -ForegroundColor Cyan
    kubectl get pods -l app=frontend -n $Namespace
} else {
    Write-Error "Deployment rollout failed or timed out"
    exit 1
}
