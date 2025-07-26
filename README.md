

# Rankitech – Backend

A scalable, AI-powered backend system for automating job description and consultant profile matching. This system compares skills and experience using intelligent scoring, ranks top candidates, and automates recruiter communication. Built with **FastAPI**, supports **Docker**, uses **Celery + Redis** for async tasks, and follows modular architecture for production-readiness.

---

## Features

* Intelligent matching of job descriptions to consultant profiles
* Customizable scoring based on skill overlap and experience
* Rank and return top 3 consultant matches
* Email notification simulation (can be integrated with real SMTP)
* Modular and scalable backend using FastAPI
* Task queue support via **Celery + Redis** (or RabbitMQ)
* API-ready for frontend integration
* Dockerized and GitHub-ready with Python virtual environment support

---

## Project Structure

```
rankitech-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                # Entry point for FastAPI app
│   ├── config.py              # Settings & environment variables
│   ├── models/                # Pydantic models
│   ├── api/                   # API routes
│   ├── services/              # Business logic (matching, ranking)
│   ├── core/                  # Core logic (email, utils)
│   └── tasks/                 # Background tasks (Celery)
│
├── tests/                     # Unit and integration tests
│
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Dev environment (API + Redis)
├── requirements.txt           # Python dependencies
├── .env.example               # Example env variables
├── README.md                  # Project documentation
└── venv/                      # Python virtual environment (ignored in .gitignore)
```

---

## Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/your-org/rankitech-backend.git
cd rankitech-backend
```

### 2. Set Up Environment

Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file based on `.env.example`.

### 3. Run the App

```bash
uvicorn app.main:app --reload
```

### 4. Run with Docker

```bash
docker-compose up --build
```

This will start:

* FastAPI backend at `http://localhost:8000`
* Redis (for background tasks)

---

## Tech Stack

* **Language:** Python 3.10+
* **Framework:** FastAPI
* **Task Queue:** Celery
* **Message Broker:** Redis (can be switched to RabbitMQ)
* **Containerization:** Docker & Docker Compose
* **Testing:** Pytest
* **Version Control:** Git, GitHub

---

## API Endpoints (Coming Soon)

### Example

| Method | Endpoint          | Description                       |
| ------ | ----------------- | --------------------------------- |
| POST   | `/match`          | Submit JD and consultant profiles |
| GET    | `/health`         | Health check                      |
| GET    | `/ranked-results` | Get last ranked result (sample)   |

---

## Security & Scalability

* Followed **12-factor app** methodology
* Supports deployment on cloud-native platforms
* Modular design allows plug-and-play with real databases and SMTP

---

## Testing

```bash
pytest tests/
```

---

## Deployment

You can deploy this backend using:

* Docker (recommended)
* AWS/GCP/Azure (container instances)
* Any VM or bare-metal server (via `gunicorn` + `uvicorn`)

---

## License

This project is under the **MIT License**. See [LICENSE](LICENSE) for details.

---



