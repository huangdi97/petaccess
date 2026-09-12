"""S3-compatible storage provider abstraction (design #29, PROVIDER_HARDENING_SPEC).

MinIO for local dev; the same interface fits any S3 endpoint. Objects are
addressed by random UUID keys (no user-controlled path components → no path
traversal). Protected access via presigned URLs only — evidence media is never
public (NEXT_GOAL §9).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from app.core.config import get_settings


@runtime_checkable
class StorageProvider(Protocol):
    def ensure_bucket(self, bucket: str) -> None: ...
    def put_object(
        self, key: str, data: bytes, content_type: str, bucket: str | None = None
    ) -> dict[str, Any]: ...
    def presigned_get_url(
        self, key: str, bucket: str | None = None, expires_seconds: int = 900
    ) -> str: ...
    def remove_object(self, key: str, bucket: str | None = None) -> None: ...
    def stat_object(self, key: str, bucket: str | None = None) -> dict[str, Any] | None: ...
    def healthy(self) -> bool: ...


class MinioStorageProvider:
    """Real S3-compatible provider backed by the local MinIO (or any S3)."""

    def __init__(self) -> None:
        from minio import Minio

        s = get_settings()
        self._bucket_default = s.s3_bucket
        self._client = Minio(
            s.s3_endpoint.replace("http://", "").replace("https://", ""),
            access_key=s.s3_access_key,
            secret_key=s.s3_secret_key,
            secure=s.s3_secure,
        )

    def ensure_bucket(self, bucket: str) -> None:
        from minio.error import S3Error

        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
        except S3Error:
            raise

    def put_object(
        self, key: str, data: bytes, content_type: str, bucket: str | None = None
    ) -> dict[str, Any]:
        import io

        b = bucket or self._bucket_default
        self.ensure_bucket(b)
        self._client.put_object(
            b,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return {"bucket": b, "key": key, "size": len(data)}

    def presigned_get_url(
        self, key: str, bucket: str | None = None, expires_seconds: int = 900
    ) -> str:
        from datetime import timedelta as _td

        b = bucket or self._bucket_default
        return self._client.presigned_get_object(
            b,
            key,
            expires=_td(seconds=expires_seconds),
            response_headers={"response-content-disposition": "inline"},
        )

    def remove_object(self, key: str, bucket: str | None = None) -> None:
        self._client.remove_object(bucket or self._bucket_default, key)

    def stat_object(self, key: str, bucket: str | None = None) -> dict[str, Any] | None:
        from minio.error import S3Error

        try:
            st = self._client.stat_object(bucket or self._bucket_default, key)
        except S3Error:
            return None
        return {
            "size": st.size,
            "etag": st.etag,
            "content_type": st.content_type,
            "last_modified": st.last_modified.isoformat() if st.last_modified else None,
        }

    def healthy(self) -> bool:
        try:
            b = self._bucket_default
            self.ensure_bucket(b)
            self._client.list_objects(b, recursive=True)
            return True
        except Exception:
            return False


class NullStorageProvider:
    """In-memory provider for unit tests / environments without MinIO."""

    def __init__(self) -> None:
        self._objects: dict[str, tuple[bytes, str]] = {}

    def ensure_bucket(self, bucket: str) -> None:
        return None

    def put_object(
        self, key: str, data: bytes, content_type: str, bucket: str | None = None
    ) -> dict[str, Any]:
        self._objects[key] = (data, content_type)
        return {"bucket": bucket or "null", "key": key, "size": len(data)}

    def presigned_get_url(
        self, key: str, bucket: str | None = None, expires_seconds: int = 900
    ) -> str:
        return f"nullstorage://{key}"

    def remove_object(self, key: str, bucket: str | None = None) -> None:
        self._objects.pop(key, None)

    def stat_object(self, key: str, bucket: str | None = None) -> dict[str, Any] | None:
        if key not in self._objects:
            return None
        data, ctype = self._objects[key]
        return {"size": len(data), "etag": None, "content_type": ctype, "last_modified": None}

    def healthy(self) -> bool:
        return True
