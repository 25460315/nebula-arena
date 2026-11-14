#!/usr/bin/env bash
# Práctica 3.4 — Extraer certificados de Agones Allocator y ejecutar los 3 escenarios de Locust
set -euo pipefail

echo "Extrayendo certificados TLS del servicio agones-allocator..."
kubectl get secret allocator-client.default -n default -o jsonpath="{.data.tls\.crt}" | base64 -d > client.crt
kubectl get secret allocator-client.default -n default -o jsonpath="{.data.tls\.key}" | base64 -d > client.key
kubectl get secret allocator-tls-ca -n agones-system -o jsonpath="{.data.tls-ca\.crt}" | base64 -d > ca.crt

export ALLOCATOR_IP=$(kubectl get svc agones-allocator -n agones-system -o jsonpath="{.status.loadBalancer.ingress[0].hostname}")
if [ -z "$ALLOCATOR_IP" ]; then
  export ALLOCATOR_IP=$(kubectl get svc agones-allocator -n agones-system -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
fi
echo "Allocator detectado en: $ALLOCATOR_IP"

# 1. Rampa: 1,000 jugadores, 2 nuevos por segundo (~8 min de subida), 20 min en total
locust -f locustfile.py Jugador -u 1000 -r 2 -t 20m --headless --processes -1 --csv rampa

# 2. Pico: 1,000 jugadores entrando en 20 s (50 jugadores/s) durante 10 min
locust -f locustfile.py Jugador -u 1000 -r 50 -t 10m --headless --processes -1 --csv pico

# 3. Espectadores: 500 espectadores a 360p durante 5 min contra CloudFront CDN
CDN_HOST="${CDN_HOST:-https://d111111abcdef8.cloudfront.net}"
locust -f locustfile.py Espectador --host "$CDN_HOST" -u 500 -r 50 -t 5m --headless --processes -1 --csv stream
