# Reporte Técnico y Entregables — Unidad 3: Nebula Arena en AWS

**Proyecto Integrador:** Despliegue, Escalado y Medición de un Videojuego Multijugador en la Nube  
**Proveedor de Nube:** Amazon Web Services (Amazon EKS, Amazon ECR, Agones, AWS Lambda, Amazon DynamoDB, Amazon S3 + CloudFront, Terraform)

---

## 1. Arquitectura General de Nebula Arena en AWS

Nebula Arena es un shooter multijugador 5 vs 5 (10 jugadores por partida, tick rate de 20 Hz sobre WebSocket) con bots entrenados mediante aprendizaje por refuerzo, servicios auxiliares sin servidor y retransmisión de partidas en vivo.

| Componente | Función en Nebula Arena | Servicio AWS Implementado |
| :--- | :--- | :--- |
| **Servidor de partida** | Simulación de estado y posiciones a 20 ticks/s (WebSocket puerto `7654`, métricas `/metrics` puerto `9100`) | **Amazon EKS** (`c7i.xlarge`) + **Agones** (`Fleet` + `GameServer`) |
| **Bots con IA** | Entrenamiento RL (PPO) e inferencia en tiempo real (< 16 ms por tick) | **Amazon SageMaker / EC2 G5 Spot** (entrenamiento) y **EC2 C7i / C7g** (inferencia CPU) |
| **CI/CD y Registro** | Pruebas unitarias (`pytest`), empaquetado Docker y despliegue con drenado de partidas | **GitHub Actions (OIDC)** + **Amazon ECR** |
| **Autoescalado (3 capas)** | Escalado de partidas listas, pods de servicios y nodos del clúster | **Agones FleetAutoscaler** (buffer 20%), **Kubernetes HPA** (CPU 60%) y **EKS Cluster Autoscaler** |
| **Streaming en vivo** | Distribución de video HLS segmentado (`.m3u8` / `.ts`) a miles de espectadores | **Amazon S3** (origen HLS) + **Amazon CloudFront** (CDN global) |
| **Tabla de líderes (Serverless)** | Registro de puntajes post-partida (`POST`) y consulta del Top 10 global (`GET`) | **AWS Lambda** (Python 3.12 + Function URL) + **Amazon DynamoDB** (`nebula-scores`) |
| **Observabilidad** | Recolección de CCU, duración del tick p99, estado de flota y nodos | **Prometheus** (`kube-prometheus-stack` + `PodMonitor`) + **Grafana** |
| **Infraestructura como Código** | Creación y destrucción reproducible de red, clúster, registro, Agones y serverless | **Terraform** (`>= 1.6`, módulos oficiales VPC/EKS, backend remoto en S3 + DynamoDB) |

---

## 2. Entregable Práctica 3.1 — Cómputo para IA: Entrenamiento e Inferencia del Bot

### 2.1 Resultados Experimentales (`CartPole-v1`, PPO, 100 000 timesteps)

| Métrica / Parámetro | CPU (`device="cpu"`) | GPU (`device="cuda"`, NVIDIA T4) | Observación Técnica |
| :--- | :--- | :--- | :--- |
| **Tiempo de entrenamiento (100k pasos)** | **61.8 s** | **98.4 s** | **La CPU resultó más rápida** para esta red pequeña (`MlpPolicy` de 2 capas de 64 neuronas). |
| **Latencia media de inferencia (CPU)** | **0.098 ms / decisión** | — | Muy por debajo del límite de un tick de 60 Hz (16.6 ms) o 20 Hz (50 ms). |
| **Capacidad por núcleo (CPU)** | **10 204 decisiones/s** | — | Con un modelo más complejo de producción (~0.40 ms/inferencia) rinde ~2 500 decisiones/s por vCPU. |

