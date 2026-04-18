#!/usr/bin/env bash
set -euo pipefail
cp -n .env.example .env || true
cp -n backend/.env.example backend/.env || true
cp -n frontend/.env.example frontend/.env || true
echo "Ambiente base pronto. Ajuste domínios no Caddyfile e .envs."
echo "Para subir: cd docker && docker compose build && docker compose up -d"
