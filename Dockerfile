FROM python:3 as compile-image
COPY requirements.txt ./
RUN pip install -r requirements.txt --target=./site-packages

FROM python:3-alpine as run-image
COPY --from=compile-image /site-packages /opt/python-modules
ENV PYTHONPATH="/opt/python-modules"
WORKDIR /app
COPY ./nifi_cluster_coordinator ./
CMD [ "python", "/app/main.py"]
