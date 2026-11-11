from datetime import date

import pytest
from sqlalchemy import func, select

from app.models import (
    CATEGORY_INTERNAL_NON_PAYING,
    ROLE_ADMIN,
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    AuditLog,
    Benefit,
    BenefitDelivery,
    BookingRefund,
    Payment,
    Slot,
)
from app.services import benefit_deliveries as service
from tests.helpers import d


def slot(db, day=13, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def boss(make_participant):
    return make_participant("boss@example.com", role=ROLE_ADMIN, first_name="Boss")


@pytest.fixture
def bottle(db, edition):
    benefit = Benefit(edition_id=edition.id, name_it="Borraccia", name_en="Bottle")
    db.add(benefit)
    db.commit()
    return benefit


@pytest.fixture
def people(db, edition, make_participant, make_booking, clock, boss):
    """A paid the base fee, B paid nothing, C is a speaker, D has the fee exempted."""

    def pay(booking, cents):
        db.add(
            Payment(
                booking_id=booking.id,
                amount_cents=cents,
                channel="iban",
                paid_on=date(2026, 7, 2),
                recorded_by_id=boss.id,
            )
        )
        db.commit()

    made = {}
    for key, last in (("a", "Alfa"), ("b", "Bravo"), ("c", "Charlie"), ("d", "Delta")):
        person = make_participant(f"{key}@example.com", first_name=key.upper(), last_name=last)
        made[key] = (person, make_booking(person, [slot(db)]))
    pay(made["a"][1], edition.base_fee_cents)
    made["c"][1].category = CATEGORY_INTERNAL_NON_PAYING
    made["d"][1].fee_exempt = True
    db.commit()
    return made


def names(rows):
    return [r.last_name for r in rows]


def test_the_list_has_only_who_is_entitled(db, edition, bottle, people, clock):
    rows = service.rows_for(db, edition, bottle, clock())
    assert names(rows) == ["Alfa", "Charlie", "Delta"]
    assert {r.state for r in rows} == {"to_deliver"}


def test_search_and_state_filters(db, edition, bottle, people, boss, clock):
    service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    assert names(service.rows_for(db, edition, bottle, clock(), query="char")) == ["Charlie"]
    assert names(service.rows_for(db, edition, bottle, clock(), state="delivered")) == ["Alfa"]
    assert names(service.rows_for(db, edition, bottle, clock(), state="pending")) == [
        "Charlie",
        "Delta",
    ]


def test_deliver_registers_who_and_when(db, edition, bottle, people, boss, clock):
    delivery, created = service.deliver(
        db, boss, edition, people["a"][0].id, bottle.id, None, clock()
    )
    assert created
    assert (delivery.delivered_by_id, delivery.delivered_at) == (boss.id, clock())
    row = service.rows_for(db, edition, bottle, clock())[0]
    assert row.state == "delivered"
    log = db.scalar(select(AuditLog).where(AuditLog.action == "benefit_delivered"))
    assert log.booking_id == people["a"][1].id
    assert log.participant_id == people["a"][0].id
    assert log.detail == "Borraccia: A Alfa"


def test_a_repeated_request_is_one_delivery(db, edition, bottle, people, boss, clock):
    first, created = service.deliver(
        db, boss, edition, people["a"][0].id, bottle.id, "key-1", clock()
    )
    again, created_again = service.deliver(
        db, boss, edition, people["a"][0].id, bottle.id, "key-1", clock()
    )
    assert (created, created_again) == (True, False)
    assert again.id == first.id
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 1


def test_a_second_admin_gets_the_existing_delivery(
    db, edition, bottle, people, boss, make_participant, clock
):
    other = make_participant("other@example.com", role=ROLE_ADMIN)
    first, _ = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, "key-1", clock())
    second, created = service.deliver(
        db, other, edition, people["a"][0].id, bottle.id, "key-2", clock()
    )
    assert not created
    assert second.id == first.id
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 1


def test_a_race_is_settled_by_the_unique_index(
    db, edition, bottle, people, boss, clock, monkeypatch
):
    first, _ = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    calls = []
    real = service._active

    def blind_once(db_, participant_id, benefit_id):
        calls.append(1)
        return None if len(calls) == 1 else real(db_, participant_id, benefit_id)

    monkeypatch.setattr(service, "_active", blind_once)
    again, created = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    assert not created
    assert again.id == first.id
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 1


