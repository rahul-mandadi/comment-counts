"""One interface over local disk and S3, so the pipeline code does not branch.

Phase 1 ran entirely on a laptop and one docket cost 886 MB. Phase 2 is five
more, including ED-2021-OCR-0166 at 68x the record count of the docket already
run, against 20 GB of free disk. So the corpus has to live in object storage
regardless of anything else, and the analysis code should not have to care.

The local backend is not a toy for tests. It is what makes every stage runnable
and debuggable without credentials, which is also what keeps the AWS bill
attached to work that has already been proven to run.
"""
import io
import os
import shutil


class LocalStore:
    def __init__(self, root):
        self.root = os.path.abspath(root)

    def _p(self, key):
        p = os.path.join(self.root, key)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        return p

    def put_bytes(self, key, data):
        with open(self._p(key), "wb") as fh:
            fh.write(data)

    def get_bytes(self, key):
        with open(self._p(key), "rb") as fh:
            return fh.read()

    def exists(self, key):
        return os.path.exists(os.path.join(self.root, key))

    def list(self, prefix=""):
        base = os.path.join(self.root, prefix)
        out = []
        for dirpath, _dirs, files in os.walk(base if os.path.isdir(base) else self.root):
            for f in files:
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, self.root)
                if rel.startswith(prefix):
                    out.append(rel)
        return sorted(out)

    def upload_file(self, path, key):
        shutil.copyfile(path, self._p(key))

    def uri(self, key):
        return "file://" + os.path.join(self.root, key)


class S3Store:
    def __init__(self, bucket, prefix="", client=None):
        import boto3
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.s3 = client or boto3.client("s3")

    def _k(self, key):
        return f"{self.prefix}/{key}" if self.prefix else key

    def put_bytes(self, key, data):
        self.s3.put_object(Bucket=self.bucket, Key=self._k(key), Body=data)

    def get_bytes(self, key):
        return self.s3.get_object(Bucket=self.bucket, Key=self._k(key))["Body"].read()

    def exists(self, key):
        from botocore.exceptions import ClientError
        try:
            self.s3.head_object(Bucket=self.bucket, Key=self._k(key))
            return True
        except ClientError:
            return False

    def list(self, prefix=""):
        token, out = None, []
        while True:
            kw = {"Bucket": self.bucket, "Prefix": self._k(prefix)}
            if token:
                kw["ContinuationToken"] = token
            r = self.s3.list_objects_v2(**kw)
            cut = len(self.prefix) + 1 if self.prefix else 0
            out += [o["Key"][cut:] for o in r.get("Contents", [])]
            token = r.get("NextContinuationToken")
            if not r.get("IsTruncated"):
                return sorted(out)

    def upload_file(self, path, key):
        self.s3.upload_file(path, self.bucket, self._k(key))

    def uri(self, key):
        return f"s3://{self.bucket}/{self._k(key)}"


def from_env(default_local="data"):
    """S3 when COMMENT_COUNTS_BUCKET is set, local otherwise.

    Selection by environment rather than by flag, so the same command runs in
    both places and nothing has to remember which mode it is in.
    """
    bucket = os.environ.get("COMMENT_COUNTS_BUCKET")
    if bucket:
        return S3Store(bucket, os.environ.get("COMMENT_COUNTS_PREFIX", ""))
    return LocalStore(os.environ.get("COMMENT_COUNTS_DATA", default_local))
