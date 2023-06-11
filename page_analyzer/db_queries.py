from .models import Urls, UrlChecks


def get_url_by_name(db_session, name):
    return db_session.query(Urls).filter_by(name=name).first()


def add_new_url(db_session, name):
    new_url = Urls(name=name)
    db_session.add(new_url)
    db_session.commit()
    return new_url


def get_url_by_id(db_session, url_id):
    return db_session.query(Urls).get(url_id)


def get_all_urls(db_session):
    return db_session.query(Urls).all()


def get_checks_by_url_id(db_session, url_id):
    return db_session.query(UrlChecks).filter_by(url_id=url_id).order_by(
        UrlChecks.created_at.desc()).all()


def add_new_check(session, url_id, created_at, status_code, h1, description, title):
    check = UrlChecks(url_id=url_id, created_at=created_at, status_code=status_code, h1=h1, description=description, title=title)
    session.add(check)
    session.commit()
