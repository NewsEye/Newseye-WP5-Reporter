FROM python:3.6

ENV omorfi 20161115
ENV PYTHONPATH /usr/lib/python3/dist-packages

RUN echo "\nINSTALLING REQUIREMENTS FROM PIP\n"
COPY ["requirements.txt", "requirements.txt"]
RUN pip3 install -r /requirements.txt

RUN echo "\nCOPYING FILES\n"
RUN mkdir app

# Heroku ignores this, required for local testing
EXPOSE 8080

ADD . /app
WORKDIR /app

# Heroku runs as non-root
RUN chmod a+rxw -R /app

RUN adduser --disabled-password myuser
USER myuser

CMD python3 /app/src/server.py $PORT
