FROM python:3.12-slim

# Cliente SSH para demostrar el acceso api -> hadoop
RUN apt-get update \
 && apt-get install -y --no-install-recommends openssh-client \
 && rm -rf /var/lib/apt/lists/*

# "ssh hadoop@hadoop" usa la llave que el contenedor hadoop deja en el volumen compartido
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh \
 && printf 'Host hadoop\n  User hadoop\n  IdentityFile /ssh-compartido/id_api\n  StrictHostKeyChecking accept-new\n' \
      > /root/.ssh/config \
 && chmod 600 /root/.ssh/config

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

EXPOSE 8000
CMD ["gunicorn", "--preload", "-w", "2", "-b", "0.0.0.0:8000", "app:app"]