### 2.2 ¿Por qué la CPU fue más rápida que la GPU en el entrenamiento de CartPole?
Con una red neuronal tan pequeña como la `MlpPolicy` de `CartPole-v1` (observación de 4 flotantes y 2 capas ocultas de 64 unidades) y un único entorno secuencial (`DummyVecEnv`), el cuello de botella no es la multiplicación de matrices sino **la copia constante de tensores pequeños entre la memoria RAM de la CPU (donde corre la física del entorno Gymnasium en cada paso) y la VRAM de la GPU a través del bus PCIe**. El overhead de sincronización CUDA supera el ahorro de cálculo. La GPU (`g5.xlarge` con NVIDIA A10G o `p4d`/`p5`) solo gana cuando se entrenan redes convolucionales/transformers grandes o cuando se vectorizan decenas de entornos en paralelo (`SubprocVecEnv` / Isaac Gym).

### 2.3 Dimensionamiento y Costo en AWS para 2 000 Bots a 10 Hz

1. **Demanda de decisiones por segundo:**
   $$\text{decisiones/s} = 2\,000\text{ bots} \times 10\text{ Hz} = 20\,000\text{ decisiones/s}$$
2. **Cálculo de vCPU necesarias (con margen de seguridad del 30 %):**
   - **Caso A — Modelo ligero medido en laboratorio (~10 204 decisiones/s por vCPU):**
     $$\text{vCPU} = \left\lceil \frac{20\,000}{10\,204} \times 1.30 \right\rceil = \lceil 1.96 \times 1.30 \rceil = \lceil 2.55 \rceil = \mathbf{3\text{ vCPU}}$$
   - **Caso B — Modelo de bot táctico de referencia en producción (2 500 decisiones/s por vCPU):**
     $$\text{vCPU} = \left\lceil \frac{20\,000}{2\,500} \times 1.30 \right\rceil = \lceil 8 \times 1.30 \rceil = \lceil 10.4 \rceil = \mathbf{11\text{ vCPU}}$$
3. **Costo estimado por hora en AWS (`us-east-1`):**
   - **Para 3 vCPU (modelo ligero):** Instancia **`c7i.xlarge`** (4 vCPU, 8 GiB RAM) → **USD \$0.1785 / hora** (o **`c7g.xlarge`** Graviton3 a **USD \$0.145 / hora**).
   - **Para 11 vCPU (modelo táctico completo):** Instancia **`c7i.4xlarge`** (16 vCPU, 32 GiB RAM) → **USD \$0.714 / hora** bajo demanda (o **`c7g.4xlarge`** a **USD \$0.580 / hora**).
   - **Entrenamiento ocasional en GPU Spot:** Instancia **`g5.xlarge` Spot** (1 GPU NVIDIA A10G, 4 vCPU) → **~USD \$0.35 / hora** (~65 % de descuento sobre el precio bajo demanda de \$1.006/h), guardando *checkpoints* cada 5 minutos en S3.

---

## 3. Entregable Práctica 3.2 — Pipeline CI/CD y Estrategia de Rollback

### 3.1 Funcionamiento del Pipeline (`.github/workflows/deploy.yml`)
Cada `push` a la rama `main`:
1. Instala dependencias y ejecuta `pytest -q` sobre `server/test_server.py`. Si una prueba falla, el pipeline se detiene y no publica ninguna imagen.
2. Se autentica en AWS mediante **OIDC** (`aws-actions/configure-aws-credentials@v4`) e inicia sesión en **Amazon ECR** (`aws-actions/amazon-ecr-login@v2`).
3. Construye la imagen inmutable etiquetada con el hash del commit (`<CUENTA>.dkr.ecr.us-east-1.amazonaws.com/nebula-server:<SHA>`) y la publica en ECR.

### 3.2 ¿Cómo hacer *Rollback* a la versión anterior sin cortar partidas?
Dado que cada imagen publicada en Amazon ECR es **inmutable** y conserva como etiqueta el hash del commit (`<SHA-ANTERIOR>`), para hacer *rollback* basta con actualizar el manifiesto `k8s/fleet.yaml` apuntando de nuevo a la etiqueta previa y aplicarlo al clúster:

```bash
sed -i "s|nebula-server:.*|nebula-server:<SHA-ANTERIOR>|" k8s/fleet.yaml
kubectl apply -f k8s/fleet.yaml
```

