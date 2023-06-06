from urllib.parse import urlparse

from validators import url as url_validator


def validate(url):
    errors = []
    if len(url) > 255:
        errors.append("URL превышает 255 символов")
    if not url_validator(url):
        errors.append("Некорректный URL")
    if not url:
        errors.append("URL обязателен")
    if errors:  # добавляем сообщение об ошибке только если есть другие ошибки
        errors.append("Произошла ошибка при проверке")
    return errors  # возвращаем список ошибок, а не результат вызова append()


def normilize(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"
