FROM python:3.9-alpine

RUN apk update && apk upgrade

# adding chromedriver
RUN apk add --no-cache bash \
    chromium \
    chromium-chromedriver
# Will also need 
RUN mkdir /app
#RUN mkdir /app/logs
#RUN mkdir /app/queries

WORKDIR /app

COPY ./requirements.txt /app

RUN pip install -r requirements.txt

ADD . /app


CMD ["/bin/sh"]
#CMD ["python", "clickreport.py"]