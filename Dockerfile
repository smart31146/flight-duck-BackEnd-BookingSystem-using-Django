# TODO: Pin python version
FROM python:latest
WORKDIR /app
COPY . /app/
RUN python3 -m pip install -r requirements.txt

RUN python3 manage.py migrate

CMD ["python3", "manage.py", "runserver"]