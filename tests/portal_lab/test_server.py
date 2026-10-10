from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import wifit3.portal_lab.server as server_module
from wifit3.portal_lab import PortalLabServer


def test_portal_lab_serves_templates_and_stops():
    portal = PortalLabServer()
    try:
        url = portal.start(open_browser=False)
        assert url.startswith("http://127.0.0.1:")
        with urlopen(url, timeout=2) as response:
            page = response.read().decode("utf-8")
            assert response.status == 200
            assert "Entorno controlado" in page
            assert "La clave introducida no se almacena" in page
        with urlopen(url + "portal.css", timeout=2) as response:
            assert response.status == 200
            assert b".content" in response.read()
        with urlopen(url + "portal.js", timeout=2) as response:
            assert response.status == 200
            assert b"requestSubmit" in response.read()
        assert portal.running
    finally:
        portal.stop()
    assert not portal.running


def test_portal_lab_records_event_without_storing_submitted_value(tmp_path, monkeypatch):
    events_file = tmp_path / "events.jsonl"
    monkeypatch.setattr(server_module, "_EVENTS_FILE", events_file)
    portal = PortalLabServer()
    try:
        url = portal.start(open_browser=False)
        payload = urlencode({"password": "SYNTHETIC-TEST-VALUE"}).encode("utf-8")
        with urlopen(url + "check.html", data=payload, timeout=2) as response:
            page = response.read().decode("utf-8")
            assert response.status == 200
            assert "no se ha almacenado ni verificado" in page
        logged = events_file.read_text(encoding="utf-8")
        assert "synthetic_portal_form_submitted" in logged
        assert '"stored_secret": false' in logged
        assert "SYNTHETIC-TEST-VALUE" not in logged
    finally:
        portal.stop()


def test_portal_lab_rejects_unknown_post_path():
    portal = PortalLabServer()
    try:
        url = portal.start(open_browser=False)
        try:
            urlopen(url + "not-found", data=b"test=1", timeout=2)
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("POST to an unknown path should be rejected")
    finally:
        portal.stop()
