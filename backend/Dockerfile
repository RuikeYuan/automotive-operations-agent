FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY integrations ./integrations
COPY database ./database
COPY knowledge ./knowledge
COPY skills ./skills
COPY tests ./tests
COPY evals ./evals
COPY scripts ./scripts
COPY demo ./demo
COPY alembic.ini pyproject.toml ./
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m backend.app.db.seed && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]