def test_who_is_not_entitled_gets_nothing(db, edition, bottle, people, boss, clock):
    with pytest.raises(service.NotEntitled):
        service.deliver(db, boss, edition, people["b"][0].id, bottle.id, None, clock())
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 0


def test_a_retired_benefit_takes_no_new_delivery(db, edition, bottle, people, boss, clock):
    bottle.retired = True
    db.commit()
    with pytest.raises(service.BenefitRetired):
        service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())


def test_an_unknown_benefit_or_person_is_refused(db, edition, bottle, people, boss, clock):
    with pytest.raises(service.BenefitNotFound):
        service.deliver(db, boss, edition, people["a"][0].id, 999, None, clock())
    with pytest.raises(service.PersonNotFound):
        service.deliver(db, boss, edition, 999, bottle.id, None, clock())


def test_annul_needs_a_reason_and_allows_a_new_delivery(db, edition, bottle, people, boss, clock):
    delivery, _ = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    with pytest.raises(service.ReasonRequired):
        service.annul(db, boss, edition, delivery.id, "  ", clock())
    annulled, changed = service.annul(
        db, boss, edition, delivery.id, "Consegnata alla persona sbagliata", clock()
    )
    assert changed
    assert annulled.annulled_by_id == boss.id
    row = [r for r in service.rows_for(db, edition, bottle, clock()) if r.last_name == "Alfa"][0]
    assert row.state == "to_deliver"
    assert [a.annul_reason for a in row.annulled] == ["Consegnata alla persona sbagliata"]
    again, created = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    assert created
    assert again.id != delivery.id
    assert db.scalar(select(func.count()).select_from(BenefitDelivery)) == 2


def test_annulling_twice_changes_and_logs_nothing(db, edition, bottle, people, boss, clock):
    delivery, _ = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    service.annul(db, boss, edition, delivery.id, "Errore", clock())
    _, changed = service.annul(db, boss, edition, delivery.id, "Altro motivo", clock())
    assert not changed
    assert delivery.annul_reason == "Errore"
    assert (
        db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == "benefit_annulled")
        )
        == 1
    )


def test_a_delivery_of_another_edition_is_not_found(db, edition, bottle, people, boss, clock):
    from app.models import Edition

    other = Edition(
        name="Old", start_date=edition.start_date, end_date=edition.end_date, is_active=False
    )
    db.add(other)
    db.commit()
    delivery, _ = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    with pytest.raises(service.DeliveryNotFound):
        service.annul(db, boss, other, delivery.id, "x", clock())
    with pytest.raises(service.BenefitNotFound):
        service.deliver(db, boss, other, people["a"][0].id, bottle.id, None, clock())


