FROM python:3.13-alpine
LABEL maintainer="opticuluz"

ENV PYTHONUNBUFFERED=1
ENV PATH="/scripts:${PATH}"
ENV PATH="/py/bin:$PATH"

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
COPY ./scripts /scripts

ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps

RUN chmod +x /scripts/*

RUN mkdir -p /vol/static
RUN mkdir -p /vol/media
RUN mkdir -p /app_logs

RUN adduser --disabled-password --no-create-home django-user
RUN chown -R django-user:django-user /vol
RUN chmod -R 755 /vol/static
RUN chmod -R 755 /vol/media
RUN chown -R django-user:django-user /app_logs
RUN chmod -R 755 /app_logs
USER django-user

CMD ["entrypoint.sh"]