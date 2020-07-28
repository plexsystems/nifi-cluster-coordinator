FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY ./src .
CMD [ "python", "/usr/src/app/main.py"]
