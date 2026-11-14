"""
Práctica 3.5 — Prueba de carga a la tabla de líderes Serverless (AWS Lambda + DynamoDB)
Ejecuta 80% lecturas (GET) y 20% escrituras (POST) con 500 usuarios concurrentes:
  locust -f locust_leaderboard.py --host <LAMBDA_FUNCTION_URL> -u 500 -r 50 -t 3m --headless --csv leaderboard
"""

import random
from locust import HttpUser, task, between


class JugadorLeaderboard(HttpUser):
    wait_time = between(0.2, 0.8)

    @task(4)  # 80% lecturas del top 10
    def consultar_top(self):
        self.client.get("/", name="GET /top10")

    @task(1)  # 20% escrituras de puntajes al terminar partida
    def registrar_puntaje(self):
        jugador = f"player_{random.randint(1, 5000)}"
        puntos = random.randint(100, 2500)
        self.client.post(
            "/",
            json={"jugador": jugador, "puntos": puntos},
            name="POST /score",
        )
