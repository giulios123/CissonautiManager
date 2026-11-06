import io

import pytest
from PIL import Image

from app.email.card import MAX_UPLOAD_BYTES
from tests.helpers import payload

URL = "/api/admin/email/registration"


def png(size=(600, 300), color=(30, 90, 120), fmt="PNG") -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format=fmt)
    return out.getvalue()


def settings_body(**overrides):
    body = {
        "templates": {
            "it": {
                "subject": "Benvenuto {first_name}!",
                "body": "Ciao {first_name} {last_name},\n\nci vediamo a {event}.",
            },
            "en": {
                "subject": "Welcome {first_name}!",
                "body": "Hi {first_name} {last_name},\n\nsee you at {event}.",
            },
        },
        "card": {
            "text_it": "",
            "text_en": "",
            "text_color": "#ffffff",
            "text_position": "bottom",
        },
    }
    body.update(overrides)
    return body


def upload(client, data=None, name="bg.png", content_type="image/png"):
    return client.put(f"{URL}/image", files={"file": (name, data or png(), content_type)})


def register(client, edition, locale="en", email="ada@example.com"):
    body = payload([edition.slots[0].id], locale=locale, email=email)
    assert client.post("/api/public/registrations", json=body).status_code == 201


class TestSettingsApi:
    def test_needs_an_admin(self, client, admin_client, edition):
        assert client.get(URL).status_code == 401
        assert client.put(URL, json=settings_body()).status_code == 401
        assert client.get(f"{URL}/preview.png").status_code == 401

    def test_participants_are_refused(self, client, make_participant, outbox, edition):
        from tests.test_auth import login

        make_participant("ada@example.com")
        login(client, outbox)
        assert client.get(URL).status_code == 403

    def test_without_an_edition(self, admin_client):
        assert admin_client.get(URL).status_code == 404

    def test_defaults_before_anything_is_saved(self, admin_client, edition):
        data = admin_client.get(URL).json()
        assert data["templates"] == {
            "it": {"subject": "", "body": ""},
            "en": {"subject": "", "body": ""},
        }
        assert data["card"]["has_image"] is False
        assert data["defaults"]["en"]["card_text"].startswith("I'm {first_name} {last_name}")
        assert data["defaults"]["it"]["subject"] == "Iscrizione al {event}"

    def test_saving_and_reading_back(self, admin_client, edition):
        body = settings_body()
        body["card"]["text_en"] = "I'm {first_name} at {event}"
        body["card"]["text_color"] = "#ffbc42"
        body["card"]["text_position"] = "top"
        response = admin_client.put(URL, json=body)
        assert response.status_code == 200
        data = admin_client.get(URL).json()
        assert data["templates"]["en"]["subject"] == "Welcome {first_name}!"
        assert data["card"]["text_en"] == "I'm {first_name} at {event}"
        assert (data["card"]["text_color"], data["card"]["text_position"]) == ("#ffbc42", "top")

    def test_saving_twice_updates_the_same_rows(self, admin_client, edition, db):
        from sqlalchemy import func, select

        from app.models import EmailTemplate, RegistrationCard

        admin_client.put(URL, json=settings_body())
        admin_client.put(URL, json=settings_body())
        assert db.scalar(select(func.count()).select_from(EmailTemplate)) == 2
        assert db.scalar(select(func.count()).select_from(RegistrationCard)) == 1

    @pytest.mark.parametrize("field", ["subject", "body"])
    def test_unknown_placeholder_is_refused_with_a_clear_message(
        self, admin_client, edition, field
    ):
        body = settings_body()
        body["templates"]["it"][field] = "Ciao {nome}"
        response = admin_client.put(URL, json=body)
        assert response.status_code == 422
        assert "{nome}" in str(response.json()["detail"])
        assert "{first_name}" in str(response.json()["detail"])

    def test_unknown_placeholder_in_the_card_text(self, admin_client, edition):
        body = settings_body()
        body["card"]["text_it"] = "Sono {nome}"
        assert admin_client.put(URL, json=body).status_code == 422

    @pytest.mark.parametrize("color", ["red", "#fff", "ffffff", "#gggggg"])
    def test_bad_color(self, admin_client, edition, color):
        body = settings_body()
        body["card"]["text_color"] = color
        assert admin_client.put(URL, json=body).status_code == 422

    def test_bad_position(self, admin_client, edition):
        body = settings_body()
        body["card"]["text_position"] = "left"
        assert admin_client.put(URL, json=body).status_code == 422

    def test_error_messages_follow_the_language(self, admin_client, edition):
        body = settings_body()
        body["templates"]["it"]["body"] = "{x}"
        response = admin_client.put(URL, json=body, headers={"Accept-Language": "en"})
        assert "Unknown placeholder" in str(response.json()["detail"])


