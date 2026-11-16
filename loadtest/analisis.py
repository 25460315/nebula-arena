import os
import pandas as pd
import matplotlib.pyplot as plt


def graficar_curva(csv_path: str = "rampa_stats_history.csv", out_png: str = "ccu_vs_p95.png"):
    if not os.path.exists(csv_path):
        print(f"Archivo {csv_path} no encontrado. Ejecuta primero el escenario rampa en Locust.")
        return
    h = pd.read_csv(csv_path)
    h = h[h["Name"] == "Aggregated"]
    h["p95"] = pd.to_numeric(h["95%"], errors="coerce")
    plt.figure(figsize=(8, 4.5))
    plt.plot(h["User Count"], h["p95"], label="Latencia RTT p95")
    plt.axhline(80, color="red", linestyle="--", label="meta p95 = 80 ms")
    plt.xlabel("Jugadores simulados (CCU)")
    plt.ylabel("Latencia p95 (ms)")
    plt.title("Nebula Arena — Curva CCU vs Latencia p95")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"Gráfica guardada en {out_png}")


def calcular_egress(ccv: int = 20_000, bitrate_kbps: int = 6_000, horas: float = 1.0, tarifa_usd_gb: float = 0.085):
    gb_hora = (ccv * bitrate_kbps * 3600) / (8 * 10**6)
    gb_totales = gb_hora * horas
    tb_totales = gb_totales / 1000.0
    costo_usd = gb_totales * tarifa_usd_gb
    print(f"--- Extrapolación de Egress ({ccv:,} espectadores @ {bitrate_kbps:,} kbps por {horas} h) ---")
    print(f"Tráfico generado: {gb_totales:,.0f} GB ({tb_totales:.2f} TB)")
    print(f"Costo estimado Amazon CloudFront ($0.085/GB): ${costo_usd:,.2f} USD / hora")
    return tb_totales, costo_usd


if __name__ == "__main__":
    graficar_curva()
    calcular_egress()
