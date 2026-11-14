# Entregable 3.3 — Contenedores y Orquestación con EKS y Agones

## 1. Guía de Capturas de Evidencia

1. **Captura 1 — Contenedor corriendo localmente (`docker run`) y métricas (`/metrics`):**
   - Terminal 1 ejecutando `docker run -p 7654:7654 -p 9100:9100 nebula-server:1.0`.
   - Terminal 2 ejecutando `curl -s http://localhost:9100/metrics | grep nebula` mostrando `nebula_players_connected 0.0` y los buckets de `nebula_tick_seconds_bucket`.
2. **Captura 2 — Flota de Agones antes de la asignación (`Ready`):**
   - Salida de `kubectl get gameservers` mostrando los 3 pods `nebula-fleet-xxxxx` en `STATE: Ready`, con IP de nodo y puerto dinámico asignado en el rango `7000-8000`.
3. **Captura 3 — Flota de Agones después de la asignación (`Allocated`):**
   - Salida de `kubectl create -f k8s/allocation.yaml` (devolviendo `status.state: Allocated`, `address` y `ports`) seguida de `kubectl get gameservers` mostrando **1 servidor en `Allocated`** y **2 servidores en `Ready`**.

---

## 2. Explicación Técnica: ¿Qué pasaría si borras un pod en estado `Allocated`?

1. **Pérdida inmediata del estado de la partida en memoria:** A diferencia de una API web sin estado (*stateless*), toda la simulación física, posiciones (`estado`) y conexiones WebSocket activas de los 10 jugadores viven exclusivamente en la memoria RAM de ese proceso. Al eliminar el pod, las conexiones TCP/WebSocket se cierran abruptamente y los 10 jugadores son desconectados de la partida sin posibilidad de recuperarla en otro contenedor.
2. **Reconciliación de la `Fleet` por Agones:** El controlador de Agones detecta la desaparición del `GameServer` que estaba en `Allocated`. Para mantener el número deseado de réplicas de la flota (`replicas: 3`), el `GameServerSet` crea un **nuevo pod en estado `Ready`**, pero este arranca limpio (`estado = {}`, `partida["iniciada"] = False`), esperando una nueva asignación del *matchmaker*.
3. **Por qué Agones protege los pods `Allocated`:** Precisamente para evitar este corte de partidas, Agones anota los pods `Allocated` con `cluster-autoscaler.kubernetes.io/safe-to-evict: "false"` y les aplica prioridad frente a reducciones de escala (*scale-down*) o actualizaciones de flota (*rolling updates*), drenando solo los servidores en `Ready` y esperando a que los `Allocated` invoquen `/shutdown` por sí mismos cuando los jugadores terminen la partida.
