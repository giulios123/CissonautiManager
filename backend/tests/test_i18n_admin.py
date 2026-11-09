import csv
import io

import pytest

from app.admin_texts import LABELS_EN
from app.models import Slot
from tests.helpers import d

CSV_URLS = [
    "/api/admin/registrations",
    "/api/admin/views/slots",
    "/api/admin/views/week",
    "/api/admin/views/meals",
    "/api/admin/views/contributions",
    "/api/admin/views/payments-review",
    "/api/admin/views/report",
    "/api/admin/activities",
    "/api/admin/guests",
]


def parse(response):
    assert response.status_code == 200, response.text
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


def filename(response) -> str:
    return response.headers["content-disposition"].split('filename="')[1].rstrip('"')


class TestCsvLanguage:
    @pytest.mark.parametrize("url", CSV_URLS)
    def test_every_italian_header_has_an_english_version(self, admin_client, edition, url):
        header = parse(admin_client.get(f"{url}?format=csv"))[0]
        missing = [cell for cell in header if cell not in LABELS_EN]
        assert missing == [], f"add to LABELS_EN: {missing}"

    @pytest.mark.parametrize("url", CSV_URLS)
    def test_english_download_has_no_italian_header(self, admin_client, edition, url):
        italian = parse(admin_client.get(f"{url}?format=csv"))[0]
        english = parse(admin_client.get(f"{url}?format=csv&lang=en"))[0]
        assert [LABELS_EN[cell] for cell in italian] == english

    def test_the_language_can_come_from_the_header(self, admin_client, edition):
        response = admin_client.get(
            "/api/admin/registrations?format=csv", headers={"Accept-Language": "en"}
        )
        assert parse(response)[0][:3] == ["First name", "Last name", "Email"]

    def test_the_address_wins_over_the_header(self, admin_client, edition):
        response = admin_client.get(
            "/api/admin/registrations?format=csv&lang=it", headers={"Accept-Language": "en"}
        )
        assert parse(response)[0][:3] == ["Nome", "Cognome", "Email"]

    def test_file_names_follow_the_language(self, admin_client, edition):
        italian = admin_client.get("/api/admin/views/slots?format=csv")
        english = admin_client.get("/api/admin/views/slots?format=csv&lang=en")
        assert filename(italian).startswith("giorni-slot-")
        assert filename(english).startswith("days-slots-")

    def test_report_rows_are_in_english(self, admin_client, edition):
        rows = parse(admin_client.get("/api/admin/views/report?format=csv&lang=en"))
        sections = {row[0] for row in rows[1:]}
        assert {"Registrations", "Attendance", "Meals", "Income", "Waitlist"} <= sections
        labels = {row[1] for row in rows[1:]}
        assert "Total due" in labels and "People with a place" in labels
        assert "Totale dovuto" not in labels

    def test_report_in_italian_is_unchanged(self, admin_client, edition):
        rows = parse(admin_client.get("/api/admin/views/report?format=csv"))
        assert rows[0] == ["Sezione", "Voce", "Confermate", "In attesa di pagamento", "Totale"]
        assert "Iscrizioni" in {row[0] for row in rows[1:]}

    def test_booleans_follow_the_language(self, admin_client, edition, db, make_participant):
        from app.csv_export import format_cell
        from app.i18n import _current

        assert format_cell(True) == "sì"
        token = _current.set("en")
        try:
            assert (format_cell(True), format_cell(False)) == ("yes", "no")
        finally:
            _current.reset(token)

    def test_the_labels_table_has_no_empty_value(self):
        assert all(value.strip() for value in LABELS_EN.values())


class TestAdminViewsInEnglish:
    def test_payments_to_review_reason(
        self, admin_client, db, make_participant, make_booking, slot_ids
    ):
        from app.models import STATUS_EXPIRED
        from tests.test_change_slots import pay

        booking = make_booking(
            make_participant("ada@example.com"),
            [db.get(Slot, slot_ids[(d(13), "morning")])],
            status=STATUS_EXPIRED,
        )
        pay(db, booking, 500)
        italian = admin_client.get("/api/admin/views/payments-review").json()[0]
        english = admin_client.get(
            "/api/admin/views/payments-review", headers={"Accept-Language": "en"}
        ).json()[0]
        assert italian["reason_label"] == "Scaduta con pagamenti registrati"
        assert english["reason_label"] == "Expired with recorded payments"

    def test_warning_when_an_expired_booking_has_payments(
        self, admin_client, db, make_participant, make_booking, slot_ids
    ):
        from app.models import STATUS_EXPIRED
        from tests.test_change_slots import pay

        booking = make_booking(
            make_participant("ada@example.com"),
            [db.get(Slot, slot_ids[(d(13), "morning")])],
            status=STATUS_EXPIRED,
        )
        pay(db, booking, 500)
        english = admin_client.get(
            f"/api/admin/registrations/{booking.id}", headers={"Accept-Language": "en"}
        ).json()
        assert english["warning"] == "There are payments recorded on an expired booking."
        italian = admin_client.get(f"/api/admin/registrations/{booking.id}").json()
        assert italian["warning"] == "Ci sono pagamenti registrati su una prenotazione scaduta."

    def test_removal_blocked_reason_in_english(self, admin_client):
        admins = admin_client.get("/api/admin/admins", headers={"Accept-Language": "en"}).json()
        assert admins[0]["blocked_reason"] == "You can't remove yourself: ask another admin."
