import argparse
import json
import os
import logging
import logging.handlers
import sys
from typing import Callable, Dict, List, Tuple

from reporter.newspaper_nlg_service import NewspaperNlgService

from bottle import Bottle, request, response, run, TEMPLATE_PATH

#
# START INIT
#

# Logging
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

rotating_file_handler = logging.handlers.RotatingFileHandler('reporter.log',
                                                             mode='a',
                                                             maxBytes=5*1024*1024,
                                                             backupCount=2,
                                                             encoding=None,
                                                             delay=0)
rotating_file_handler.setFormatter(formatter)
rotating_file_handler.setLevel(logging.INFO)

log.addHandler(stream_handler)
log.addHandler(rotating_file_handler)


# Bottle
app = Bottle()
service = NewspaperNlgService(
    random_seed=4551546
)
TEMPLATE_PATH.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../views/")
static_root = os.path.dirname(os.path.realpath(__file__)) + "/../static/"


#
# END INIT
#

LANGUAGES = [
    'en', 'fi', 'de'
]

FORMATS = [
    'p', 'ol', 'ul'
]


def allow_cors(func: Callable) -> Callable:
    """ this is a decorator which enable CORS for specified endpoint """

    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return func(*args, **kwargs)

    return wrapper


def generate(language: str, format:str = None, data:str = None) -> Tuple[str, str]:
    return service.run_pipeline(language, format, data)

@app.route('/api/report')
@allow_cors
def api_generate() -> Dict[str, str]:
    language = request.query.language or "en"

    header, body = generate(language)
    return dict({
        "language": language,
        "header": header,
        "body": body,
    })

@app.route('/api/report/json', method='POST')
@allow_cors
def api_generate() -> Dict[str, str]:
    body = json.loads(request.body.read())
    language = body['language']
    format = body['format']
    data = json.dumps(body['data'])

    if language not in LANGUAGES or format not in FORMATS:
        response.status = 400
        return

    header, body = generate(language, format, data)
    return dict({
        "language": language,
        "header": header,
        "body": body,
    })

@app.route('/api/report', method='POST')
@allow_cors
def api_generate() -> Dict[str, str]:
    language = request.forms.get('language')
    format = request.forms.get('format')
    data = request.forms.get('data')
    
    for key in request.forms:
        log.info(f'{key}')
        log.info(request.forms.get(key))

    log.info("{}, {}, {}".format(language, format, data))

    if language not in LANGUAGES or format not in FORMATS:
        response.status = 400
        return

    header, body = generate(language, format, data)
    return dict({
        "language": language,
        "header": header,
        "body": body,
    })

@app.route('/api/languages')
@allow_cors
def get_languages() -> Dict[str, List[str]]:
    return {"languages": LANGUAGES}

@app.route('/api/formats')
@allow_cors
def get_formats() -> Dict[str, List[str]]:
    return {"formats": FORMATS}


def main() -> None:
    log.info("Starting server at 8080")
    run(app, server='meinheld', host='0.0.0.0', port=8080)
    log.info("Stopping")


if __name__ == '__main__':
    main()
    #print(generate())
