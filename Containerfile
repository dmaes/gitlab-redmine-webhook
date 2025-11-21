FROM docker.io/library/python:3.14.0

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gitlab-redmine.py .

ENV GUNICORN_CMD_ARGS="--bind=[::]:8000 --workers=1 --access-logfile=- --capture-output --error-logfile=-"

CMD ["gunicorn", "gitlab-redmine:app"]
