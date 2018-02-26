FROM python:3

LABEL maintainer='i@AngelMsger.Com'

COPY . /app

WORKDIR /app

RUN pip install -i http://mirrors.163.com/pypi/simple -r requirements.txt

CMD ['python', 'exec.py']