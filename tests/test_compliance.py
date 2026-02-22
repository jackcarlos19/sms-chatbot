from types import SimpleNamespace

from app.core.compliance import handle_compliance, is_compliance_keyword


def test_is_compliance_keyword_opt_out() -> None:
    assert is_compliance_keyword(" stop ") == (True, "opt_out")
    assert is_compliance_keyword("UNSUBSCRIBE") == (True, "opt_out")


def test_is_compliance_keyword_opt_in() -> None:
    assert is_compliance_keyword("start") == (True, "opt_in")
    assert is_compliance_keyword("YES") == (True, "opt_in")


def test_is_compliance_keyword_help() -> None:
    assert is_compliance_keyword("help") == (True, "help")
    assert is_compliance_keyword("INFO") == (True, "help")


def test_handle_stop_message_and_contact_update() -> None:
    contact = SimpleNamespace(opt_in_status="opted_in", opt_in_date=None, opt_out_date=None)
    response = handle_compliance(
        contact=contact,
        keyword_type="opt_out",
        business_name="Acme Services",
        support_number="+15551234567",
    )
    assert contact.opt_in_status == "opted_out"
    assert contact.opt_out_date is not None
    assert (
        response
        == "You have been unsubscribed and will not receive further messages. Reply START to re-subscribe."
    )


def test_handle_start_message_and_contact_update() -> None:
    contact = SimpleNamespace(opt_in_status="opted_out", opt_in_date=None, opt_out_date=None)
    response = handle_compliance(
        contact=contact,
        keyword_type="opt_in",
        business_name="Acme Services",
        support_number="+15551234567",
    )
    assert contact.opt_in_status == "opted_in"
    assert contact.opt_in_date is not None
    assert response == "You have been re-subscribed to Acme Services messages. Reply STOP to unsubscribe."


def test_handle_help_message() -> None:
    contact = SimpleNamespace(opt_in_status="opted_in", opt_in_date=None, opt_out_date=None)
    response = handle_compliance(
        contact=contact,
        keyword_type="help",
        business_name="Acme Services",
        support_number="+15551234567",
    )
    assert (
        response
        == "Acme Services: For support call +15551234567. Msg frequency varies. Msg&data rates may apply. Reply STOP to cancel."
    )
