# Guion de Presentación y Demo en Vivo (10 Minutos) — Nebula Arena en AWS

**Objetivo:** Demostrar la arquitectura cloud-native de **Nebula Arena** en AWS (`us-east-1`), el ciclo CI/CD, la observabilidad en Grafana, el autoescalado de partidas con Agones y el costo por jugador.

---

## Estructura de Tiempos (10:00 min totales)

| Minuto | Bloque | Qué mostrar en pantalla | Mensaje clave a comunicar |
| :---: | :--- | :--- | :--- |
| **00:00 – 01:30** | **1. Arquitectura e IA (3.1)** | Diagrama de arquitectura en `docs/reporte_final_nebula_arena.md` y tabla `bot/train_bot.py` | "La partida con estado vive en EKS + Agones; todo lo que la rodea (leaderboard, video HLS) vive en servicios serverless y CDN. Para 2,000 bots a 10 Hz medimos `0.38 ms` por inferencia en CPU (`2,500 dec/s`), requiriendo solo `11 vCPU` (`$0.43/h` en Graviton3)." |
| **01:30 – 03:00** | **2. IaC con Terraform y CI/CD (3.6 y 3.2)** | Carpeta `infra/` (`eks.tf`, `agones.tf`) + pestaña GitHub Actions en verde (`e8aa906`) + Amazon ECR | "Con `terraform apply` creamos la VPC, el clúster `nebula-default`, los nodos `c7i.xlarge` con Amazon Linux 2023 y Agones. Cada push a `main` corre `pytest` y publica la imagen inmutable en ECR usando OIDC sin guardar llaves secretas." |
| **03:00 – 06:30** | **3. DEMO EN VIVO: Autoescalado y Grafana (3.3 y 3.4)** | Mitad izquierda: Terminal con `kubectl get gameservers -w` y Locust.<br>Mitad derecha: Tablero de Grafana (`http://localhost:3000`) | "Observamos en vivo cómo empiezan 3 GameServers en `Ready`. Al lanzar Locust, cada 10 jugadores llenan una sala que pasa a `Allocated`. En 3 a 5 segundos el `FleetAutoscaler` detecta que el buffer bajó del 20% y levanta nuevos pods `Ready` mientras la latencia RTT `p95` se mantiene en `7 ms`." |
| **06:30 – 08:30** | **4. Resultados 1,000 CCU, Streaming y Serverless (3.4 y 3.5)** | Gráfica `loadtest/ccu_vs_p95.png` + `curl` a la Function URL de Lambda + métrica de concurrencia en CloudWatch | "Soportamos 1,000 jugadores (~100 por nodo `c7i.xlarge`) con `0%` de fallos y `p95 = 7 ms`. En streaming HLS logramos `0.01%` de rebuffering en CloudFront y demostramos que 20,000 espectadores en 1080p generan `54 TB/h` (`$4,590/h`). El leaderboard en Lambda + DynamoDB cuesta `$0.80/mes` frente a `$16.78–$50/mes` de una VM." |
| **08:30 – 10:00** | **5. Costo por Jugador, Cierre yPreguntas** | Tabla financiera del reporte final | "El costo operativo total de la flota para 1,000 jugadores concurrentes es de `$2.35 USD/hora`, es decir, **`$0.00235 USD` (0.23 centavos) por jugador por hora**, y al terminar ejecutamos `terraform destroy` dejando `$0` en recursos huérfanos." |

---

## Comandos Listos para Copiar durante la Demo en Vivo (Minuto 03:00 – 06:30)

```powershell
# Terminal 1: Observar cómo Agones asigna y autoescala los GameServers en vivo
kubectl apply -f k8s/fleet.yaml -f k8s/autoscaler.yaml
kubectl get gameservers -w

# Terminal 2: Consultar el Top 10 en vivo desde la Lambda Function URL
curl.exe -X POST https://xbx6aq53ueopg4cn32ytbihsuy0cxveq.lambda-url.us-east-1.on.aws/ -H "Content-Type: application/json" -d '{\"jugador\":\"demo_live\",\"puntos\":2500}'
curl.exe https://xbx6aq53ueopg4cn32ytbihsuy0cxveq.lambda-url.us-east-1.on.aws/
```
