FROM nginx:1.28-alpine

# COPY ./nginx/* /etc/nginx/
# COPY ./run.sh /run.sh

# ENV APP_HOST=app
# ENV APP_PORT=9000

# RUN apk add --no-cache openssl bash
# RUN chmod +x /run.sh

# VOLUME /vol/static
# VOLUME /vol/media
# VOLUME /vol/www

# CMD ["/run.sh"]




COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY ./nginx/uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV APP_HOST=app
ENV APP_PORT=9000

RUN apk add --no-cache bash
RUN chmod +x /run.sh

VOLUME /vol/static
VOLUME /vol/media

CMD ["/run.sh"]
