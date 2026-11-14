# Nebula Arena — Infraestructura y Despliegue de Videojuegos en la Nube (AWS)

Repositorio completo del **Proyecto Integrador y Prácticas 3.1 a 3.6** de la Unidad 3 (*Infraestructura y despliegue de videojuegos en la nube*), implementado para la ruta de **Amazon Web Services (AWS)**: Amazon EKS, Amazon ECR, Agones, AWS Lambda, Amazon DynamoDB, Amazon S3 + CloudFront, Prometheus/Grafana, Locust y Terraform.

## Estructura del Repositorio

```text
nebula-arena/
├── .github/workflows/
│   └── deploy.yml                  # Práctica 3.2: Pipeline CI/CD (pytest -> ECR -> EKS rolling drain)
├── bot_ia/
│   ├── train_and_benchmark.py      # Práctica 3.1: Entrenamiento PPO CartPole-v1 (CPU vs GPU) y latencia
│   └── practica_3_1_bot_nebula.ipynb # Notebook para SageMaker Studio Lab / Google Colab (T4 GPU)
├── server/
│   ├── server.py                   # Práctica 3.3: Servidor WebSocket 5v5 (20 Hz) + Agones SDK + Prometheus
│   ├── requirements.txt            # Dependencias del servidor (websockets, prometheus-client)
│   ├── Dockerfile                  # Imagen de contenedor inmutable (python:3.11-slim, usuario 1000)
│   └── test_server.py              # Pruebas unitarias ejecutadas en CI con pytest
├── k8s/
│   ├── fleet.yaml                  # Flota de Agones (nebula-fleet) con requests/limits y healthcheck
│   ├── autoscaler.yaml             # FleetAutoscaler (buffer 20%) + HPA de referencia (CPU 60%)
│   ├── podmonitor.yaml             # PodMonitor para recolectar /metrics (puerto 9100) en Prometheus
│   ├── allocation.yaml             # GameServerAllocation para pruebas manuales de asignación
│   └── grafana-dashboard.json      # Tablero de Grafana con los 4 paneles requeridos
├── loadtest/
│   ├── locustfile.py               # Práctica 3.4: Jugador (WebSocket + Allocator) y Espectador (HLS CDN)
│   ├── generar_stream_aws.sh       # Genera video HLS 360p con FFmpeg y lo publica en S3 + CloudFront
│   ├── ejecutar_escenarios.sh      # Ejecuta los escenarios rampa, pico y stream en Locust
│   ├── analizar_resultados.py      # Genera las 3 gráficas PNG y calcula la extrapolación de egress
│   ├── ccu_vs_p95.png              # Gráfica 1: Curva CCU vs Latencia p95
│   ├── escalado_timeline.png       # Gráfica 2: Línea de tiempo de GameServers y Nodos EKS
│   └── errores_y_rebuffering_pico.png # Gráfica 3: Errores en pico 10x y Rebuffering en CDN
├── serverless/
│   ├── lambda_function.py          # Práctica 3.5: Tabla de líderes en AWS Lambda + DynamoDB (nebula-scores)
│   └── locust_leaderboard.py       # Prueba de carga 80% GET / 20% POST con 500 usuarios
├── infra/
│   ├── main.tf                     # Práctica 3.6: Proveedores AWS/Helm y backend S3 con bloqueo
│   ├── variables.tf                # Variables parametrizables por entorno (dev/staging/prod)
│   ├── red.tf                      # Módulo VPC oficial + Security Group UDP/TCP 7000-8000
│   ├── eks.tf                      # Módulo EKS oficial (node group c7i.xlarge) + repositorio ECR
│   ├── agones.tf                   # Instalación automática de Agones vía Helm provider
│   ├── serverless.tf               # Tabla DynamoDB + Rol IAM + Función Lambda + Function URL
│   └── outputs.tf                  # Salidas del clúster, registro ECR y URL del leaderboard
└── docs/
    └── REPORTE_TECNICO_Y_ENTREGABLES.md # Reporte técnico completo (máx. 6 págs) y entregables 3.1–3.6
```

## Guía Rápida de Ejecución

### 1. Ejecutar Pruebas Unitarias y Servidor Local (Prácticas 3.2 y 3.3)
```bash
cd server
pip install -r requirements.txt pytest
pytest -q
docker build -t nebula-server:1.0 .
docker run -p 7654:7654 -p 9100:9100 nebula-server:1.0
```

### 2. Desplegar toda la Infraestructura en AWS con Terraform (Práctica 3.6)
```bash
cd infra
terraform init
terraform validate
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

### 3. Desplegar Flota y Autoescalado en EKS (Prácticas 3.3 y 3.4)
```bash
aws eks update-kubeconfig --region us-east-1 --name nebula-default
kubectl apply -f ../k8s/fleet.yaml -f ../k8s/autoscaler.yaml -f ../k8s/podmonitor.yaml
kubectl get gameservers
```

### 4. Generar Gráficas y Análisis de Carga (Práctica 3.4)
```bash
cd ../loadtest
python analizar_resultados.py
```

### 5. Destruir el Entorno al Terminar la Sesión (Control de Costos)
```bash
cd ../infra
terraform destroy
```
