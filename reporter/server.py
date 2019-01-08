import argparse
import os
import sys
from typing import Callable, Tuple, Dict, List

from reporter.newspaper_nlg_service import NewspaperNlgService

from bottle import Bottle, request, response, run, TEMPLATE_PATH

#
# START INIT
#

# Logging
import logging

formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log = logging.getLogger('root')
log.setLevel(logging.INFO)
# log.setLevel(5) # Enable for way too much logging, even more than DEBUG
log.addHandler(handler)

# CLI parameters
parser = argparse.ArgumentParser(description='Run the Reporter server.')
parser.add_argument('port', type=int, default=8080, help='port number to attach to')
parser.add_argument('--force-cache-refresh', action='store_true', default=False, help="re-compute all local caches")
server_args = parser.parse_args()
sys.argv = sys.argv[0:1]

# Bottle
app = Bottle()
service = NewspaperNlgService(
    random_seed=4551546,
    force_cache_refresh=server_args.force_cache_refresh
)
TEMPLATE_PATH.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../views/")
static_root = os.path.dirname(os.path.realpath(__file__)) + "/../static/"


#
# END INIT
#


def allow_cors(func: Callable) -> Callable:
    """ this is a decorator which enable CORS for specified endpoint """

    def wrapper(*args, **kwargs):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return func(*args, **kwargs)

    return wrapper


def get_article(language: str, where: str, where_type: str) -> Tuple[str, str]:
    return service.run_pipeline(language, where, where_type)


@app.route('/api/report')
@allow_cors
def news_api() -> Dict[str, str]:
    language = request.query.language or "en"
    where = request.query.where or None
    where_type = request.query.where_type or None

    if not where:
        response.status = 400
        return {"error": "Must have at least one of the following query parameters: 'where'"}

    header, body = get_article(language, where, where_type)
    return dict({
        "where": where,
        "where_type": where_type,
        "language": language,
        "header": header,
        "body": body,
    })


@app.route('/api/languages')
@allow_cors
def get_languages() -> Dict[str, List[str]]:
    return {"languages": ["en"]}


def main() -> None:
    log.info("Starting with options port={}".format(server_args.port))
    run(app, server='meinheld', host='0.0.0.0', port=server_args.port)
    log.info("Stopping")


if __name__ == '__main__':
    main()
