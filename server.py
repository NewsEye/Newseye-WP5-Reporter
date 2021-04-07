import json
import logging.handlers
import os
from typing import Callable, Dict, List, Optional, Tuple

import bottle
from bottle import TEMPLATE_PATH, Bottle, request, response, run

from reporter.newspaper_nlg_service import NewspaperNlgService

#
# START INIT
#

# Logging
log = logging.getLogger("root")
log.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

rotating_file_handler = logging.handlers.RotatingFileHandler(
    "reporter.log", mode="a", maxBytes=5 * 1024 * 1024, backupCount=2, encoding=None, delay=0
)
rotating_file_handler.setFormatter(formatter)
rotating_file_handler.setLevel(logging.INFO)

log.addHandler(stream_handler)
log.addHandler(rotating_file_handler)


# Bottle
bottle.BaseRequest.MEMFILE_MAX = 512 * 1024 * 1024  # Allow up to 512MB requests
app = Bottle()
service = NewspaperNlgService(random_seed=4551546)
TEMPLATE_PATH.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../views/")
static_root = os.path.dirname(os.path.realpath(__file__)) + "/../static/"

#
# END INIT
#

FORMATS = ["p", "ol", "ul"]


def allow_cors(func: Callable) -> Callable:
    """ this is a decorator which enable CORS for specified endpoint """

    def wrapper(*args, **kwargs):
        response.headers["Access-Control-Allow-Origin"] = "*"
        return func(*args, **kwargs)

    return wrapper


def generate(language: str, format: str = None, data: str = None, links: bool = False) -> Tuple[str, str, List[str]]:
    return service.run_pipeline(language, format, data, links)


@app.route("/api/report/json", method="POST")
@allow_cors
def api_generate_json() -> Optional[Dict[str, str]]:
    body = json.loads(request.body.read())
    language = body["language"]
    format = body["format"]
    links = body.get("links", False)
    data = json.dumps(body["data"])

    if language not in service.get_languages() or format not in FORMATS:
        response.status = 400
        return

    header, body, errors = generate(language, format, data, links)
    output = {"language": language, "head": header, "body": body}
    if errors:
        output["errors"] = errors
    return output


@app.route("/api/report", method="POST")
@allow_cors
def api_generate() -> Optional[Dict[str, str]]:
    language = request.forms.get("language")
    format = request.forms.get("format")
    data = request.forms.get("data")
    links = request.forms.get("links", "") == "true"

    if language not in service.get_languages() or format not in FORMATS:
        response.status = 400
        return

    header, body, errors = generate(language, format, data, links)
    output = {"language": language, "head": header, "body": body}
    if errors:
        output["errors"] = errors
    return output


@app.route("/api/languages")
@allow_cors
def get_languages() -> Dict[str, List[str]]:
    return {"languages": service.get_languages()}


@app.route("/api/formats")
@allow_cors
def get_formats() -> Dict[str, List[str]]:
    return {"formats": FORMATS}


def main() -> None:
    log.info("Starting server at 8080")
    run(app, server="meinheld", host="0.0.0.0", port=8080)
    log.info("Stopping")


if __name__ == "__main__":
    main()
