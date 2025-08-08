# celery_worker.py
from app.tasks import celery

# Run using CLI: celery -A celery_worker.celery worker --loglevel=info
# or keep this only for debug/testing if needed
if __name__ == "__main__":
    celery.worker_main(["worker", "--loglevel=info"])
