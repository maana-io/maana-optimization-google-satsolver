FROM tiangolo/uvicorn-gunicorn:python3.7

WORKDIR /

COPY requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt
RUN pip install ortools
COPY ./app /app
COPY start.sh /start.sh
RUN chmod +x /start.sh


