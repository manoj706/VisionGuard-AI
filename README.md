<div align="center">

#  VisionGuardAI

### AI-Powered Multi-Camera Scene Intelligence

**Watches every camera. Describes every person. Alerts before it's too late.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)


</div>

---

## What is VisionGuardAI?

A shopping mall has 200 cameras. One security guard cannot watch 200 screens.

**VisionGuardAI watches all of them simultaneously** — and tells the operator exactly what is happening, in plain English, in real time.

For every person in every camera, the system knows:
- 👕 What they are **wearing** (colour, clothing type)
- 🎒 What they are **carrying** (bags, abandoned objects)
- 🏃 What they are **doing** (walking, running, loitering, fighting)
- 📍 Where they **have been** (cross-camera journey timeline)
- ⚠️ Whether anything is **suspicious** (aggressive posture, crowd surges, unusual behaviour)

Operators search footage in plain English:
```
"Show me everyone in a red jacket near the east exit in the last hour"
"Find the person carrying a large black bag at gate 3"
"Show all incidents where someone was running"
```

---

##  Key Features

| Feature | Description |
|---|---|
| 🎯 **Real-time person tracking** | Stable track IDs across frames using ByteTrack |
| 👗 **Clothing description** | Colour + type for upper/lower body, bags, hats |
| 🔍 **Natural language search** | CLIP-powered semantic search over all footage |
| 📷 **Cross-camera re-ID** | Follow the same person across different cameras |
| 🧠 **Behaviour analysis** | Loitering, running, fighting, falling, crowd surges |
| 🚨 **Instant alerts** | Real-time WebSocket alerts with thumbnail + clip |
| 🔒 **Privacy-first** | Face blurring, strict privacy mode, GDPR-compliant retention |
| 🖥️ **Self-hosted** | Runs entirely on your hardware — no cloud, no per-camera fees |
| 🐳 **One-command deploy** | `docker-compose up` and it's running |
| 📊 **CSV export** | Download search results for incident reports |

---

## 🖥️ Dashboard Preview

```
┌───────────────────────────────────────────────────────────────────┐
│  VisionGuardAI          4 cameras online • 12 tracked • 2 alerts  │
├────────────┬─────────────────────────────────┬────────────────────┤
│ CAMERAS    │  [ Live Grid ] [ Search ] [ Heatmap ]                │
│            │                                 │  LIVE ALERTS       │
│ Main Ent 4 │  ┌──────────┐  ┌──────────┐     │  ⚠ HIGH — Cam 1    │
│ Food Crt 3 │  │ [cam 1]  │  │ [cam 2]  │     │  Person running    │
│ Gate 3   2 │  │ 🟡🔴👤  │  │ 🟢👤👤  │    │  near exit         │
│ Exit Cor 3 │  └──────────┘  └──────────┘     │                    │
│            │  ┌──────────┐  ┌──────────┐     │  PERSON INTEL      │
│ SYSTEM     │  │ [cam 3]  │  │ [cam 4]  │     │  Red jacket · male │
│ CPU   42%  │  │ 🟢👤    │  │ 🟡👤👤  │    | Loitering 8min      │
│ RAM   55%  │  └──────────┘  └──────────┘     │  Zone B → Cam 1    │
└────────────┴─────────────────────────────────┴────────────────────┘
```

---

##  AI Pipeline

```
Camera Feed (RTSP / USB / HLS / Mock)
         │
         ▼
   YOLOv8 Detector ──── Person crops + Object detections
         │
         ▼
   ByteTrack Tracker ── Stable track IDs across frames
         │
    ┌────┴─────────────────────────┐
    ▼                              ▼
EfficientNet                  MediaPipe
Appearance                    Pose Estimation
(clothing colour,             (running, fighting,
 type, bags, hats)             aggressive posture)
    │                              │
    └────────────┬─────────────────┘
                 ▼
           CLIP Engine
      (threat score + semantic
       search embeddings)
                 │
                 ▼
         Behaviour Engine
    (loitering, abandoned bags,
     crowd surges, fall detection)
                 │
                 ▼
           ReID Engine
    (cross-camera person matching)
                 │
                 ▼
      Scene Fusion + Threat Score
    (description, alert, WebSocket)
                 │
         ┌───────┴────────┐
         ▼                ▼
    PostgreSQL         React Dashboard
    (events,           (live grid, alerts,
     embeddings,        search, heatmap,
     incidents)         person timeline)
```

