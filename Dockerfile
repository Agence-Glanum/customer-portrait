FROM python:3.10-slim

WORKDIR /app

RUN mkdir /app/data

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN exit
RUN apt-get update

RUN apt-get install -y unixodbc-dev

RUN apt-get install -y libgssapi-krb5-2

COPY . /app

RUN pip3 install -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]