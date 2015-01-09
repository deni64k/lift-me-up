FROM python:3.4
MAINTAINER Denis Sukhonin <dsukhonin@gmail.com>

ADD . /src
WORKDIR /src

RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "-u", "run.py", "-p", "8080"]
