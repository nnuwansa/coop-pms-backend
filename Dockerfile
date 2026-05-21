FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN python3 -m venv /home/app/venv && \
    /home/app/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY ./app /app

EXPOSE 8000

CMD ["/home/app/venv/bin/python", "main.py"]