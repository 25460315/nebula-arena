import random
from locust import HttpUser, task, between


class LeaderboardUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(4)  # 80% lecturas (GET top 10)
    def consultar_top(self):
        self.client.get("/", name="GET /top")

    @task(1)  # 20% escrituras (POST score)
    def registrar_puntaje(self):
        jugador = f"jugador_{random.randint(1, 500)}"
        puntos = random.randint(50, 1500)
        self.client.post(
            "/",
            json={"jugador": jugador, "puntos": puntos},
            name="POST /score",
        )
