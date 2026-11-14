import time
import gymnasium as gym
import numpy as np
import torch
from stable_baselines3 import PPO


def entrenar(device: str, timesteps: int = 100_000) -> tuple[PPO, float]:
    env = gym.make("CartPole-v1")
    modelo = PPO("MlpPolicy", env, verbose=0, device=device)
    inicio = time.time()
    modelo.learn(total_timesteps=timesteps)
    duracion = time.time() - inicio
    print(f"Entrenamiento ({device}): {duracion:.1f} s")
    return modelo, duracion


def medir_inferencia(modelo: PPO, n_predicciones: int = 10_000) -> tuple[float, float]:
    env = gym.make("CartPole-v1")
    obs, _ = env.reset()
    t = time.perf_counter()
    for _ in range(n_predicciones):
        accion, _ = modelo.predict(obs, deterministic=True)
    lat_ms = (time.perf_counter() - t) / n_predicciones * 1000
    decisiones_s = 1000.0 / lat_ms
    print(f"Latencia media (CPU): {lat_ms:.3f} ms -> {decisiones_s:,.0f} decisiones/s por núcleo")
    return lat_ms, decisiones_s


if __name__ == "__main__":
    modelo_cpu, t_cpu = entrenar(device="cpu", timesteps=100_000)
    modelo_cpu.save("bot_nebula")

    if torch.cuda.is_available():
        _, t_gpu = entrenar(device="cuda", timesteps=100_000)
    else:
        print("CUDA no disponible localmente; ejecuta en SageMaker Studio Lab / Colab con GPU T4 para medir device='cuda'.")
        t_gpu = None

    lat_ms, dec_s = medir_inferencia(modelo_cpu, n_predicciones=10_000)

    demanda_total = 2000 * 10  # 2,000 bots a 10 Hz = 20,000 decisiones/s
    vcpu_base = demanda_total / dec_s
    vcpu_con_margen = np.ceil(vcpu_base * 1.30)
    print(f"Demanda: {demanda_total:,} decisiones/s | vCPU base: {vcpu_base:.2f} | vCPU (+30% margen): {int(vcpu_con_margen)}")
