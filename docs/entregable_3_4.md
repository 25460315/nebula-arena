# Entregable 3.4 — Reporte Técnico de Autoescalado, Monitoreo y Pruebas de Carga en AWS

**Proyecto:** Nebula Arena (Shooter 5v5 en Amazon EKS + Agones + Amazon CloudFront)  
**Región:** `us-east-1` | **Cuenta AWS:** `131470772842`  
**Allocator Endpoint:** `a71c21b2774ff4240bf13bf6e8ca8d44-259804529.us-east-1.elb.amazonaws.com`  
**Distribución CloudFront:** `https://d36d1uciy62mmx.cloudfront.net` (`s3://nebula-stream-131470772842`)  
**Generador de Carga:** EC2 `c7i.2xlarge` (`54.174.30.167`, Ubuntu 24.04 LTS en `us-east-1`)

---

## 1. Arquitectura de Observabilidad y las Tres Capas de Autoescalado

La plataforma instrumenta las cuatro señales doradas (latencia, tráfico, errores y saturación) mediante `kube-prometheus-stack` y un `PodMonitor` (`nebula-gameservers`) que recolecta cada `5 s` el endpoint `:9100/metrics` de los pods `GameServer`, junto con el `ServiceMonitor` nativo de Agones.

| Capa | Recurso / Objeto | Herramienta en AWS | Métrica Disparadora | Configuración Aplicada |
| :--- | :--- | :--- | :--- | :--- |
| **1. Partidas (Con estado)** | `GameServer` / `Fleet` (`nebula-fleet`) | Agones `FleetAutoscaler` (`nebula-autoscaler`) | Porcentaje de servidores `Ready` libres (*buffer*) | `bufferSize: 20%`, `minReplicas: 3`, `maxReplicas: 200` |
| **2. Servicios sin estado** | `Deployment` (`matchmaker`) | Kubernetes `HorizontalPodAutoscaler` (`matchmaker-hpa`) | Utilización media de CPU | `averageUtilization: 60%`, `min: 2`, `max: 30`, `stabilizationWindow: 300s` |
| **3. Infraestructura** | Nodos EC2 (`c7i.xlarge` / 4 vCPU, 8 GiB) | EKS Managed Node Group Autoscaler | Pods en estado `Pending` / Escalado de Nodegroup | `minSize: 3`, `maxSize: 12`, `desiredSize: 10` |

### Consultas PromQL del Tablero de Grafana

| Panel | Consulta PromQL | Meta (SLO) |
| :--- | :--- | :--- |
| **1. Jugadores conectados (CCU)** | `sum(nebula_players_connected)` | Hasta 1,000 CCU (100 partidas 5v5) |
| **2. Duración del tick p99 (ms)** | `histogram_quantile(0.99, sum by (le) (rate(nebula_tick_seconds_bucket[1m]))) * 1000` | `< 25 ms` (50% del periodo de tick de `50 ms` a 20 Hz) |
| **3. Servidores por estado** | `sum by (type) (agones_gameservers_count{fleet_name="nebula-fleet"})` | `Ready >= 20%` del total de la flota |
| **4. Nodos del clúster** | `count(kube_node_info)` | Escalado elástico entre 3 y 12 nodos |

---

## 2. Resultados Reales de las Pruebas de Carga (`rampa`, `pico` y `stream`)

