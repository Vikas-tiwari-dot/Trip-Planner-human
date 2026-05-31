# 🧭 Pathick — AI-Powered Travel Companion

Pathick is a full-stack travel platform that combines live location sharing, real-time traveler chat, intelligent route planning, local guide discovery, and automatic trip detection in one seamless experience.

## ✨ Features

* 🔐 JWT Authentication & Secure User Management
* 📍 Live Location Sharing with Leaflet Maps & Socket.IO
* 💬 Real-Time Private Chat with Typing Indicators
* 🗺️ Route Planning using OpenStreetMap + OSRM
* 🧳 Automatic Trip Detection & Travel History
* 👤 Local Guide Discovery System
* 🔍 Nearby Travelers & Places Search
* 🤖 AI-Ready Service Architecture

## 🛠️ Tech Stack

**Backend**

* Flask
* Flask-SocketIO
* SQLAlchemy
* JWT Authentication
* bcrypt

**Frontend**

* HTML, CSS, JavaScript
* TailwindCSS
* Leaflet.js

**Database**

* SQLite (Development)
* PostgreSQL (Production)

**Maps & Routing**

* OpenStreetMap
* Nominatim
* OSRM
* Folium

## 🚀 Quick Start

```bash
git clone https://github.com/Vikas-tiwari-dot/Trip-Planner-human
cd pathick

python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

python app.py
```

Open:

```text
http://localhost:5001
```

## ⚙️ Environment Variables

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=sqlite:///database/pathick.db
PORT=5000
TRIP_THRESHOLD_KM=50
```

## 🔒 Security

* JWT Authentication
* bcrypt Password Hashing
* SQLAlchemy ORM Protection
* Rate Limiting
* Environment-based Secrets
* XSS Protection

## 📌 Highlights

* Real-time location tracking
* Live traveler communication
* Smart route generation
* Local guide marketplace
* Automatic travel detection
* Scalable Flask architecture

## 📄 License

MIT License

---

**Built with ❤️ by Vikas for travelers everywhere.**
