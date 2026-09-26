.PHONY: install dev-backend dev-frontend dev test

install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8002

dev-frontend:
	cd frontend && npm run dev -- --port 5174

dev:
	$(MAKE) -j2 dev-backend dev-frontend

test:
	cd backend && . .venv/bin/activate && pytest -q