class TestEntitlementLost:
    def deliver_to_c(self, db, edition, bottle, people, boss, clock):
        service.deliver(db, boss, edition, people["c"][0].id, bottle.id, None, clock())

    def row(self, db, edition, bottle, clock, last):
        rows = {r.last_name: r for r in service.rows_for(db, edition, bottle, clock())}
        return rows.get(last)

    def test_a_category_change_keeps_the_delivery_marked(
        self, db, edition, bottle, people, boss, clock
    ):
        self.deliver_to_c(db, edition, bottle, people, boss, clock)
        people["c"][1].category = "ordinary"
        db.commit()
        row = self.row(db, edition, bottle, clock, "Charlie")
        assert row.state == "delivered_without_entitlement"
        assert not row.entitled

    def test_regaining_the_entitlement_clears_the_mark(
        self, db, edition, bottle, people, boss, clock
    ):
        self.deliver_to_c(db, edition, bottle, people, boss, clock)
        people["c"][1].category = "ordinary"
        db.commit()
        people["c"][1].category = CATEGORY_INTERNAL_NON_PAYING
        db.commit()
        assert self.row(db, edition, bottle, clock, "Charlie").state == "delivered"

    def test_a_cancelled_booking_keeps_the_delivery(self, db, edition, bottle, people, boss, clock):
        service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
        people["a"][1].status = STATUS_CANCEL_REQUESTED
        db.commit()
        assert self.row(db, edition, bottle, clock, "Alfa").state == "delivered_without_entitlement"

    def test_an_expired_booking_is_not_entitled(self, db, edition, bottle, people, boss, clock):
        people["a"][1].status = STATUS_EXPIRED
        db.commit()
        assert self.row(db, edition, bottle, clock, "Alfa") is None

    def test_a_refund_below_the_base_fee_removes_the_entitlement(
        self, db, edition, bottle, people, boss, clock
    ):
        service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
        people["a"][1].status = STATUS_CONFIRMED
        db.add(
            BookingRefund(
                booking_id=people["a"][1].id,
                amount_cents=100,
                channel="iban",
                refunded_on=date(2026, 7, 3),
                recorded_by_id=boss.id,
            )
        )
        db.commit()
        db.expire_all()  # the app reads with a new session on every request
        assert self.row(db, edition, bottle, clock, "Alfa").state == "delivered_without_entitlement"

    def test_only_annulled_deliveries_and_no_entitlement_leaves_the_list(
        self, db, edition, bottle, people, boss, clock
    ):
        delivery, _ = service.deliver(
            db, boss, edition, people["c"][0].id, bottle.id, None, clock()
        )
        service.annul(db, boss, edition, delivery.id, "Errore", clock())
        people["c"][1].category = "ordinary"
        db.commit()
        assert self.row(db, edition, bottle, clock, "Charlie") is None

    def test_the_delivery_outlives_the_booking(self, db, edition, bottle, people, boss, clock):
        self.deliver_to_c(db, edition, bottle, people, boss, clock)
        booking = people["c"][1]
        booking.slots = []
        db.delete(booking)
        db.commit()
        row = self.row(db, edition, bottle, clock, "Charlie")
        assert row.state == "delivered_without_entitlement"
        assert row.booking_id is None


def test_the_catalogue_counts_and_hides_retired_benefits_without_deliveries(
    db, edition, bottle, people, boss, clock
):
    spare = Benefit(edition_id=edition.id, name_it="Spilla", name_en="Pin", retired=True)
    db.add(spare)
    db.commit()
    service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    items = service.catalogue(db, edition, clock())
    assert [(i["benefit"].name_it, i["delivered"], i["entitled"]) for i in items] == [
        ("Borraccia", 1, 3)
    ]
    delivery = db.scalar(select(BenefitDelivery))
    spare_delivery = BenefitDelivery(
        edition_id=edition.id,
        participant_id=people["a"][0].id,
        benefit_id=spare.id,
        delivered_at=clock(),
        delivered_by_id=boss.id,
    )
    db.add(spare_delivery)
    db.commit()
    assert delivery
    assert [i["benefit"].name_it for i in service.catalogue(db, edition, clock())] == [
        "Borraccia",
        "Spilla",
    ]


def test_queries_do_not_grow_with_the_people(db, edition, bottle, people, boss, clock):
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    statements: list[str] = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", record)
    try:
        service.rows_for(db, edition, bottle, clock())
    finally:
        event.remove(Engine, "before_cursor_execute", record)
    assert len(statements) <= 6


def test_a_retired_benefit_stays_in_the_catalogue_with_only_annulled_deliveries(
    db, edition, bottle, people, boss, clock
):
    delivery, _ = service.deliver(db, boss, edition, people["a"][0].id, bottle.id, None, clock())
    service.annul(db, boss, edition, delivery.id, "Errore", clock())
    bottle.retired = True
    db.commit()
    items = service.catalogue(db, edition, clock())
    assert [(i["benefit"].name_it, i["delivered"]) for i in items] == [("Borraccia", 0)]


def test_all_annulled_deliveries_are_listed_once_the_person_has_an_active_one(
    db, edition, bottle, people, boss, clock
):
    person = people["c"][0]
    first, _ = service.deliver(db, boss, edition, person.id, bottle.id, None, clock())
    service.annul(db, boss, edition, first.id, "Errore", clock())
    service.deliver(db, boss, edition, person.id, bottle.id, None, clock())
    people["c"][1].category = "ordinary"
    db.commit()
    row = next(
        r for r in service.rows_for(db, edition, bottle, clock()) if r.last_name == "Charlie"
    )
    assert row.state == "delivered_without_entitlement"
    assert len(row.annulled) == 1
