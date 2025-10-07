#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Full deployment script for Credit Card Processor to AKS
.DESCRIPTION
    Builds and pushes both frontend and backend Docker images to ACR,
    then redeploys all components to AKS with cleanup
#>

param(
    [string]$FrontendTag = "v1.0.1",
    [string]$BackendTag = "v1.0.1",
    [string]$ACRName = "iiusacr",
    [string]$Namespace = "credit-card-processor",
    [string]$AKSCluster = "dev-aks",
    [string]$ResourceGroup = "rg_prod"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Full AKS Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Frontend Tag: $FrontendTag" -ForegroundColor Yellow
Write-Host "Backend Tag:  $BackendTag" -ForegroundColor Yellow
Write-Host "ACR:          $ACRName" -ForegroundColor Yellow
Write-Host "Namespace:    $Namespace" -ForegroundColor Yellow
Write-Host "AKS Cluster:  $AKSCluster" -ForegroundColor Yellow
Write-Host ""

# Step 1: Ensure AKS credentials
Write-Host "[1/11] Getting AKS credentials..." -ForegroundColor Green
az aks get-credentials --resource-group $ResourceGroup --name $AKSCluster --overwrite-existing
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to get AKS credentials"
    exit 1
}

# Step 2: Login to ACR
Write-Host "[2/11] Logging into Azure Container Registry..." -ForegroundColor Green
az acr login --name $ACRName
if ($LASTEXITCODE -ne 0) {
    Write-Error "ACR login failed"
    exit 1
}

# Step 3: Build frontend image
Write-Host "[3/11] Building frontend Docker image..." -ForegroundColor Green
docker build -t "$ACRName.azurecr.io/expense-frontend:$FrontendTag" .
if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend Docker build failed"
    exit 1
}

# Step 4: Push frontend image
Write-Host "[4/11] Pushing frontend image to ACR..." -ForegroundColor Green
docker push "$ACRName.azurecr.io/expense-frontend:$FrontendTag"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend Docker push failed"
    exit 1
}

# Step 5: Build backend image
Write-Host "[5/11] Building backend Docker image..." -ForegroundColor Green
docker build -t "$ACRName.azurecr.io/expense-backend:$BackendTag" -f backend/Dockerfile ./backend
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend Docker build failed"
    exit 1
}

# Step 6: Push backend image
Write-Host "[6/11] Pushing backend image to ACR..." -ForegroundColor Green
docker push "$ACRName.azurecr.io/expense-backend:$BackendTag"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend Docker push failed"
    exit 1
}

# Step 7: Delete existing backend pods
Write-Host "[7/11] Deleting existing backend pods..." -ForegroundColor Green
kubectl delete pods -l app=backend -n $Namespace
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to delete backend pods (may not exist yet)"
}

# Step 8: Update backend deployment
Write-Host "[8/11] Updating backend deployment..." -ForegroundColor Green
kubectl set image deployment/backend "backend=$ACRName.azurecr.io/expense-backend:$BackendTag" -n $Namespace
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend deployment update failed"
    exit 1
}

# Step 9: Wait for backend rollout
Write-Host "[9/11] Waiting for backend rollout..." -ForegroundColor Green
kubectl rollout status deployment/backend -n $Namespace --timeout=5m
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend rollout failed or timed out"
    exit 1
}

# Step 10: Delete existing frontend pods
Write-Host "[10/11] Deleting existing frontend pods..." -ForegroundColor Green
kubectl delete pods -l app=frontend -n $Namespace
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to delete frontend pods (may not exist yet)"
}

# Step 11: Update frontend deployment
Write-Host "[11/11] Updating frontend deployment..." -ForegroundColor Green
kubectl set image deployment/frontend "frontend=$ACRName.azurecr.io/expense-frontend:$FrontendTag" -n $Namespace
if ($LASTEXITCODE -ne 0) {
    Write-Error "Frontend deployment update failed"
    exit 1
}

# Wait for frontend rollout
Write-Host ""
Write-Host "Waiting for frontend rollout..." -ForegroundColor Cyan
kubectl rollout status deployment/frontend -n $Namespace --timeout=5m

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Frontend: $ACRName.azurecr.io/expense-frontend:$FrontendTag" -ForegroundColor Green
    Write-Host "Backend:  $ACRName.azurecr.io/expense-backend:$BackendTag" -ForegroundColor Green

    # Show deployment status
    Write-Host ""
    Write-Host "Current deployments:" -ForegroundColor Cyan
    kubectl get deployments -n $Namespace

    Write-Host ""
    Write-Host "Current pods:" -ForegroundColor Cyan
    kubectl get pods -n $Namespace

    Write-Host ""
    Write-Host "Services:" -ForegroundColor Cyan
    kubectl get services -n $Namespace
} else {
    Write-Error "Frontend deployment rollout failed or timed out"
    exit 1
}
