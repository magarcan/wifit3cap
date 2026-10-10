from urllib.request import urlopen
from urllib.error import HTTPError

from wifit3.portal_lab import PortalLabServer


def test_portal_lab_serves_local_page_and_stops():
    portal = PortalLabServer()
    try:
        url = portal.start(open_browser=False)
        assert url.startswith("http://127.0.0.1:")
        with urlopen(url, timeout=2) as response:
            page = response.read().decode("utf-8")
            assert response.status == 200
            assert "Entorno de laboratorio" in page
            assert "no solicita, registra ni verifica contraseñas" in page
        assert portal.running
    finally:
        portal.stop()
    assert not portal.running


def test_portal_lab_rejects_form_submissions():
    portal = PortalLabServer()
    try:
        url = portal.start(open_browser=False)
        try:
            urlopen(url, data=b"password=synthetic-test", timeout=2)
        except HTTPError as error:
            assert error.code == 405
        else:
            raise AssertionError("POST should be rejected")
    finally:
        portal.stop()
