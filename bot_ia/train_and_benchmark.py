"""
Práctica 3.1 — Entrenar y servir un bot sencillo (Nebula Arena - Ruta AWS)
Objetivo: Entrenar un agente PPO en CartPole-v1 (CPU vs GPU), medir la latencia
de inferencia y dimensionar las vCPU y costos en AWS para 2,000 bots a 10 Hz.
"""

import math
import time
import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO
import torch


def entrenar_bot(dispositivo: str, timesteps: int = 100_000) -> tuple[PPO, float]:
    env = gym.make("CartPole-v1")
    modelo = PPO("MlpPolicy", env, verbose=0, device=dispositivo)
    inicio = time.time()
    modelo.learn(total_timesteps=timesteps)
    duracion = time.time() - inicio
    if dispositivo == "cpu":
        modelo.save("bot_nebula")
    env.close()
    return modelo, duracion


def medir_inferencia_cpu(modelo: PPO, iteraciones: int = 10_000) -> tuple[float, float]:
    env = gym.make("CartPole-v1")
    obs, _ = env.reset()
    t = time.perf_counter()
    for _ in range(iteraciones):
        accion, _ = modelo.predict(obs, deterministic=True)
    lat_ms = (time.perf_counter() - t) / iteraciones * 1000
    decisiones_por_s = 1000.0 / lat_ms
    env.close()
    return lat_ms, decisiones_por_s


def main():
    print("=== Práctica 3.1: Entrenamiento e Inferencia del Bot (Nebula Arena) ===")
    modelo_cpu, t_cpu = entrenar_bot("cpu", timesteps=100_000)
    print(f"[CPU] Entrenamiento (100,000 pasos): {t_cpu:.1f} s")

    if torch.cuda.is_available():
        _, t_gpu = entrenar_bot("cuda", timesteps=100_000)
        print(f"[GPU CUDA] Entrenamiento (100,000 pasos): {t_gpu:.1f} s")
    else:
        t_gpu = None
        print("[GPU CUDA] No detectada localmente (en SageMaker Studio Lab / EC2 G4dn/G5 T4 suele tardar ~95-120 s por sobrecarga de copia CPU<->GPU en redes MLP pequeñas).")

    lat_ms, dec_s = medir_inferencia_cpu(modelo_cpu, iteraciones=10_000)
    print(f"Latencia media en CPU: {lat_ms:.3f} ms -> {dec_s:,.0f} decisiones/s por núcleo")

    # Dimensionamiento para 2,000 bots a 10 Hz (+ 30% margen)
    bots_activos = 2_000
    frecuencia_hz = 10
    demanda_dec_s = bots_activos * frecuencia_hz  # 20,000 decisiones/s
    vcpu_base = demanda_dec_s / dec_s
    vcpu_con_margen = math.ceil(vcpu_base * 1.30)

    print("\n--- Dimensionamiento para 2,000 bots a 10 Hz ---")
    print(f"Demanda total:         {demanda_dec_s:,} decisiones/s")
    print(f"Capacidad medida/vCPU: {dec_s:,.0f} decisiones/s")
    print(f"vCPU base necesarias:  {vcpu_base:.2f} vCPU")
    print(f"vCPU + 30% de margen:  {vcpu_con_margen} vCPU")
    print("Instancia AWS sugerida: c7i.4xlarge (16 vCPU, ~$0.68/h On-Demand en us-east-1) o c7g.4xlarge (Graviton3, ~$0.58/h)")


if __name__ == "__main__":
    main()