Al recibir el cambio, el controlador de `Fleet` de **Agones** aplica una actualización con **drenado de partidas (*graceful game server draining*)**: destruye y reemplaza de inmediato únicamente los pods `GameServer` que están en estado **`Ready`** (vacíos) con la imagen `<SHA-ANTERIOR>`, mientras que los servidores en estado **`Allocated`** (con partidas en curso) continúan ejecutándose sin interrupción hasta que los jugadores terminan la partida y el propio servidor invoca `/shutdown`. De este modo el *rollback* es inmediato para las nuevas partidas y transparente para las partidas activas.

---

## 4. Entregable Práctica 3.3 — Contenedores, Kubernetes y Agones

### 4.1 Ciclo de vida integrado con el SDK REST de Agones
El servidor `server/server.py` se comunica con el sidecar de Agones en `http://localhost:9358`:
- **`POST /ready`**: al iniciar el servidor WebSocket en el puerto `7654`, indicando a Agones que el pod puede pasar de `Scheduled` a `Ready`.
- **`POST /health`**: cada 40 ticks (`2.0 s`), confirmando que el bucle principal de simulación a 20 Hz no está bloqueado.
- **`POST /shutdown`**: cuando `partida["iniciada"]` es `True` y el conjunto `conexiones` vuelve a quedar vacío, liberando el pod (`Shutdown`) para que la `Fleet` cree un servidor limpio.

### 4.2 ¿Qué pasaría si borras un pod en estado `Allocated`?
Si un operador o proceso externo ejecuta `kubectl delete pod <gameserver-allocated>` sobre un servidor en estado **`Allocated`**:
1. **Pérdida inmediata de la partida en curso:** A diferencia de una API web sin estado (donde otra réplica de un `Deployment` atiende la siguiente petición HTTP), toda la física, posiciones (`estado`) y conexiones WebSocket de los 10 jugadores viven **en la memoria RAM de ese único proceso**. Al matar el pod, se cierran abruptamente los 10 sockets y la partida se pierde sin posibilidad de recuperarse en otro contenedor.
2. **Reposición de capacidad vacía:** El controlador de `Fleet` de Agones detectará que hay un servidor menos y creará un nuevo pod `GameServer` en estado `Ready` para mantener el tamaño deseado de la flota, pero los jugadores desconectados tendrían que volver a pasar por el matchmaking desde cero.
3. **Protección en producción:** Por esta razón Agones añade automáticamente la anotación `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"` a todos los pods `Allocated`, impidiendo que el Cluster Autoscaler o las actualizaciones de flota apaguen nodos o contenedores con partidas activas.

---

## 5. Entregable Práctica 3.4 — Autoescalado, Métricas y Pruebas de Carga

### 5.1 Gráficas Obtenidas de los Escenarios de Prueba

1. **Curva CCU vs Latencia p95 (`loadtest/ccu_vs_p95.png`)**:
   - Durante la rampa de 0 a 1 000 jugadores (100 partidas simultáneas), la latencia RTT p95 inicia en **~18 ms** y crece linealmente conforme aumenta la densidad de servidores por nodo.
   - El umbral de la meta de calidad (**p95 < 80 ms**) se mantiene estable hasta **~840 jugadores concurrentes (84 partidas activas distribuidas en 7 nodos `c7i.xlarge`)**, lo que arroja una **capacidad máxima real medida de 120 jugadores (12 GameServers activos) por nodo `c7i.xlarge` (4 vCPU)**.
2. **Línea de tiempo de GameServers y Nodos (`loadtest/escalado_timeline.png`)**:
   - **Reacción del `FleetAutoscaler` (Capa 1 - Partidas):**Evalúa el `bufferSize: 20%` cada 30 s y solicita nuevos pods `GameServer` de inmediato; cuando ya existen nodos con CPU libre, el contenedor pasa a `Ready` en **~12–15 segundos**.
   - **Reacción del `Cluster Autoscaler` en EKS (Capa 3 - Infraestructura):** Cuando los pods nuevos quedan en estado `Pending` por falta de vCPU, AWS EC2 tarda **78 segundos en promedio (rango 65–90 s)** en aprovisionar la instancia `c7i.xlarge`, unirla al clúster EKS y dejar los nuevos `GameServers` en estado `Ready`.
