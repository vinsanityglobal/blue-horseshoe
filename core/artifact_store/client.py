"""
Blue Horseshoe — Artifact Storage Client
Provider-agnostic abstraction for storing large payloads outside Airtable.
Supports: local filesystem (dev/Railway Volumes), S3-compatible (AWS S3, Cloudflare R2).
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ArtifactRef:
    """Reference stored in Airtable pointing to the artifact."""
    artifact_id: str
    artifact_url: str
    checksum_sha256: str
    size_bytes: int
    mime_type: str
    created_at: str


class ArtifactStoreClient:
    def __init__(self):
        s = get_settings()
        self.store_type = s.artifact_store_type
        self.local_path = Path(s.artifact_store_path)

        if self.store_type == "local":
            self.local_path.mkdir(parents=True, exist_ok=True)
        elif self.store_type in ("s3", "r2"):
            self._init_s3(s)

    def _init_s3(self, s):
        try:
            import boto3
            kwargs = {
                "aws_access_key_id": s.artifact_store_key,
                "aws_secret_access_key": s.artifact_store_secret,
            }
            if s.artifact_store_endpoint:
                kwargs["endpoint_url"] = s.artifact_store_endpoint
            self.s3 = boto3.client("s3", **kwargs)
            self.bucket = s.artifact_store_bucket
        except ImportError:
            logger.warning("boto3 not installed. Falling back to local storage.")
            self.store_type = "local"

    def _compute_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _detect_mime(self, content: any) -> str:
        if isinstance(content, (dict, list)):
            return "application/json"
        if isinstance(content, str):
            return "text/plain"
        return "application/octet-stream"

    def save(self, artifact_id: str, content: any, mime_type: str = None) -> ArtifactRef:
        """
        Save content to the artifact store.
        Returns an ArtifactRef to be stored in Airtable.
        """
        if isinstance(content, (dict, list)):
            raw = json.dumps(content, indent=2).encode("utf-8")
            ext = ".json"
        elif isinstance(content, str):
            raw = content.encode("utf-8")
            ext = ".txt"
        else:
            raw = content
            ext = ".bin"

        mime = mime_type or self._detect_mime(content)
        checksum = self._compute_checksum(raw)
        size = len(raw)
        created_at = datetime.utcnow().isoformat() + "Z"

        if self.store_type == "local":
            file_path = self.local_path / f"{artifact_id}{ext}"
            file_path.write_bytes(raw)
            url = str(file_path)
        else:
            key = f"{artifact_id}{ext}"
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=raw,
                ContentType=mime,
            )
            url = f"s3://{self.bucket}/{key}"

        logger.info(f"Artifact saved: {artifact_id} ({size} bytes) → {url}")
        return ArtifactRef(
            artifact_id=artifact_id,
            artifact_url=url,
            checksum_sha256=checksum,
            size_bytes=size,
            mime_type=mime,
            created_at=created_at,
        )

    def load(self, artifact_url: str) -> bytes:
        """Load raw bytes from an artifact URL."""
        if self.store_type == "local" or artifact_url.startswith("/"):
            return Path(artifact_url).read_bytes()
        elif artifact_url.startswith("s3://"):
            parts = artifact_url[5:].split("/", 1)
            bucket, key = parts[0], parts[1]
            resp = self.s3.get_object(Bucket=bucket, Key=key)
            return resp["Body"].read()
        raise ValueError(f"Unknown artifact URL scheme: {artifact_url}")

    def load_json(self, artifact_url: str) -> dict:
        """Load and parse a JSON artifact."""
        return json.loads(self.load(artifact_url).decode("utf-8"))
