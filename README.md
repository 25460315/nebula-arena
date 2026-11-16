# Nebula Arena — Infraestructura y Despliegue en AWS (`us-east-1`)

Repositorio oficial del **Proyecto Integrador y las 6 Prácticas de la Unidad 3** (Variante 100% AWS: Amazon EKS, Agones, Amazon ECR, GitHub Actions OIDC, Prometheus/Grafana, Locust, Amazon S3 + CloudFront, AWS Lambda + DynamoDB y Terraform).

---

## Estructura Modular del Repositorio

```text
nebula-arena/
├── .github/workflows/
│   └── deploy.yml                   # Práctica 3.2: Pipeline CI/CD (pytest -> OIDC -> Amazon ECR)
├── bot/
│   ├── requirements.txt             # Práctica 3.1: gymnasium + stable-baselines3
│   └── train_bot.py                 # Práctica 3.1: Entrenamiento PPO (CPU vs GPU) y benchmark inferencia
├── server/
│   ├── server.py                    # Práctica 3.3: Servidor 5v5 WebSocket (20 Hz), Prometheus y SDK Agones
│   ├── requirements.txt             # Práctica 3.3: websockets==12.0, prometheus-client==0.20.0
│   ├── Dockerfile                   # Práctica 3.3: python:3.11-slim, puertos 7654/9100, USER 1000
│   └── test_server.py               # Práctica 3.3 / 3.2: Pruebas unitarias pytest
├── k8s/
│   ├── fleet.yaml                   # Práctica 3.3: Fleet nebula-fleet (Agones)
│   ├── allocation.yaml              # Práctica 3.3: GameServerAllocation
│   ├── autoscaler.yaml              # Práctica 3.4: FleetAutoscaler (buffer 20%) + HPA
│   └── podmonitor.yaml              # Práctica 3.4: PodMonitor para Prometheus (cada 5s)
├── loadtest/
│   ├── locustfile.py                # Práctica 3.4: Jugador (WS 20 Hz + ping RTT) y Espectador (HLS 360p)
│   ├── analisis.py                  # Práctica 3.4: Curva CCU vs p95 y extrapolación de egress CloudFront
│   ├── ccu_vs_p95.png               # Práctica 3.4: Gráfica real generada (1,000 CCU)
│   ├── rampa_stats.csv              # Práctica 3.4: Métricas reales escenario Rampa
│   ├── pico_stats.csv               # Práctica 3.4: Métricas reales escenario Pico
│   └── stream_stats.csv             # Práctica 3.4: Métricas reales escenario Streaming HLS
├── serverless/
│   ├── lambda_function.py           # Práctica 3.5: AWS Lambda (Python 3.12) + DynamoDB nebula-scores
│   ├── function.zip                 # Práctica 3.5: Paquete desplegable Lambda
│   └── locust_leaderboard.py        # Práctica 3.5: Prueba de carga 80% GET / 20% POST (500 usuarios)
├── infra/
│   ├── main.tf                      # Práctica 3.6: Providers AWS/Helm y backend S3 + DynamoDB Lock
│   ├── variables.tf                 # Práctica 3.6: Variables de región, proyecto y nodos
│   ├── red.tf                       # Práctica 3.6: Módulo VPC y Security Group TCP/UDP 7000-8000
│   ├── eks.tf                       # Práctica 3.6: Módulo EKS (nebula-default, c7i.xlarge) y ECR
│   ├── agones.tf                    # Práctica 3.6: Release Helm de Agones
│   ├── serverless.tf                # Práctica 3.6: Tabla DynamoDB y Lambda Function URL como código
│   └── outputs.tf                   # Práctica 3.6: Outputs de clúster y registro ECR
└── docs/
    ├── entregable_3_1.md            # Entregable Práctica 3.1 (Cómputo para IA)
    ├── entregable_3_2.md            # Entregable Práctica 3.2 (CI/CD y Rollback)
    ├── entregable_3_3.md            # Entregable Práctica 3.3 (Contenedores, EKS y Agones)
    ├── entregable_3_4.md            # Entregable Práctica 3.4 (Reporte Técnico de Autoescalado y Carga)
    ├── entregable_3_5.md            # Entregable Práctica 3.5 (Serverless vs EC2 24/7)
    ├── entregable_3_6.md            # Entregable Práctica 3.6 (Terraform IaC)
    ├── reporte_final_nebula_arena.md # Proyecto Integrador: Reporte Técnico Final Completo
    ├── guion_presentacion_10min.md  # Proyecto Integrador: Guion minuto a minuto y Demo en Vivo
    └── autoevaluacion_unidad3.md    # Respuestas a las 8 preguntas de Autoevaluación
```
