# TODO: This is incomplete, this still needs to be fixed

FROM python:slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "/usr/src/app/src/main.py"]