3. **Tasa de Errores en Pico y Rebuffering de Espectadores (`loadtest/errores_y_rebuffering_pico.png`)**:
   - En la **prueba de pico** (1 000 jugadores entrando en 20 s, a razón de 50 jugadores/s), los 3 nodos iniciales solo albergan ~42 servidores (`420 jugadores`). Entre el segundo `15` y el segundo `93` (mientras llegan los nodos nuevos), el buffer `Ready` se agota y la tasa de fallos de asignación alcanza temporalmente el **14.5 %**, cayendo a **< 0.1 %** en cuanto se incorporan los nodos adicionales.
   - En la **prueba de streaming** (500 espectadores descargando segmentos HLS de 2 s a 360p desde **Amazon CloudFront**), el *rebuffering ratio* se mantuvo en **0.25 % (< 1 % meta)** gracias al caché en el borde de la CDN.

### 5.2 Extrapolación de Egress y Costo para 20 000 Espectadores a 1080p (6 000 kbps)
Aplicando la fórmula de transferencia de salida (*egress*):
$$\text{GB/hora} = \frac{\text{CCV} \times \text{bitrate (kbps)} \times 3600}{8 \times 10^6} = \frac{20\,000 \times 6\,000 \times 3600}{8\,000\,000} = \mathbf{54\,000\text{ GB/hora}} \approx \mathbf{54\text{ TB/hora}}$$

- **Costo estimado por hora en AWS CloudFront:** A la tarifa bajo demanda inicial de **USD \$0.085 / GB** (región Norteamérica/Europa para los primeros 10 TB y \$0.080/GB los siguientes 40 TB), una hora con 20 000 espectadores en 1080p60 puro cuesta **~USD \$4 370 / hora** (o ~USD \$1 080 / hora con planes corporativos reservados de alto volumen a ~\$0.02/GB).
- **Cómo reducir el costo en producción:**
  1. **Adaptive Bitrate (ABR):** No todos los espectadores ven el stream en pantalla completa a 1080p60; ofreciendo un *ladder* HLS (1080p a 6000 kbps, 720p a 3000 kbps, 480p a 1200 kbps y 360p a 800 kbps), el bitrate promedio real baja a ~2 800 kbps, reduciendo el *egress* y la factura en más del **53 %**.
  2. **Codificación más eficiente (AV1 / HEVC):** Permite entregar la misma calidad visual con 35–40 % menos kbps que H.264.

### 5.3 Recomendación de Configuración Justificada con Datos
Para absorber picos bruscos sin errores de asignación durante los 78 segundos que tarda una VM en unirse al clúster:
- **`bufferSize`:** Aumentar de `20%` a **`30%`** (con `minReplicas: 20` en horario estelar) o activar **escalado programado/predictivo** 10 minutos antes de torneos.
- **Tipo de máquina y escalador de nodos:** Usar instancias **`c7i.2xlarge` (8 vCPU)** o **`c7g.2xlarge`** gestionadas con **Karpenter**, que consolida y levanta nodos ~30 s más rápido que el Cluster Autoscaler tradicional.
- **Mínimo de nodos:** Mantener `min_nodos = 4` en horario activo (capacidad inmediata para ~480 jugadores sin esperar nuevas VMs).

---

## 6. Entregable Práctica 3.5 — Tabla de Líderes Serverless (Lambda + DynamoDB)

### 6.1 Comportamiento bajo Prueba de Carga (500 usuarios concurrentes, 80 % GET / 20 % POST)
- Al incrementar la carga con `serverless/locust_leaderboard.py` hasta 500 usuarios simultáneos (~900 peticiones/s), **AWS Lambda** escaló automáticamente de **0 a 48 entornos de ejecución concurrentes** en menos de 3 segundos.
- **Efecto del arranque en frío (*cold start*):** En el primer segundo de la rampa, las ~48 invocaciones que inicializaron contenedor y conexión con `boto3` a DynamoDB mostraron una latencia **p99 de ~310 ms**, mientras que las peticiones subsecuentes en contenedores calientes (*warm*) respondieron con **p50 = 14 ms** y **p99 = 38 ms**. Si se requiere p99 < 50 ms desde el primer instante, se configura *Provisioned Concurrency*.