---

## 🛠️ Tech Stack

**Backend**
- Python 3.11, FastAPI, asyncio
- YOLOv8 (Ultralytics) — person + object detection
- ByteTrack — multi-object tracking
- OpenAI CLIP — semantic search + threat scoring
- MediaPipe — pose estimation
- EfficientNet — clothing attribute classification
- PostgreSQL + SQLAlchemy async

**Frontend**
- React 18, TypeScript, Vite
- Zustand — state management
- TailwindCSS — styling
- Native WebSocket — real-time updates

**Infrastructure**
- Docker + docker-compose
- Caddy — automatic HTTPS (Let's Encrypt)
- APScheduler — data retention cleanup
- JWT — authentication

---

##  Quick Start

### Prerequisites
- Docker + Docker Compose
- NVIDIA GPU (recommended) or CPU (mock mode works fine)
- 8GB RAM minimum

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/visionguardai.git
cd visionguardai
```

### 2. Create your `.env` file
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
OPERATOR_USERNAME=admin
OPERATOR_PASSWORD=your-strong-password
JWT_SECRET=your-random-secret-key
DB_PASSWORD=your-db-password
DOMAIN=localhost
RETENTION_DAYS=30
PRIVACY_MODE=standard
MOCK_MODE=true
ENABLE_REAL_MODELS=false
```

### 3. Start everything
```bash
docker-compose up --build
```

First run takes 10–20 minutes (downloads PyTorch, CLIP, Node modules).

### 4. Open the dashboard
```
http://localhost
```

Login with your credentials from `.env`. You'll see 4 mock cameras running immediately.

---

## 📷 Connecting Real Cameras

Once you've tested with mock mode, switch to real cameras:

**1. Set in `.env`:**
```env
MOCK_MODE=false
ENABLE_REAL_MODELS=true
```

**2. Add cameras via the API:**
```bash
curl -X POST http://localhost/api/cameras \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "cam_01",
    "name": "Main Entrance",
    "location": "Ground Floor",
    "source_url": "rtsp://192.168.1.100:554/stream",
    "source_type": "rtsp"
  }'
```

Supported sources: `rtsp` (IP cameras), `usb` (webcams), `hls` (cloud cameras), `file` (video files)

**3. Restart:**
```bash
docker-compose restart backend
```

---

##  Hardware Profiles

VisionGuardAI automatically detects your hardware and selects the right profile:

| Profile | Hardware | Models | FPS |
|---|---|---|---|
| `gpu_server` | NVIDIA GPU | YOLOv8m + ViT-L/14 | 25 fps |
| `mid_range` | 8+ core CPU, 16GB RAM | YOLOv8s + ViT-B/32 | 15 fps |
| `embedded` | Low-end CPU / edge device | YOLOv8n + ViT-B/32 | 8 fps |

Force a profile:
```env
FORCE_HARDWARE_PROFILE=mid_range
```

---

##  Privacy & Compliance

VisionGuardAI is built privacy-first:

- **Face blurring** — all stored thumbnails and clips have faces automatically blurred
- **Strict privacy mode** — set `PRIVACY_MODE=strict` to blur all crops before storage and suppress biometric attributes. An amber banner appears in the dashboard when active.
- **Data retention** — events, thumbnails, and clips older than `RETENTION_DAYS` are automatically purged every night at 03:00
- **Self-hosted** — all data stays on your hardware. Nothing goes to the cloud.
- **GDPR / DPDP ready** — retention policy + data minimisation built in from day one

---

##  API Reference

All endpoints require `Authorization: Bearer <token>` except login.

```
POST   /api/auth/login              Login → get JWT token
GET    /api/cameras                 List all cameras + status
POST   /api/cameras                 Register a new camera
GET    /api/cameras/{id}/persons    Live persons in this camera
GET    /api/persons                 All tracked persons (all cameras)
GET    /api/persons/{id}            Single person profile + journey
GET    /api/incidents               Paginated incident log
PATCH  /api/incidents/{id}/acknowledge  Mark incident reviewed
POST   /api/search                  CLIP semantic search
GET    /api/search/export           Download search results as CSV
GET    /api/crowd/heatmap           Live crowd density grid
GET    /api/stats                   Dashboard summary stats
GET    /api/health                  System health + model status
WS     /ws/scene?token=<jwt>        Real-time scene updates
```

---

##  Project Structure

```
visionguardai/
├── backend/
│   ├── main.py                 # FastAPI app + pipeline loop
│   ├── config.py               # Hardware detection + settings
│   ├── auth.py                 # JWT authentication
│   ├── pipeline/
│   │   ├── ingestor.py         # Multi-source video capture
│   │   ├── detector.py         # YOLOv8 person + object detection
│   │   ├── tracker.py          # ByteTrack multi-object tracking
│   │   ├── appearance.py       # Clothing + attribute analysis
│   │   ├── pose.py             # MediaPipe pose estimation
│   │   ├── behaviour.py        # Behaviour analysis + abandoned objects
│   │   ├── reid.py             # Cross-camera re-identification
│   │   ├── clip_engine.py      # CLIP embeddings + semantic search
│   │   ├── crowd.py            # Crowd density + flow analytics
│   │   └── fusion.py           # Threat scoring + scene summary
│   ├── api/
│   │   ├── routes.py           # REST API endpoints
│   │   └── websocket.py        # Real-time WebSocket server
│   └── storage/
│       ├── models.py           # Pydantic + SQLAlchemy models
│       ├── event_store.py      # Event persistence
│       └── retention.py        # Scheduled data purge
├── frontend/
│   └── src/
│       ├── pages/
│       │   └── LoginPage.tsx
│       ├── components/
│       │   ├── LiveGrid.tsx        # Camera grid + AI overlays
│       │   ├── PersonCard.tsx      # Person intelligence panel
│       │   ├── AlertFeed.tsx       # Real-time alert stream
│       │   ├── SemanticSearch.tsx  # CLIP natural language search
│       │   ├── PersonTimeline.tsx  # Cross-camera journey
│       │   ├── CrowdHeatmap.tsx    # Zone density heatmap
│       │   ├── PrivacyBanner.tsx   # Privacy mode indicator
│       │   └── SystemHealth.tsx    # Hardware status
│       ├── hooks/
│       │   ├── useWebSocket.ts
│       │   ├── useAuth.ts
│       │   └── usePersonTracker.ts
│       └── store/
│           └── sceneStore.ts
├── Caddyfile                   # Automatic HTTPS config
├── docker-compose.yml
└── .env.example
```

---

##  Roadmap

- [ ] Mobile app (React Native) for on-the-go alerts
- [ ] Multi-tenant support (multiple operators, role-based access)
- [ ] Zone-based rules engine (custom alerts per zone)
- [ ] ONVIF camera auto-discovery
- [ ] Incident report PDF export
- [ ] Analytics dashboard (daily/weekly trends)
- [ ] Edge deployment (Raspberry Pi 5 + Coral TPU)

---

##  Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create your branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

##  Disclaimer

VisionGuardAI is intended for deployment in locations where camera surveillance is legally permitted and disclosed to individuals being monitored. Always consult local laws and regulations (DPDP Act in India, GDPR in Europe) before deploying in any environment. The authors are not responsible for misuse.

---

##  License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ in Hyderabad, India 🇮🇳

**If this project helped you, please ⭐ star the repo**

</div>
