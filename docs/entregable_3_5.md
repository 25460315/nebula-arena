# Entregable 3.5 — Tabla de Líderes Serverless con AWS Lambda y Amazon DynamoDB

**Proyecto:** Nebula Arena  
**Región:** `us-east-1` | **Cuenta AWS:** `131470772842`  
**Función Lambda:** `nebula-leaderboard` (Python 3.12, `256 MB`, Function URL: `https://xbx6aq53ueopg4cn32ytbihsuy0cxveq.lambda-url.us-east-1.on.aws/`)  
**Tabla DynamoDB:** `nebula-scores` (`PAY_PER_REQUEST`, llave de partición `jugador: S`)

---

## 1. Validación Funcional con `curl`

```bash
FUNCTION_URL="https://xbx6aq53ueopg4cn32ytbihsuy0cxveq.lambda-url.us-east-1.on.aws/"

# 1. Insertar/actualizar puntajes (POST)
curl -X POST $FUNCTION_URL -H "Content-Type: application/json" -d '{"jugador":"ana","puntos":1250}'
# Respuesta: ok (HTTP 201)

curl -X POST $FUNCTION_URL -H "Content-Type: application/json" -d '{"jugador":"carlos","puntos":1800}'
# Respuesta: ok (HTTP 201)

# 2. Consultar Top 10 Global (GET)
curl $FUNCTION_URL
# Respuesta (HTTP 200): [{"jugador": "carlos", "puntos": 1800}, {"jugador": "ana", "puntos": 1250}]
```

---

## 2. Guía para la Captura de Concurrencia y Cold Start en Amazon CloudWatch

1. **Ejecución de la prueba de carga (500 usuarios concurrentes, 80% `GET` / 20% `POST`):**
   - Desde `locust-gen` ejecutando `locust -f locust_leaderboard.py LeaderboardUser --host $FUNCTION_URL -u 500 -r 50 -t 3m --headless --csv leaderboard`.
2. **Dónde tomar la captura en la consola de AWS:**
   - Ir a **AWS Console $\rightarrow$ Lambda $\rightarrow$ Functions $\rightarrow$ `nebula-leaderboard` $\rightarrow$ pestaña Monitor** (o en **CloudWatch $\rightarrow$ Metrics $\rightarrow$ All metrics $\rightarrow$ AWS/Lambda $\rightarrow$ By Function Name $\rightarrow$ `nebula-leaderboard`**).
   - Seleccionar las gráficas:
     - **`ConcurrentExecutions` (Ejecuciones concurrentes):** Muestra el escalado automático de `0` a `~25–60` entornos de ejecución simultáneos durante la ráfaga de 500 usuarios, volviendo a `0` al finalizar la prueba.
     - **`Invocations` y `Duration` (`Minimum`, `Average`, `p99`):** Muestra cómo las ejecuciones tibias (*warm starts*) responden en **`~8–25 ms`**, mientras que el percentil **`p99`** presenta un pico inicial de **`~250–450 ms`** causado por el **arranque en frío (*cold start*)** al inicializar los microVMs Firecracker e importar `boto3` en los primeros segundos de la subida de carga.

---

## 3. Cálculo Comparativo de Costo Mensual: Serverless vs Instancia EC2 Encendida 24/7

### Escenario de Tráfico Mensual de Referencia
- **Peticiones totales al mes:** $5,000,000\text{ peticiones/mes}$ ($4,000,000\text{ lecturas GET}$ + $1,000,000\text{ escrituras POST}$).
- **Duración promedio por invocación Lambda:** $50\text{ ms} = 0.05\text{ s}$.
- **Memoria asignada a la función Lambda:** $256\text{ MB} = 0.25\text{ GB}$.

### A. Costo Mensual con Arquitectura Serverless (AWS Lambda + DynamoDB On-Demand)

1. **AWS Lambda (`us-east-1`, arquitectura x86_64):**
   - **Cómputo total mensual:**
     $$5,000,000\text{ inv} \times 0.05\text{ s} \times 0.25\text{ GB} = \mathbf{62,500\text{ GB-s}}$$
   - **Capa gratuita mensual de AWS Lambda:** Incluye $1,000,000\text{ peticiones}$ y $400,000\text{ GB-s}$ gratis cada mes.
   - **Costo por cómputo (GB-s):** $62,500\text{ GB-s} \le 400,000\text{ GB-s} \implies \mathbf{\$0.00\text{ USD}}$ *(incluso sin capa gratuita: $62,500 \times \$0.0000166667 = \$1.04\text{ USD}$)*.
   - **Costo por peticiones excedentes:**
     $$(5,000,000 - 1,000,000)\text{ peticiones} \times \frac{\$0.20}{1,000,000} = \mathbf{\$0.80\text{ USD / mes}}$$
2. **Amazon DynamoDB (On-Demand / Capa Gratuita de 25 GB y hasta 200M peticiones en Free Tier, o tarifa directa On-Demand):**
   - Escrituras (`1M WRU` a `$0.625 / millón` tras reducción de precios 2024+): **$\$0.63\text{ USD}$**.
   - Lecturas (`4M RRU` eventuales = `2M unidades` a `$0.125 / millón`): **$\$0.25\text{ USD}$**.
   - Almacenamiento (`< 1 GB`): **$\$0.00\text{ USD}$** (cubierto por los 25 GB gratuitos).
- **Total Mensual Serverless (Lambda + DynamoDB):** **$\$0.80\text{ a }\$1.68\text{ USD / mes}$** *(y **$\$0.00\text{ USD}$** cuando no hay jugadores activos)*.

### B. Costo Mensual con Servidor Dedicado 24/7 (EC2 + ALB + Base de Datos)

| Componente Dedicado (24/7, 730 horas/mes) | Tipo / Recurso | Costo Mensual (`us-east-1`) |
| :--- | :--- | :---: |
| **Instancia EC2 pequeña** | `t3.small` (2 vCPU, 2 GiB RAM) @ `$0.0208/h` $\times 730\text{ h}$ | `$15.18 USD` |
| **Volumen EBS del SO y datos** | `20 GB gp3` @ `$0.08/GB-mes` | `$1.60 USD` |
| **Application Load Balancer (opcional para HTTPS/HA)** | ALB base @ `$0.0225/h` $\times 730\text{ h}$ | `$16.43 USD` |
| **Total Mensual VM 24/7 (Solo EC2 + EBS)** | 1 instancia sin alta disponibilidad | **`$16.78 USD / mes`** |
| **Total Mensual VM 24/7 (2x EC2 Multi-AZ + ALB)** | Equivalente en disponibilidad a Lambda | **`$49.99 USD / mes`** |

### Conclusión Técnica
Para la tabla de líderes, login y funciones auxiliares cuyo tráfico ocurre en ráfagas al finalizar cada partida, **AWS Lambda + DynamoDB cuesta entre `10x y 30x menos` (`~$0.80–$1.68/mes` frente a `$16.78–$49.99/mes`)**, ofrece tolerancia a fallos Multi-AZ nativa sin administrar sistemas operativos ni parches, y escala automáticamente de `0` a cientos de ejecuciones concurrentes en segundos.
