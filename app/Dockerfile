FROM python
#FROM ubuntu:latest
MAINTAINER Jeff Sutch, jeff@collettpark.com
RUN apt-get update -y
RUN apt-get install -y python3-pip python3  supervisor
#RUN apt-get install -y python3-pip python3-dev pipenv gunicorn uwsgi supervisor
RUN mkdir -p /var/log/supervisor
VOLUME ["/var/www/webhook/app"]
COPY . /var/www/webhook/app/
RUN pip3 install -r /var/www/webhook/app/requirements.txt
ENV FLASK_APP /var/www/webhook/app/main.py
EXPOSE 6666
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
