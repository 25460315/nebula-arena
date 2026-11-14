#!/usr/bin/env bash
# Práctica 3.4 (Variante AWS) — Generar stream HLS 360p y publicarlo en S3 + CloudFront
set -euo pipefail

BUCKET_NAME="nebula-stream-${1:-tu-id-unico}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "1. Generando video HLS de prueba (5 min a 360p, segmentos de 2 s)..."
ffmpeg -f lavfi -i testsrc2=size=640x360:rate=30 -t 300 \
  -c:v libx264 -preset veryfast -b:v 800k -maxrate 800k -bufsize 1600k -g 60 \
  -hls_time 2 -hls_playlist_type vod -hls_segment_filename "360p_%03d.ts" \
  360p.m3u8

echo "2. Creando bucket S3 y subiendo segmentos..."
aws s3 mb "s3://${BUCKET_NAME}" --region "${AWS_REGION}"
aws s3 cp . "s3://${BUCKET_NAME}/live/nebula/" --recursive --exclude "*" --include "360p*"

echo "3. Creando distribución de Amazon CloudFront delante del bucket S3..."
aws cloudfront create-distribution \
  --origin-domain-name "${BUCKET_NAME}.s3.${AWS_REGION}.amazonaws.com" \
  --default-root-object "live/nebula/360p.m3u8" \
  --query "Distribution.DomainName" --output text
