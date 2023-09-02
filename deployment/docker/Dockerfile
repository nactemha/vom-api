FROM ghcr.io/coqui-ai/tts-cpu

WORKDIR /app

RUN pip install --upgrade pip
ENV NATS_SERVER=nats://nats.nats.svc:4222

ADD . .

RUN pip install -r requirements.txt

ENV HTTP_PORT=80
EXPOSE 80

ENTRYPOINT ["python", "main.py"]
