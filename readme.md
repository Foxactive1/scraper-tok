# 🚀 TikTok Scraper Pro

> Ferramenta web para extração de dados e download de vídeos do TikTok.  
> Desenvolvida por **[InNovaIdeia](mailto:innovaideia2023@gmail.com)** · Franca, SP · Brasil

---

## 📋 Visão Geral

TikTok Scraper Pro é uma aplicação Flask que permite extrair metadados de vídeos do TikTok (autor, descrição, views, likes) e obter links de download sem marca d'água, via interface web responsiva.

**Stack:** Python · Flask · Celery · Redis · Bootstrap 5 · Docker · Railway

---

## ✨ Funcionalidades

- 🔍 Extração de metadados: autor, descrição, views e likes
- ⬇️ Download sem marca d'água (SD e HD) via tikwm.com API
- ⚡ Suporte a links curtos (`vt.tiktok.com`, `vm.tiktok.com`)
- 🔄 Polling assíncrono com feedback de progresso em tempo real
- 📱 Interface responsiva (Bootstrap 5 dark theme)
- 🤖 Rotação de User-Agent para reduzir detecção bot
- 🐳 Deploy via Docker ou Railway

---

## 🗂️ Estrutura do Projeto

```
tiktok-scraper-pro/
├── run.py                  # Entrypoint Flask
├── config.py               # Configurações via variáveis de ambiente
├── requirements.txt        # Dependências Python
├── Dockerfile              # Imagem Docker (python:3.11-slim)
├── docker-compose.yml      # Orquestração: web + worker + redis
├── railway.json            # Config Railway — serviço web
├── railway.worker.json     # Config Railway — serviço Celery worker
├── app/
│   ├── __init__.py         # App Factory (create_app)
│   ├── routes.py           # Blueprint: /scrape, /status, /download, /
│   ├── tasks.py            # Celery task: scrape_task
│   └── scraper.py          # Lógica: resolve_url, fetch_html, parse_video, get_download_url
└── templates/
│   └── index.html          # Frontend Bootstrap
└── static/
    └── js/
        └── app.js          # Polling, renderização, download
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | URL do broker/backend Redis |
| `CELERY_TASK_ALWAYS_EAGER` | `true` | `true` = modo síncrono (sem Redis) |
| `REQUEST_TIMEOUT` | `15` | Timeout HTTP em segundos |

> **Android / Pydroid 3:** mantenha `CELERY_TASK_ALWAYS_EAGER=true` — Redis não roda nativamente no Android.

---

## 🚀 Como Executar

### Desenvolvimento local (sem Redis)

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
python run.py
```

Acesse: [http://localhost:5000](http://localhost:5000)

---

### Docker Compose (com Redis + Worker)

```bash
# Build e start de todos os serviços
docker-compose up --build

# Apenas em background
docker-compose up -d --build

# Parar
docker-compose down
```

Serviços iniciados:
- `web` → Flask em `http://localhost:5000`
- `worker` → Celery worker
- `redis` → Redis 7 Alpine

---

### Pydroid 3 / Termux (Android)

```bash
pip install flask celery requests
python run.py
```

Acesse pelo IP local do dispositivo: `http://192.168.x.x:5000`

---

## ☁️ Deploy Railway

### Serviço Web

1. Conecte o repositório no [Railway](https://railway.com)
2. Railway detecta o `railway.json` automaticamente
3. Adicione o plugin **Redis** ao projeto

### Serviço Worker (Celery)

1. New Service → Same Repo
2. Settings → **Config File Path** → `railway.worker.json`

### Variáveis de Ambiente (ambos os serviços)

```
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_TASK_ALWAYS_EAGER=false
REQUEST_TIMEOUT=15
PORT=5000
```

---

## 🔌 API Endpoints

### `POST /scrape`
Inicia a extração de dados de um vídeo.

**Request:**
```json
{ "url": "https://vt.tiktok.com/ZSH9dAps1/" }
```

**Response `202`:**
```json
{ "task_id": "uuid", "status": "processing" }
```

---

### `GET /status/<task_id>`
Consulta o resultado da task.

**Response `200`:**
```json
{
  "status": "SUCCESS",
  "result": {
    "id": "7614213859422899473",
    "desc": "Descrição do vídeo...",
    "author": "usuario",
    "likes": 30900,
    "views": 549800,
    "video_url": "https://www.tiktok.com/@usuario/video/..."
  },
  "error": null
}
```

---

### `POST /download`
Obtém links diretos de download via tikwm.com.

**Request:**
```json
{ "url": "https://www.tiktok.com/@usuario/video/7614213859422899473" }
```

**Response `200`:**
```json
{
  "url_sd": "https://www.tikwm.com/video/media/play/...",
  "url_hd": "https://www.tikwm.com/video/media/hdplay/...",
  "url_wm": "https://www.tikwm.com/video/media/wmplay/..."
}
```

> ⚠️ Links do tikwm.com expiram em alguns minutos. Faça o download logo após obtê-los.

---

## 📦 Dependências

```
flask
celery
redis
requests
```

Instalar:
```bash
pip install flask celery redis requests
```

---

## 🔒 Limitações

- O TikTok pode bloquear requisições em casos de uso intenso (rate limiting / Cloudflare)
- Links de download gerados pela tikwm.com API são de terceiros e podem expirar
- `playAddr` / `downloadAddr` diretos do CDN Akamai exigem cookies de sessão (não utilizados)

---

## 👨‍💻 Autor

**Dione Castro Alves**  
Fundador · [InNovaIdeia](mailto:innovaideia2023@gmail.com)  
Consultoria · Desenvolvimento de Software · Treinamentos

[![GitHub](https://img.shields.io/badge/GitHub-Foxactive1-181717?logo=github)](https://github.com/Foxactive1)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Dione%20Castro%20Alves-0A66C2?logo=linkedin)](https://www.linkedin.com/in/dione-castro-alves)
[![Email](https://img.shields.io/badge/Email-innovaideia2023%40gmail.com-EA4335?logo=gmail)](mailto:innovaideia2023@gmail.com)

---

© 2025 InNovaIdeia · Franca, SP · Brasil