class TestImageUpload:
    @pytest.mark.parametrize(
        ("fmt", "mime"), [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")]
    )
    def test_accepted_pictures(self, admin_client, edition, fmt, mime):
        response = upload(admin_client, png(fmt=fmt), content_type=mime)
        assert response.status_code == 200
        assert response.json()["card"]["has_image"] is True

    def test_what_is_stored_is_a_clean_png(self, admin_client, edition, db):
        from sqlalchemy import select

        from app.models import RegistrationCard

        upload(admin_client, png(size=(3000, 1000), fmt="JPEG"), content_type="image/jpeg")
        stored = db.scalar(select(RegistrationCard.image))
        image = Image.open(io.BytesIO(stored))
        assert image.format == "PNG" and image.size == (1600, 533)

    def test_a_text_file_is_refused(self, admin_client, edition):
        response = upload(admin_client, b"not an image", "x.png")
        assert response.status_code == 422
        assert admin_client.get(URL).json()["card"]["has_image"] is False

    def test_a_pdf_renamed_png_is_refused(self, admin_client, edition):
        assert upload(admin_client, b"%PDF-1.4 hello", "fake.png").status_code == 422

    def test_a_gif_is_a_wrong_format(self, admin_client, edition):
        response = upload(admin_client, png(fmt="GIF"), "a.gif", "image/gif")
        assert response.status_code == 422
        assert "JPEG" in response.json()["detail"]

    def test_too_big_is_413(self, admin_client, edition):
        response = upload(admin_client, b"0" * (MAX_UPLOAD_BYTES + 10))
        assert response.status_code == 413

    def test_missing_file_is_422(self, admin_client, edition):
        assert admin_client.put(f"{URL}/image").status_code == 422

    def test_a_participant_cannot_upload(self, client, edition):
        assert upload(client).status_code == 401

    def test_removing_the_picture(self, admin_client, edition):
        upload(admin_client)
        response = admin_client.delete(f"{URL}/image")
        assert response.json()["card"]["has_image"] is False


class TestPreview:
    def get(self, client, query=""):
        response = client.get(f"{URL}/preview.png{query}")
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "image/png"
        return Image.open(io.BytesIO(response.content))

    def test_works_without_a_background(self, admin_client, edition):
        assert self.get(admin_client).size == (1200, 630)

    def test_uses_the_background(self, admin_client, edition):
        upload(admin_client, png(size=(500, 250)))
        assert self.get(admin_client, "?locale=en").size == (500, 250)

    def test_shows_what_is_typed_before_saving(self, admin_client, edition):
        plain = admin_client.get(f"{URL}/preview.png?locale=en").content
        typed = admin_client.get(f"{URL}/preview.png?locale=en&text=Hello+{{first_name}}").content
        assert plain != typed

    def test_unknown_placeholder_in_the_typed_text(self, admin_client, edition):
        assert admin_client.get(f"{URL}/preview.png?text={{x}}").status_code == 422

    def test_bad_language(self, admin_client, edition):
        assert admin_client.get(f"{URL}/preview.png?locale=fr").status_code == 422


class TestTestMessage:
    def test_goes_to_the_admin_with_the_picture(self, admin_client, edition, outbox):
        upload(admin_client)
        admin_client.put(URL, json=settings_body())
        response = admin_client.post(f"{URL}/test?locale=en")
        assert response.status_code == 200
        assert "boss@example.com" in response.json()["message"]
        message = outbox.sent[-1]
        assert message.to == "boss@example.com"
        # the admin fixture is a person called Ada Lovelace: the sample uses the admin's own name
        assert message.subject == "Welcome Ada!"
        assert message.attachments and message.attachments[0].content_type == "image/png"
        assert "https://camp.example.org/login/verify?token=EXAMPLE" in message.body

    def test_without_a_picture_email_has_html_and_text_bodies(self, admin_client, edition, outbox):
        admin_client.post(f"{URL}/test?locale=it")
        assert outbox.sent[-1].html is not None and outbox.sent[-1].attachments == ()

    def test_without_edition_slots_email_still_sends(self, admin_client, edition, outbox, db):
        from app.models import Slot

        edition.start_date = None
        edition.end_date = None
        db.query(Slot).filter_by(edition_id=edition.id).delete()
        db.commit()

        response = admin_client.post(f"{URL}/test?locale=en")

        assert response.status_code == 200
        assert "1 day of attendance" not in outbox.sent[-1].body
        assert "Payment reference:" in outbox.sent[-1].body

    def test_needs_an_admin(self, client, edition):
        assert client.post(f"{URL}/test").status_code == 401


class TestRegistrationEmail:
    def test_default_email_is_unchanged_until_the_admin_writes(self, client, edition, outbox):
        register(client, edition, "it")
        message = outbox.sent[0]
        assert message.subject == "Iscrizione al Cissonauti Summer Camp 2026"
        assert message.body.startswith("Ciao Ada,\n\ngrazie per esserti iscritto")
        assert message.html is not None and message.attachments == ()
        assert "font-size:13px" in message.html

    def test_custom_text_and_subject_in_each_language(self, admin_client, client, edition, outbox):
        admin_client.put(URL, json=settings_body())
        register(client, edition, "en")
        english = outbox.sent[-1]
        assert english.subject == "Welcome Ada!"
        assert english.body.startswith(
            "Hi Ada Lovelace,\n\nsee you at Cissonauti Summer Camp 2026."
        )
        register(client, edition, "it", email="bea@example.com")
        italian = outbox.sent[-1]
        assert italian.subject == "Benvenuto Ada!"
        assert "ci vediamo a Cissonauti Summer Camp 2026." in italian.body

    def test_the_essential_block_is_always_there(self, admin_client, client, edition, outbox):
        body = settings_body()
        body["templates"]["en"]["body"] = "Just a hello"
        admin_client.put(URL, json=body)
        register(client, edition, "en")
        text = outbox.sent[-1].body
        assert text.startswith("Just a hello")
        for expected in (
            "1 day of attendance:",
            "Full days, except where periods are listed.",
            "Mon 13 Jul",
            "Payment reference: CSC-",
            "How to pay:",
            "/login/verify?token=",
        ):
            assert expected in text

    def test_empty_fields_fall_back_to_the_standard_wording(
        self, admin_client, client, edition, outbox
    ):
        body = settings_body()
        body["templates"]["en"] = {"subject": "", "body": ""}
        admin_client.put(URL, json=body)
        register(client, edition, "en")
        assert outbox.sent[-1].subject == "Registration for Cissonauti Summer Camp 2026"
        assert outbox.sent[-1].body.startswith("Hi Ada,")

    def test_the_picture_carries_the_name_and_the_dates(
        self, admin_client, client, edition, outbox
    ):
        upload(admin_client)
        register(client, edition, "en")
        message = outbox.sent[-1]
        assert len(message.attachments) == 1
        attachment = message.attachments[0]
        assert attachment.content_id == "registration-card"
        assert Image.open(io.BytesIO(attachment.content)).size == (600, 300)
        assert "cid:registration-card" in message.html
        assert (
            "I&#x27;m Ada Lovelace and I&#x27;ll be at Cissonauti Summer Camp 2026 "
            "from 13 July 2026 to 17 July 2026"
        ) in message.html

    def test_italian_picture_text(self, admin_client, client, edition, outbox):
        upload(admin_client)
        register(client, edition, "it")
        assert (
            "Sono Ada Lovelace e sarò a Cissonauti Summer Camp 2026 "
            "dal 13 luglio 2026 al 17 luglio 2026"
        ) in outbox.sent[-1].html

    def test_a_custom_picture_text(self, admin_client, client, edition, outbox):
        upload(admin_client)
        body = settings_body()
        body["card"]["text_en"] = "{first_name} is coming!"
        admin_client.put(URL, json=body)
        register(client, edition, "en")
        assert 'alt="Ada is coming!"' in outbox.sent[-1].html

    def test_html_is_escaped(self, admin_client, client, edition, outbox, db):
        upload(admin_client)
        register(client, edition, "en", email="x@example.com")
        # A person who types HTML in their name must not inject it into the email.
        body = payload([edition.slots[1].id], locale="en", email="mal@example.com")
        body["first_name"] = "<script>alert(1)</script>"
        body["last_name"] = '"><img src=x>'
        assert client.post("/api/public/registrations", json=body).status_code == 201
        html = outbox.sent[-1].html
        assert "<script>" not in html and "<img src=x>" not in html
        assert "&lt;script&gt;" in html

    def test_the_link_in_the_html_is_clickable(self, admin_client, client, edition, outbox):
        upload(admin_client)
        register(client, edition, "en")
        assert '<a href="https://camp.example.org/login/verify?token=' in outbox.sent[-1].html

    def test_no_picture_for_someone_only_on_a_waitlist(
        self, admin_client, client, edition, outbox, fill_slot
    ):
        upload(admin_client)
        slot = edition.slots[0]
        fill_slot(slot)
        body = payload([], waitlist_slot_ids=[slot.id], locale="en")
        assert client.post("/api/public/registrations", json=body).status_code == 201
        assert outbox.sent[-1].attachments == ()

    def test_removing_the_picture_keeps_html_and_text_bodies(
        self, admin_client, client, edition, outbox
    ):
        upload(admin_client)
        admin_client.delete(f"{URL}/image")
        register(client, edition, "en")
        assert outbox.sent[-1].html is not None
        assert "cid:registration-card" not in outbox.sent[-1].html
        assert outbox.sent[-1].attachments == ()
