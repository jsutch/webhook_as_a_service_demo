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
#WORKDIR /var/www/webhook/app
EXPOSE 6666
#CMD python3 -m flask run --host=0.0.0.0 --port=6666
#CMD python3 worker.py
#CMD [ "/usr/bin/python3", "worker.py" ] # This works
##CMD [ "pipenv", "run", "gunicorn", "-w", "4", "-b", ":6666", "--certfile", "/certs/fullchain.pem", "--keyfile", "/certs/privkey.pem", "main:app" ]
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
#CMD ["/usr/bin/supervisord", "-c /var/www/webhook/app/supervisord.conf"]
CMD ["/usr/bin/supervisord"]
