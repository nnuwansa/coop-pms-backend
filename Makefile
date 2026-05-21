
build_frontend:
	docker-compose build frontend

push_frontend:
	docker push ghcr.io/dushmanthasse/coop_pms_fe_service:v1.0.1

build_backend:
	docker-compose build backend

push_backend:
	docker push ghcr.io/dushmanthasse/coop_pms_core_service:v1.0.1

