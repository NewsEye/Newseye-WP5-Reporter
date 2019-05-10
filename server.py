import argparse
import json
import os
import logging
import sys
from typing import Callable, Dict, List, Tuple

from reporter.newspaper_nlg_service import NewspaperNlgService

from bottle import Bottle, request, response, run, TEMPLATE_PATH

#
# START INIT
#

# Logging
formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)
# log.setLevel(5) # Enable for way too much logging, even more than DEBUG
log.addHandler(handler)

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
    'en'
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
    data = body['data']

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
def get_languages() -> Dict[str, List[str]]:
    return {"formats": FORMATS}


def main() -> None:
    log.info("Starting server at 8080")
    run(app, server='meinheld', host='0.0.0.0', port=8080)
    log.info("Stopping")


if __name__ == '__main__':
    main()
    #print(generate())
