from datetime import date

from sqlalchemy import select

from app.models import STATUS_CONFIRMED, Edition, ParticipantEditionProfile
from tests.test_auth import login


def test_public_location_catalogs_are_local_and_searchable(client):
    cities = client.get("/api/public/municipalities", params={"q": "Torino"})
    assert cities.status_code == 200
    torino = next(item for item in cities.json() if item["name"] == "Torino")
    assert torino["province"] == "TO"
    assert torino["region"] == "Piemonte"
    assert torino["istat_code"] == "001272"
    homonyms = client.get("/api/public/municipalities", params={"q": "Livo"}).json()
    assert {(item["name"], item["province"]) for item in homonyms if item["name"] == "Livo"} == {
        ("Livo", "CO"),
        ("Livo", "TN"),
    }

    countries = client.get("/api/public/countries")
    assert countries.status_code == 200
    assert {item["name"] for item in countries.json()} >= {"Italy", "United States"}


def test_profile_apis_require_authentication(client, make_participant):
    participant = make_participant("private@example.com")
    assert client.get("/api/me/profile").status_code == 401
    assert client.get(f"/api/admin/participants/{participant.id}/profile").status_code == 401


def test_authenticated_profile_reports_missing_fields_and_saves_profile(
    client, db, outbox, make_participant, edition
):
    participant = make_participant("legacy@example.com")
    login(client, outbox, participant.email)

    initial = client.get("/api/me/profile").json()
    assert initial["complete"] is False
    assert "phone" in initial["missing_fields"]
    assert "city" in initial["missing_fields"]

    response = client.put(
        "/api/me/profile",
        json={
            "phone": "+39 333 1234567",
            "telegram": "I don't have it",
            "linkedin": "https://linkedin.com/in/ada",
            "city": "Torino",
            "province": "TO",
            "region": "Piemonte",
            "country": "Italia",
            "istat_code": "001272",
            "job_title": "Studente",
            "company": "Nessuna azienda",
            "expectations": "Conoscere persone nuove",
            "attended_previous": False,
        },
    )
    assert response.status_code == 204
    saved = client.get("/api/me/profile").json()
    assert saved["complete"] is True
    assert saved["missing_fields"] == []
    assert saved["profile"]["company"] == "Nessuna azienda"
    db.refresh(participant)
    assert participant.phone == "+39 333 1234567"
    assert db.scalar(select(ParticipantEditionProfile)).attendance_source == "declared"


def test_profile_rejects_municipality_code_that_does_not_match_city(
    client, outbox, make_participant, edition
):
    participant = make_participant("legacy@example.com")
    login(client, outbox, participant.email)
    response = client.put(
        "/api/me/profile",
        json={
            "phone": "+39 333 1234567",
            "telegram": "@ada",
            "linkedin": "https://www.linkedin.com/in/ada",
            "city": "Milano",
            "province": "MI",
            "region": "Lombardia",
            "country": "Italia",
            "istat_code": "001272",
            "job_title": "Studentessa",
            "company": "Nessuna azienda",
            "expectations": "Conoscere persone nuove",
            "attended_previous": False,
        },
    )
    assert response.status_code == 422


def test_confirmed_booking_in_previous_edition_overrides_declared_answer(
    client, db, outbox, make_participant, make_booking, edition
):
    participant = make_participant("returning@example.com")
    previous = Edition(
        name="Camp precedente",
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 7),
        is_active=False,
    )
    db.add(previous)
    db.flush()
    booking = make_booking(participant, [], status=STATUS_CONFIRMED)
    booking.edition_id = previous.id
    db.commit()
    login(client, outbox, participant.email)

    response = client.put(
        "/api/me/profile",
        json={
            "phone": "+39 333 1234567",
            "telegram": "Non possiedo",
            "linkedin": "Non possiedo",
            "city": "Torino",
            "province": "TO",
            "region": "Piemonte",
            "country": "Italia",
            "istat_code": "001272",
            "job_title": "Studente",
            "company": "Nessuna azienda",
            "expectations": "Conoscere persone nuove",
            "attended_previous": False,
        },
    )
    assert response.status_code == 204
    profile = db.scalar(select(ParticipantEditionProfile))
    assert profile.attended_previous is True
    assert profile.attendance_source == "derived"
    assert profile.previous_edition_id == previous.id


def test_admin_can_review_and_correct_profile_without_a_booking(
    admin_client, db, make_participant, edition
):
    participant = make_participant("no-booking@example.com")
    before = admin_client.get(f"/api/admin/participants/{participant.id}/profile")
    assert before.status_code == 200
    assert before.json()["profile"] is None
    response = admin_client.put(
        f"/api/admin/participants/{participant.id}/profile",
        json={
            "phone": "+39 333 1234567",
            "telegram": "Non possiedo",
            "linkedin": "Non possiedo",
            "city": "Aosta",
            "province": "AO",
            "region": "Valle d'Aosta/Vallée d'Aoste",
            "country": "Italia",
            "istat_code": "007003",
            "job_title": "Pensionato",
            "company": "Nessuna azienda",
            "expectations": "Imparare",
            "attended_previous": False,
        },
    )
    assert response.status_code == 204
    saved = admin_client.get(f"/api/admin/participants/{participant.id}/profile").json()
    assert saved["profile"]["city"] == "Aosta"