| Escenario | Peticiones Totales | Fallos (`%`) | Latencia Mediana (`p50`) | Latencia Promedio | Latencia `p95` | Latencia `p99` | Throughput (`req/s`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Rampa (`WS rtt`, 1,000 CCU)** | `18,795` | `0 (0.00%)` | `3 ms` | `3.46 ms` | **`7 ms`** | **`8 ms`** | `78.31 req/s` |
| **Rampa (`WS asignacion`)** | `23` | `0 (0.00%)` | `480 ms` | `484.46 ms` | `600 ms` | `620 ms` | `0.10 req/s` |
| **Pico (`WS rtt`, 1,000 CCU @ 50/s)** | `32,216` | `0 (0.00%)` | `3 ms` | `3.45 ms` | **`7 ms`** | **`7 ms`** | `268.28 req/s` |
| **Pico (`WS asignacion`)** | `36` | `0 (0.00%)` | `510 ms` | `532.12 ms` | `1,000 ms` | `1,100 ms` | `0.30 req/s` |
| **Stream HLS (`GET manifiesto`)** | `49,248` | `0 (0.00%)` | `21 ms` | `22.02 ms` | **`38 ms`** | **`46 ms`** | `246.02 req/s` |
| **Stream HLS (`GET segmento`)** | `49,223` | `5 (0.01%)` | `31 ms` | `31.61 ms` | **`49 ms`** | **`67 ms`** | `245.90 req/s` |

### Análisis de las Tres Gráficas
1. **Gráfica 1 — Curva CCU vs Latencia RTT p95 (`loadtest/ccu_vs_p95.png`):**
   - En el arranque (`0–50 CCU`), el percentil 95 agregado refleja las primeras llamadas HTTPS mTLS a `agones-allocator` (`~370–440 ms`) mientras aún hay pocas muestras de `rtt`.
   - A partir de `50 CCU` y hasta alcanzar los **`1,000 jugadores concurrentes (CCU)`**, la latencia `p95` se mantiene completamente plana en **`7 ms`** (`p99 = 8 ms`), más de $10\times$ por debajo del umbral máximo permitido (`meta p95 = 80 ms`), con **`0.00%` de desconexiones**.
2. **Gráfica 2 — Línea de Tiempo de `GameServers` (`Ready` / `Allocated`) y Nodos del Clúster:**
   - **Capa de Partidas (`FleetAutoscaler`):** Reacciona en **`3 a 5 segundos`** creando nuevos pods `nebula-fleet` en cuanto el buffer de servidores `Ready` baja del `20%`.
   - **Capa de Infraestructura (Nodos EC2 en EKS):** El escalado del nodegroup de `3` a `10` instancias `c7i.xlarge` tardó **`~95 segundos`** en registrar los nuevos nodos en estado `Ready` dentro de EKS.
3. **Gráfica 3 — Tasa de Errores y Rebuffering durante el Pico:**
   - En el escenario `pico` (`r = 50 jugadores/s`), la latencia de asignación (`WS asignacion`) subió de `480 ms` (mediana) a `1,000 ms` (`p95`) por la concurrencia sobre `agones-allocator`, pero mantuvo **`0%` de fallos** una vez disponibles los 10 nodos.
   - En el escenario `stream` (`500 espectadores concurrentes` descargando segmentos HLS de `~212.6 KB` cada `2 s`, `98,471` peticiones totales), solo `5` segmentos superaron los `2 s`, logrando un **rebuffering ratio de `0.01%`** (meta `< 1%`) y `p95 = 49 ms`.

---

## 3. Capacidad Máxima Medida por Nodo

Cada nodo **`c7i.xlarge`** cuenta con **4 vCPU (`4,000m`) y 8 GiB de RAM**. Restando el sobrecosto del sistema operativo, `kubelet`, `aws-node`, `kube-proxy` y monitoreo (`~650m` vCPU), quedan **`~3,350m` vCPU alocables**:

$$\text{GameServers por nodo} = \left\lfloor \frac{3,350\text{m}}{250\text{m (request por pod)}} \right\rfloor = 13\text{ GameServers por nodo}$$

Descontando el `20%` de buffer en estado `Ready`, cada nodo sostiene **`10 a 11 partidas activas (100 a 110 jugadores concurrentes por nodo)`** con una duración de tick `p99 < 5 ms` y RTT `p95 = 7 ms`. Con **10 nodos `c7i.xlarge`**, el clúster soporta los **1,000 CCU** (`100 Allocated` + `25 Ready` = `125 pods`).

---

## 4. Extrapolación de Egress y Costo de Streaming (20,000 Espectadores a 1080p)

Aplicando la fórmula de transferencia de salida (*egress*) para **$20,000\text{ espectadores (CCV)}$** viendo una partida en **1080p a $6,000\text{ kbps}$** durante **1 hora**:

$$\text{GB/hora} = \frac{20,000 \times 6,000\text{ kbps} \times 3,600\text{ s}}{8 \times 10^6} = 54,000\text{ GB/hora} = \mathbf{54.00\text{ TB/hora}}$$

- **Costo estimado en Amazon CloudFront (`$0.085 USD / GB`):**
  $$\text{Costo por hora} = 54,000\text{ GB} \times \$0.085 = \mathbf{\$4,590.00\text{ USD / hora}}$$
  *(Aplicando tramos progresivos de CloudFront en `us-east-1` de `$0.085/GB` los primeros 10 TB y `$0.080/GB` los siguientes 40 TB: $\approx \mathbf{\$4,371.20\text{ USD / hora}}$).*

---

## 5. Recomendación de Configuración Justificada

1. **Tipo de máquina:** **`c7i.xlarge` (`$0.1785/h` On-Demand)** o **`c7g.xlarge` (`$0.1450/h`)**. Proporciona una densidad óptima de ~100 jugadores por nodo sin que un fallo de hardware afecte a más del 10% de una cohorte de 1,000 jugadores.
2. **Mínimo de nodos (`minSize`):** **`4 nodos`** en horas valle (~400 CCU de capacidad inmediata) y pre-escalado programado a **`10 nodos`** 10 minutos antes de eventos pico, compensando los `~95 s` de arranque de EC2.
3. **`FleetAutoscaler`:** Configurar **`bufferSize: 25%`** y **`minReplicas: 25`** para absorber ráfagas de matchmaking (`50 jugadores/s`) sin elevar la latencia de asignación por encima de `500 ms`.
