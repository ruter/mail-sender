"""Tests for MailSender.send_email() handling of partial recipient refusal."""

import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Mock db module before importing mail_sender to avoid DB initialization
sys.modules['db'] = MagicMock()
sys.modules['db.database'] = MagicMock()
sys.modules['db.database'].db = MagicMock()

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mail_assistant"))

from services.mail_sender import MailSender, SMTPConfig


class FakeSMTP:
    """Fake SMTP connection that records sendmail() calls and returns configured refusals."""

    instances = []

    def __init__(self, server, port, timeout):
        self.server = server
        self.port = port
        self.timeout = timeout
        self.sent = []
        self.login_args = None
        FakeSMTP.instances.append(self)

    def ehlo(self):
        return 250, b"OK"

    def starttls(self):
        return 220, b"Ready"

    def login(self, sender_email, password):
        self.login_args = (sender_email, password)

    def sendmail(self, from_addr, to_addrs, message):
        self.sent.append((from_addr, to_addrs, message))
        return self.__class__.refused

    def quit(self):
        self.quit_called = True


CONFIG = SMTPConfig("smtp.example.com", 465, "sender@example.com", "password")


class TestSendEmailPartialRefusal(unittest.TestCase):
    """Verify that partial SMTP refusal (some recipients rejected) is detected and reported."""

    def setUp(self):
        FakeSMTP.instances = []
        FakeSMTP.refused = {}

    def _send(self, to_email, cc_emails):
        with patch("services.mail_sender.smtplib.SMTP_SSL", FakeSMTP):
            return MailSender.send_email(
                to_email=to_email,
                cc_emails=cc_emails,
                subject="Test",
                body="Body",
                attachment_path="/tmp/nonexistent.xlsx",
                config=CONFIG,
            )

    def test_all_accepted_returns_success(self):
        """When SMTP server accepts all recipients, send_email returns (True, None)."""
        FakeSMTP.refused = {}
        success, error = self._send("to@example.com", ["cc@example.com"])
        self.assertTrue(success)
        self.assertIsNone(error)

    def test_partial_refusal_returns_failure_with_details(self):
        """When SMTP server rejects CC but accepts To, send_email returns failure with refused addresses."""
        FakeSMTP.refused = {"cc@example.com": (550, b"Rejected")}
        success, error = self._send("to@example.com", ["cc@example.com"])
        self.assertFalse(success)
        self.assertIn("cc@example.com", error)

    def test_to_recipient_refused_returns_failure(self):
        """When SMTP server rejects the To recipient, send_email returns failure."""
        FakeSMTP.refused = {"to@example.com": (550, b"Rejected")}
        success, error = self._send("to@example.com", ["cc@example.com"])
        self.assertFalse(success)
        self.assertIn("to@example.com", error)

    def test_multiple_cc_some_refused(self):
        """When some CC recipients are refused, all refused addresses appear in the error."""
        FakeSMTP.refused = {"cc2@example.com": (550, b"Rejected")}
        success, error = self._send("to@example.com", ["cc1@example.com", "cc2@example.com"])
        self.assertFalse(success)
        self.assertIn("cc2@example.com", error)
        self.assertNotIn("cc1@example.com", error)

    def test_partial_refusal_retries_and_fails_after_max_attempts(self):
        """When CC is refused on all attempts, send_email retries and returns failure."""
        FakeSMTP.refused = {"cc@example.com": (550, b"Rejected")}
        with patch("services.mail_sender.smtplib.SMTP_SSL", FakeSMTP):
            with patch("services.mail_sender.time.sleep") as mock_sleep:
                success, error = MailSender.send_email(
                    to_email="to@example.com",
                    cc_emails=["cc@example.com"],
                    subject="Subject",
                    body="Body",
                    attachment_path="/tmp/missing.xlsx",
                    config=CONFIG,
                    max_retries=2,
                )

        self.assertFalse(success)
        self.assertIn("cc@example.com", error)
        # 2 retries = 2 sleeps (attempt 0 and 1 both sleep before retrying)
        self.assertEqual(mock_sleep.call_count, 2)
        # 3 total send attempts (initial + 2 retries)
        self.assertEqual(len(FakeSMTP.instances), 3)

    def test_retry_only_sends_to_refused_recipients(self):
        """On retry, envelope recipients shrink to only the previously refused addresses."""
        attempt_count = 0

        class ConditionalFakeSMTP(FakeSMTP):
            def sendmail(self_inner, from_addr, to_addrs, message):
                nonlocal attempt_count
                attempt_count += 1
                self_inner.sent.append((from_addr, list(to_addrs), message))
                if attempt_count == 1:
                    # First attempt: To accepted, CC refused
                    return {"cc@example.com": (550, b"Rejected")}
                # Second attempt: CC accepted
                return {}

        FakeSMTP.instances = []
        with patch("services.mail_sender.smtplib.SMTP_SSL", ConditionalFakeSMTP):
            with patch("services.mail_sender.time.sleep"):
                success, error = MailSender.send_email(
                    to_email="to@example.com",
                    cc_emails=["cc@example.com"],
                    subject="Subject",
                    body="Body",
                    attachment_path="/tmp/missing.xlsx",
                    config=CONFIG,
                    max_retries=2,
                )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(len(FakeSMTP.instances), 2)
        # First attempt: full recipient list
        self.assertEqual(
            FakeSMTP.instances[0].sent[0][1],
            ["to@example.com", "cc@example.com"]
        )
        # Second attempt: only the refused recipient
        self.assertEqual(
            FakeSMTP.instances[1].sent[0][1],
            ["cc@example.com"]
        )

    def test_partial_refusal_succeeds_on_retry(self):
        """When CC is refused on first attempt but accepted on retry, send_email returns success."""
        attempt_count = 0

        class ConditionalFakeSMTP(FakeSMTP):
            def sendmail(self_inner, from_addr, to_addrs, message):
                nonlocal attempt_count
                attempt_count += 1
                self_inner.sent.append((from_addr, list(to_addrs), message))
                if attempt_count == 1:
                    return {"cc@example.com": (550, b"Rejected")}
                return {}

        FakeSMTP.instances = []
        with patch("services.mail_sender.smtplib.SMTP_SSL", ConditionalFakeSMTP):
            with patch("services.mail_sender.time.sleep"):
                success, error = MailSender.send_email(
                    to_email="to@example.com",
                    cc_emails=["cc@example.com"],
                    subject="Subject",
                    body="Body",
                    attachment_path="/tmp/missing.xlsx",
                    config=CONFIG,
                    max_retries=2,
                )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(len(FakeSMTP.instances), 2)
        # First attempt: full list
        self.assertEqual(
            FakeSMTP.instances[0].sent[0][1],
            ["to@example.com", "cc@example.com"]
        )
        # Second attempt: only the refused CC
        self.assertEqual(
            FakeSMTP.instances[1].sent[0][1],
            ["cc@example.com"]
        )

    def test_envelope_recipients_include_cc(self):
        """Verify that the SMTP envelope recipient list includes both To and CC addresses."""
        FakeSMTP.refused = {}
        self._send("to@example.com", ["cc1@example.com", "cc2@example.com"])
        envelope_recipients = FakeSMTP.instances[0].sent[0][1]
        self.assertEqual(envelope_recipients, ["to@example.com", "cc1@example.com", "cc2@example.com"])

    def test_message_cc_header_present(self):
        """Verify that the MIME message has the Cc header set."""
        FakeSMTP.refused = {}
        self._send("to@example.com", ["cc1@example.com", "cc2@example.com"])
        raw_message = FakeSMTP.instances[0].sent[0][2]
        self.assertIn("Cc: cc1@example.com, cc2@example.com", raw_message)

    def test_message_has_message_id_header(self):
        """Verify that the MIME message includes a Message-ID header."""
        FakeSMTP.refused = {}
        self._send("to@example.com", ["cc@example.com"])
        raw_message = FakeSMTP.instances[0].sent[0][2]
        self.assertIn("Message-ID:", raw_message)

    def test_message_has_date_header(self):
        """Verify that the MIME message includes a Date header."""
        FakeSMTP.refused = {}
        self._send("to@example.com", ["cc@example.com"])
        raw_message = FakeSMTP.instances[0].sent[0][2]
        self.assertIn("Date:", raw_message)


class TestNormalizedCcEmails(unittest.TestCase):
    """Verify CC email normalization handles edge cases."""

    def setUp(self):
        FakeSMTP.instances = []
        FakeSMTP.refused = {}

    def _send(self, cc_emails):
        with patch("services.mail_sender.smtplib.SMTP_SSL", FakeSMTP):
            return MailSender.send_email(
                to_email="to@example.com",
                cc_emails=cc_emails,
                subject="Test",
                body="Body",
                attachment_path="/tmp/nonexistent.xlsx",
                config=CONFIG,
            )

    def test_comma_separated_cc_split(self):
        """CC strings containing commas are split into individual addresses."""
        self._send(["a@example.com, b@example.com"])
        envelope = FakeSMTP.instances[0].sent[0][1]
        self.assertEqual(envelope, ["to@example.com", "a@example.com", "b@example.com"])

    def test_empty_cc_skipped(self):
        """Empty CC entries are filtered out."""
        self._send(["", "  ", "cc@example.com"])
        envelope = FakeSMTP.instances[0].sent[0][1]
        self.assertEqual(envelope, ["to@example.com", "cc@example.com"])


if __name__ == "__main__":
    unittest.main()
