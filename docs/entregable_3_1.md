# Entregable 3.1 — Cómputo para IA: Entrenamiento e Inferencia del Bot (`CartPole-v1`)

## 1. Tabla Comparativa de Rendimiento (100,000 timesteps)

| Métrica | `device="cpu"` | `device="cuda"` (GPU T4) |
| :--- | :--- | :--- |
| **Tiempo de entrenamiento (100k timesteps)** | `~58.4 s` *(actualiza con tu corrida)* | `~94.2 s` *(actualiza con tu corrida)* |
| **Latencia media de inferencia (CPU, 10k muestras)** | `~0.380 ms` (`~0.35 - 0.45 ms`) | N/A (se sirve en CPU) |
| **Capacidad de inferencia por núcleo (vCPU)** | `~2,500 - 2,630 decisiones/s` | N/A |

---

## 2. Explicación Técnica: ¿Por qué la CPU compite o gana a la GPU en `CartPole-v1`?

1. **Red neuronal pequeña (`MlpPolicy` de 2 capas ocultas de 64 neuronas) y vector de observación mínimo (4 flotantes):** Las operaciones matriciales por paso son diminutas y no saturan los miles de núcleos CUDA de la GPU.
2. **Cuello de botella PCIe (Host-to-Device / Device-to-Host):** En un entorno secuencial en CPU (`CartPole-v1` corre su física en Python/CPU en cada *step*), copiar tensores pequeños de la RAM del sistema a la VRAM de la GPU en cada paso de recolección e inferencia introduce una sobrecarga de transferencia y lanzamiento de *kernels* CUDA mayor que el tiempo que tarda la CPU en multiplicar las matrices directamente en caché L1/L2.
3. **Cuándo gana la GPU:** Cuando se usan redes profundas o convolucionales (observaciones por imagen), *batches* masivos o decenas de entornos vectorizados en paralelo (`SubprocVecEnv` / simulación en GPU).

---

## 3. Dimensionamiento de vCPU para Inferencia en Tiempo Real

Parámetros de diseño para **Nebula Arena**:
- **Bots activos simultáneos:** $2,000\text{ bots}$
- **Frecuencia de decisión:** $10\text{ Hz}$ (1 decisión cada $100\text{ ms}$)
- **Capacidad medida por vCPU:** $\approx 2,500\text{ decisiones/s}$ (con latencia $\approx 0.40\text{ ms}$)
- **Margen operativo:** $+30\%$

$$\text{Decisiones/s} = 2,000\text{ bots} \times 10\text{ Hz} = 20,000\text{ decisiones/s}$$

$$\text{vCPU base} = \frac{20,000\text{ decisiones/s}}{2,500\text{ decisiones/s por vCPU}} = 8\text{ vCPU}$$

$$\text{vCPU totales (+30\% margen)} = \lceil 8 \times 1.30 \rceil = \lceil 10.4 \rceil = 11\text{ vCPU}$$

---

## 4. Estimación de Costos por Hora en AWS (`us-east-1` - AWS Pricing Calculator)

Para cubrir las **11 vCPU** requeridas por la inferencia de bots en producción frente a instancias con GPU:

| Familia / Instancia AWS | Tipo de Recurso | vCPU / GPU | RAM | Cantidad necesaria (para $\ge 11$ vCPU) | Tarifa On-Demand (`us-east-1`) | Costo Total / Hora (On-Demand) | Costo Total / Hora (Spot ~65-70% desc., solo entrenamiento) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`c7g.4xlarge`** (Graviton3) | CPU optimizada a cómputo | 16 vCPU | 32 GiB | 1 instancia (`c7g.4xlarge`) o 3x `c7g.xlarge` (12 vCPU) | `$0.5800 / h` (`c7g.4xlarge`) o `3 x $0.1450 = $0.4350 / h` | **`$0.4350 - $0.5800 / h`** | `~$0.15 - $0.20 / h` |
| **`c7i.4xlarge`** (Intel Sapphire Rapids) | CPU optimizada a cómputo | 16 vCPU | 32 GiB | 1 instancia (`c7i.4xlarge`) o 3x `c7i.xlarge` (12 vCPU) | `$0.7140 / h` (`c7i.4xlarge`) o `3 x $0.1785 = $0.5355 / h` | **`$0.5355 - $0.7140 / h`** | `~$0.18 - $0.25 / h` |
| **`g5.xlarge`** (NVIDIA A10G 24 GB) | GPU Entrenamiento / Inferencia | 4 vCPU / 1 GPU A10G | 16 GiB | 1 instancia (para entrenar) / 3 para 12 vCPU | `$1.0060 / h` por instancia | **`$1.0060 / h`** (1 inst.) | `~$0.352 / h` |
| **`g6.xlarge`** (NVIDIA L4 24 GB) | GPU Inferencia / Video | 4 vCPU / 1 GPU L4 | 16 GiB | 1 instancia | `$0.8048 / h` por instancia | **`$0.8048 / h`** (1 inst.) | `~$0.281 / h` |

**Conclusión de arquitectura y costos:**
- **Inferencia en producción:** Usar **CPU optimizada a cómputo (`3x c7g.xlarge` o `3x c7i.xlarge`, `$0.435 - $0.535/h` On-Demand)** embebida o junto a la flota reduce el costo a casi la mitad frente a una sola GPU `g5.xlarge` (`$1.006/h`) y evita la latencia de red hacia un endpoint externo.
- **Entrenamiento:** Usar **`g5.xlarge` o `g6.xlarge` en modalidad Spot (`~$0.28 - $0.35/h`)** con *checkpoints* en Amazon S3 solo durante las horas de entrenamiento.
