FROM python:3.9

ENV PYTHONUNBUFFERED=1

RUN apt-get update -y \
    && apt-get -y dist-upgrade \
    && apt-get install -y netcat postgresql-client \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/transportation/
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . /usr/src/transportation/
RUN chmod a+x /usr/src/transportation/entry.sh
EXPOSE 8000
ENTRYPOINT ["./entry.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
