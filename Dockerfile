FROM tiangolo/uvicorn-gunicorn:python3.7

RUN pip install ariadne graphqlclient uvicorn gunicorn asgi-lifespan python-dotenv requests numpy
RUN pip install ortools

COPY ./app /app