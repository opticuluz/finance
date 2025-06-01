FROM nginx:1.28-alpine

COPY ./nginx/default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./nginx/uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV APP_HOST=app
ENV APP_PORT=9000

RUN apk add --no-cache bash
RUN chmod +x /run.sh

VOLUME /vol/static
VOLUME /vol/media

CMD ["/run.sh"]
