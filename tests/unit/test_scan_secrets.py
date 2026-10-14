"""Unit tests for the M1 secret scanner (scripts/scan_secrets.py, A7)."""

from __future__ import annotations

from scan_secrets import is_dev_line, is_known_history_template, scan_text


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


def test_scan_text_skips_public_preview_ci_fixture_credentials() -> None:
    hits = scan_text(
        "\n".join(
            [
                "DATABASE_URL=postgresql+psycopg://petaccess:ci_preview_postgres_0123456789abcdef@db:5432/petaccess_preview_ci",
                "S3_SECRET_KEY=ci_preview_storage_0123456789abcdef",
                "JWT_SECRET=ci_preview_jwt_0123456789abcdef0123456789abcdef",
            ]
        )
    )
    assert hits == []


def test_public_preview_ci_marker_never_hides_high_signal_secret() -> None:
    hits = scan_text(
        "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE JWT_SECRET=ci_preview_jwt_0123456789abcdef"
    )
    assert any(name == "AWS access key" for name, _ in hits)


def test_scan_text_finds_real_generic_secret() -> None:
    hits = scan_text('password = "s3cr3t-password-1234567890"')
    assert any(name == "generic secret assignment" for name, _ in hits)


def test_scan_text_finds_db_url_credentials() -> None:
    hits = scan_text(
        'url = "postgresql://petaccess:REALPASSWORD-1234567890@127.0.0.1:5432/petaccess"'
    )
    assert any(name == "DB URL with credentials" for name, _ in hits)

def test_history_exemption_is_narrow_to_removed_dynamic_preview_db_template() -> None:
    template = (
        'DATABASE_URL="postgresql+psycopg://'
        '$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB"'
    )
    assert is_known_history_template(
        ".github/workflows/public-preview-deploy.yml",
        "DB URL with credentials",
        template,
    )
    assert not is_known_history_template(
        ".github/workflows/public-preview-deploy.yml",
        "DB URL with credentials",
        "DATABASE_URL=postgresql://petaccess:REALPASSWORD-1234567890@db:5432/petaccess",
    )
    assert not is_known_history_template(
        "other.yml",
        "DB URL with credentials",
        template,
    )

