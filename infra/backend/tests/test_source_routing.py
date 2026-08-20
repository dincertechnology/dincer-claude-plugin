import os
import sys

for key, value in {
    "BUCKET_NAME": "bucket",
    "DEPOT_KEY": "depot.xlsx",
    "TRANSPORT_KEY": "transport.xlsx",
    "COGNITO_ISSUER": "https://issuer.example",
    "COGNITO_CLIENT_ID": "client",
    "COGNITO_LOGIN_DOMAIN": "https://login.example",
}.items():
    os.environ.setdefault(key, value)

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import app


def test_transport_terms_override_wrong_source(monkeypatch):
    seen = []
    monkeypatch.setattr(app, "_workbook_bytes", lambda source: seen.append(source) or b"")
    monkeypatch.setattr(app, "search_workbook", lambda *args: ([], False))

    app.query_data("Adıyaman kamyon fiyatı", source="depo")

    assert seen == ["tasima"]


def test_storage_terms_override_wrong_source(monkeypatch):
    seen = []
    monkeypatch.setattr(app, "_workbook_bytes", lambda source: seen.append(source) or b"")
    monkeypatch.setattr(app, "search_workbook", lambda *args: ([], False))

    app.query_data("Dilovası depolama fiyatı", source="tasima")

    assert seen == ["depo"]


def test_result_hides_source_metadata(monkeypatch):
    monkeypatch.setattr(app, "_workbook_bytes", lambda source: b"")
    monkeypatch.setattr(
        app,
        "search_workbook",
        lambda *args: ([{"source": "tasima", "sheet": "Sheet1", "row": 7, "score": 2, "values": {"İl": "Ağrı"}}], False),
    )

    result = app.query_data("Ağrı taşıma fiyatı")

    assert result == {"results": [{"İl": "Ağrı"}], "message": ""}


def test_empty_result_returns_contact_direction(monkeypatch):
    monkeypatch.setattr(app, "_workbook_bytes", lambda source: b"")
    monkeypatch.setattr(app, "search_workbook", lambda *args: ([], False))

    result = app.query_data("Olmayan ilçe taşıma fiyatı")

    assert result["results"] == []
    assert result["message"] == "Güncel fiyat ve hizmet bilgisi için Dinçer Logistics ile iletişime geçebilirsiniz."
