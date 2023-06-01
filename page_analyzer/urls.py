from urllib.parse import urlparse

from validators import url as url_validator


def validate(url):
    errors = []
    if len(url) > 255:
        errors.append("URL is too long")
    if not url_validator(url):
        errors.append("URL is invalid")
    if not url:
        errors.append("URL is required")
    return errors

def normilize(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"