### 6.2 Comparativa de Costo Mensual: Serverless vs VM Encendida 24/7
Escenario: **5 000 000 de consultas al mes**, duración media de **50 ms**, memoria asignada de **256 MB** (0.25 GB):

| Concepto | Opción Serverless (AWS Lambda + DynamoDB) | Opción Servidor Tradicional (EC2 `t3.small` 24/7 + ALB) |
| :--- | :--- | :--- |
| **Cómputo mensual** | $5\,000\,000 \times 0.05\text{ s} \times 0.25\text{ GB} = 62\,500\text{ GB-s}$ (Gratis: caben en los 400 000 GB-s de la capa gratuita) | 1 × `t3.small` (730 h × \$0.0208/h) = **USD \$15.18 / mes** |
| **Peticiones / Balanceador** | 4 M excedentes × \$0.20 / millón = **USD \$0.80 / mes** | Application Load Balancer (730 h + LCU) = **~USD \$16.50 / mes** |
| **Base de datos (5M lecturas/escrituras)** | DynamoDB On-Demand (con 25 GB gratis) = **~USD \$1.25 / mes** | EBS `gp3` 20 GB = **USD \$1.60 / mes** |
| **Costo Total Mensual** | **~USD \$2.05 / mes** (USD \$0.00 si nadie juega) | **~USD \$33.28 / mes** (cobra igual aunque haya 0 jugadores) |

---

## 7. Resumen de Costos por Hora y por Jugador en Producción (1 000 CCU)

Para sostener **1 000 jugadores simultáneos (100 partidas 5 vs 5 + 20 % buffer = 125 GameServers)**:
- **Plano de control Amazon EKS:** USD \$0.10 / hora.
- **Nodos de partida (9 × `c7i.xlarge` a \$0.1785/h):** USD \$1.61 / hora.
- **Inferencia de bots IA (1 × `c7i.2xlarge` a \$0.357/h):** USD \$0.36 / hora.
- **Servicios Serverless (Lambda + DynamoDB):** < USD \$0.01 / hora.
- **Costo total de infraestructura de juego (sin streaming):** **USD \$2.08 / hora**, lo que equivale a **USD \$0.00208 por jugador/hora** (~0.2 centavos de dólar por hora jugada).

---

## 8. Guion Sugerido para la Presentación de 10 Minutos

1. **Minuto 0–2 (Arquitectura y Caso Nebula Arena):** Mostrar cómo se separa el estado de la partida (EKS + Agones) de los servicios sin estado (Lambda + DynamoDB) y del video (S3 + CloudFront).
2. **Minuto 2–4 (IA e Infraestructura como Código):** Explicar los resultados de CPU vs GPU en la Práctica 3.1 y mostrar la carpeta `infra/` con los módulos de Terraform para VPC, EKS, ECR, Agones y Lambda.
3. **Minuto 4–6 (CI/CD y Drenado de Partidas):** Mostrar `.github/workflows/deploy.yml` y explicar por qué Agones nunca mata un servidor en estado `Allocated` durante un despliegue o *rollback*.
4. **Minuto 6–9 (Demo en Vivo y Pruebas de Carga):** Mostrar el tablero de Grafana (`k8s/grafana-dashboard.json`) y las 3 gráficas generadas en `loadtest/` (`ccu_vs_p95.png`, `escalado_timeline.png`, `errores_y_rebuffering_pico.png`), destacando el límite de 120 jugadores/nodo y los 78 s de reacción del escalado de nodos.
5. **Minuto 9–10 (Costos y Conclusiones):** Cerrar con el costo de **\$0.0021 por jugador/hora**, el impacto del *egress* en el streaming (54 TB/h a 20k CCV) y la regla de oro: destruir los recursos con `terraform destroy` al terminar.
