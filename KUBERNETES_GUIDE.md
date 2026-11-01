# ☸️ Kubernetes Deployment & Operations Guide

This guide walks through deploying the **Real-Time UPI Fraud Detection System** to a Kubernetes cluster using the manifests in `infra/k8s/`.

---

## 🎯 Architecture Overview

```
                         [UPI Payment Gateway Traffic]
                                       │
                                       ▼
                          ┌────────────────────────┐
                          │  Kubernetes Service    │
                          │  (upi-fraud-service)   │
                          └────────────┬───────────┘
                                       │ Load Balancer (Round Robin)
                   ┌───────────────────┴───────────────────┐
                   ▼                                       ▼
       ┌───────────────────────┐               ┌───────────────────────┐
       │   Pod 1: upi-fraud    │               │   Pod 2: upi-fraud    │
       │  (FastAPI + ML Engine)│               │  (FastAPI + ML Engine)│
       └───────────────────────┘               └───────────────────────┘
                   ▲                                       ▲
                   └───────────────────┬───────────────────┘
                                       │ Auto-Scales (2 to 10 Pods)
                          ┌────────────┴───────────┐
                          │  HPA (Horizontal Pod   │
                          │      Autoscaler)       │
                          │ (Target: 70% Avg CPU)  │
                          └────────────────────────┘
```

---

## 🛠️ Step 1: Prerequisites
* [Docker Desktop](https://www.docker.com/)
* [kubectl](https://kubernetes.io/docs/tasks/tools/)
* [Minikube](https://minikube.sigs.k8s.io/) (for local Kubernetes development)

---

## 🚀 Step 2: Build Image in Minikube's Docker Environment
When testing locally, configure your terminal to use Minikube's built-in Docker daemon:

```bash
# 1. Start your local cluster
minikube start --cpus=2 --memory=4096

# 2. Point local docker CLI to Minikube
# On Linux/macOS:
eval $(minikube docker-env)

# On Windows PowerShell:
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# 3. Build the image directly inside the cluster environment
docker build -t upi-fraud-engine:latest .
```

---

## 📦 Step 3: Deploy to Kubernetes

Apply the declarative manifests in order:

```bash
# Apply deployment (spins up 2 replicas with health probes)
kubectl apply -f infra/k8s/deployment.yaml

# Apply service (creates internal load-balanced DNS endpoint)
kubectl apply -f infra/k8s/service.yaml

# Apply autoscaler (HPA metrics target)
kubectl apply -f infra/k8s/hpa.yaml
```

---

## 🔍 Step 4: Verify Deployment Status

Check that the pods are running and healthchecks are passing:

```bash
# Check pod health
kubectl get pods -l app=upi-fraud-api

# Check service endpoint
kubectl get svc upi-fraud-service

# Check autoscaler status
kubectl get hpa upi-fraud-hpa
```

### Accessing the API Locally:
Forward the service port to your host machine:
```bash
kubectl port-forward svc/upi-fraud-service 8000:80
```
Open `http://localhost:8000` in your browser to view the live dashboard!

---

## 📈 Step 5: Testing Autoscaling Under Load
To simulate peak transaction traffic (e.g., sudden UPI spikes during a festival sale):

```bash
# Run a temporary load generator container
kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://upi-fraud-service/health; done"
```

In a separate terminal, watch the HPA automatically increase the replica count from 2 up to 10 pods:
```bash
kubectl get hpa upi-fraud-hpa --watch
```

---

## 🧹 Step 6: Teardown
```bash
kubectl delete -f infra/k8s/
```
