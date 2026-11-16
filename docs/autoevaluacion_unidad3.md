# Autoevaluación Unidad 3 — Respuestas Técnicas Completas

1. **¿Por qué no conviene ejecutar un servidor de partida en instancias Spot, pero sí el entrenamiento de un bot?**
   - **Respuesta:** Las instancias Spot pueden ser reclamadas por AWS con solo 2 minutos de preaviso cuando sube la demanda. Como un servidor de partida (`Allocated`) mantiene el estado físico y las conexiones WebSocket/UDP de los 10 jugadores en memoria RAM, su interrupción cortaría la partida en curso sin posibilidad de migrarla. En cambio, el entrenamiento de un bot de aprendizaje por refuerzo guarda *checkpoints* periódicos en Amazon S3 y puede reanudarse automáticamente desde el último *checkpoint* sin afectar a ningún jugador, aprovechando descuentos del 60% al 90%.

2. **Si cada partida tiene 10 jugadores, hay 4,300 jugadores conectados y quieres un buffer de 20% sobre los servidores en uso, ¿cuántos GameServers deben existir?**
   - **Respuesta:**
     $$\text{Servidores en uso (Allocated)} = \left\lceil \frac{4,300}{10} \right\rceil = 430\text{ servidores}$$
     $$\text{Buffer (20\% sobre servidores en uso)} = 430 \times 0.20 = 86\text{ servidores Ready}$$
     $$\text{Total de GameServers} = 430 + 86 = \mathbf{516\text{ GameServers}}$$
     *(Nota: Si se evalúa con la política `bufferSize: 20%` nativa de Agones, que calcula el 20% sobre el total de la flota: $\lceil 430 \div 0.80 \rceil = \mathbf{538\text{ GameServers}}$, con 108 en `Ready`).*

3. **¿Qué diferencia hay entre el HPA, el FleetAutoscaler de Agones y el Cluster Autoscaler?**
   - **Respuesta:**
     - **HPA (`HorizontalPodAutoscaler`):** Escala réplicas de pods **sin estado** (matchmaking, APIs, inferencia) basándose en métricas como CPU o peticiones por segundo; al escalar hacia abajo puede eliminar cualquier réplica.
     - **FleetAutoscaler (Agones):** Escala servidores de partida **con estado** (`GameServers`) manteniendo un *buffer* de servidores vacíos en estado `Ready`, y al reducir la flota solo elimina servidores `Ready`, respetando siempre los que están en `Allocated`.
     - **Cluster Autoscaler:** Escala la capa de **infraestructura (nodos EC2 del clúster)**: agrega máquinas virtuales cuando hay pods en estado `Pending` por falta de CPU/RAM y retira nodos subutilizados que no tengan partidas `Allocated`.

4. **¿Qué métrica de streaming eleva más el costo y cómo se reduce?**
   - **Respuesta:** El **egress (transferencia de salida de datos hacia internet en GB)**, determinado por el número de espectadores concurrentes (CCV) multiplicado por el bitrate del video. Se reduce distribuyendo el video mediante un **CDN (Amazon CloudFront)**, aplicando **ABR (Adaptive Bitrate)** para ajustar la calidad al dispositivo/red de cada espectador, y utilizando codificación de video más eficiente.

5. **15,000 espectadores a 4,500 kbps durante 2 horas, ¿cuántos TB de egress generan?**
   - **Respuesta:**
     $$\text{GB totales} = \frac{15,000 \times 4,500\text{ kbps} \times (2 \times 3,600\text{ s})}{8 \times 10^6} = \frac{486,000,000,000}{8,000,000} = 60,750\text{ GB} \approx \mathbf{60.75\text{ TB}}$$

6. **Menciona tres funciones de Nebula Arena adecuadas para serverless y una que no lo es, con su razón.**
   - **Respuesta:**
     - **Tres adecuadas para serverless:** (1) Tabla de líderes (`nebula-leaderboard`), (2) Login y perfil del jugador, (3) Procesamiento asíncrono de resultados de partida o tienda y recompensas diarias. *Razón:* Son operaciones cortas, sin estado persistente en memoria y con tráfico en ráfagas (si nadie juega, el costo cae a casi cero).
     - **Una NO adecuada para serverless:** El **servidor de partida en tiempo real**. *Razón:* Mantiene el estado de la simulación a 20 Hz en memoria RAM, requiere conexiones persistentes de baja latencia (WebSocket/UDP) con un puerto dedicado por partida y sesiones largas que chocan con el modelo efímero por petición de FaaS.

7. **¿Qué es el *drift* en Terraform y con qué comando se detecta?**
   - **Respuesta:** El *drift* es la diferencia o divergencia entre el estado deseado definido en los archivos de código de Terraform (`.tf`) y la infraestructura real existente en la nube (provocada cuando alguien modifica recursos manualmente desde la consola web o AWS CLI). Se detecta con el comando **`terraform plan`** (o `terraform plan -refresh-only`).

8. **En la curva CCU vs latencia p95, ¿cómo identificas la capacidad máxima de un nodo?**
   - **Respuesta:** Se identifica el punto de jugadores simultáneos (CCU) donde la curva de latencia `p95` cruza la meta de servicio (`80 ms`) o cambia bruscamente de pendiente disparándose hacia arriba, y se divide ese número de jugadores entre la cantidad de nodos activos en el clúster en ese momento.
