"""Unit tests for the M1 secret scanner (scripts/scan_secrets.py, A7)."""

from __future__ import annotations

from scan_secrets import is_dev_line, scan_text


def test_is_dev_line_marks_demo_values() -> None:
    assert is_dev_line("JWT_SECRET=dev_only_change_me_32_bytes_1234567890")
    assert is_dev_line("DATABASE_URL=postgresql://petaccess:petaccess_dev_only@localhost:5432/x")


def test_is_dev_line_keeps_real_values() -> None:
    assert not is_dev_line("SK=f5f3c9d2a1b4e7f8a0c3d5e6b7f1a2b3c4d5e6f7a")
    assert not is_dev_line("export JWT_SECRET=0123456789abcdef0123456789abcdef")


def test_scan_text_finds_high_signal_even_with_dev_marker() -> None:
    # AWS access key must be reported even if another part of the line looks
    # like a dev value: a dev label must never hide a real high-signal key.
    hits = scan_text('aws = "AKIAIOSFODNN7EXAMPLE" access_key=example')
    assert any(name == "AWS access key" for name, _ in hits)


def test_scan_text_finds_github_token() -> None:
    hits = scan_text('token="ghp_012345678901234567890123456789ABCDEF"')
    assert any(name == "GitHub token" for name, _ in hits)


def test_scan_text_finds_private_key_block() -> None:
    hits = scan_text("-----BEGIN RSA PRIVATE KEY-----\nMIICWwIBAA")
    assert any(name == "private key block" for name, _ in hits)


def test_scan_text_skips_dev_generic_secret() -> None:
    hits = scan_text('api_key = "dev_only_value_for_tests"')
    assert hits == []


def test_scan_text_finds_real_generic_secret() -> None:
    hits = scan_text('password = "s3cr3t-password-1234567890"')
    assert any(name == "generic secret assignment" for name, _ in hits)


def test_scan_text_finds_db_url_credentials() -> None:
    hits = scan_text(
        'url = "postgresql://petaccess:REALPASSWORD-1234567890@127.0.0.1:5432/petaccess"'
    )
    assert any(name == "DB URL with credentials" for name, _ in hits)
