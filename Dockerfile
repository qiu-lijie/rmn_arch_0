FROM python:3.8.10

ADD ./requirements /code/requirements

WORKDIR /code/

RUN pip install --upgrade pip && pip install -r requirements/local.txt

CMD python manage.py migrate && python manage.py runserver_plus 0.0.0.0:8000
