.PHONY: start\
	start \
	stop \
	kill \
	logs \
	test

start:
	docker compose up --remove-orphans -d --build && docker compose logs -f

stop:
	docker compose down

kill:
	docker compose kill
	docker compose down

logs:
	docker compose logs -f app

test:
	docker compose exec app pytest -v

producer:
	docker compose exec app python app/run_producer.py
