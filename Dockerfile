# app/Dockerfile

FROM python:3.9-slim

EXPOSE 8508

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir "/usr/share/fonts/truetype/freefont/"
RUN cp /app/fonts/* /usr/share/fonts/truetype/freefont/

ENTRYPOINT ["streamlit", "run", "frontend.py", "--server.port=80", "--server.address=0.0.0.0"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]
