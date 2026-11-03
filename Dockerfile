FROM python:3.12-slim

LABEL maintainer="i@AngelMsger.Com"

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "exec.py"]
