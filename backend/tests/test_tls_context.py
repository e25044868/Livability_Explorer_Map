import ssl

from app.sources.downloader import system_trust_context


def test_system_trust_context_keeps_certificate_verification_enabled() -> None:
    context = system_trust_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
