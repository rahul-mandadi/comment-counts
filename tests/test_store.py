import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import store


def test_local_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        s = store.LocalStore(d)
        s.put_bytes("a/b.json", b"hello")
        assert s.get_bytes("a/b.json") == b"hello" and s.exists("a/b.json")


def test_local_list_is_prefix_scoped():
    with tempfile.TemporaryDirectory() as d:
        s = store.LocalStore(d)
        s.put_bytes("x/1.json", b"1"); s.put_bytes("x/2.json", b"2"); s.put_bytes("y/3.json", b"3")
        assert s.list("x/") == ["x/1.json", "x/2.json"]


def test_missing_key_is_not_reported_as_present():
    with tempfile.TemporaryDirectory() as d:
        assert not store.LocalStore(d).exists("nope.json")


def test_env_selects_local_when_no_bucket(monkeypatch=None):
    os.environ.pop("COMMENT_COUNTS_BUCKET", None)
    assert isinstance(store.from_env(), store.LocalStore)


def test_env_selects_s3_when_bucket_is_set():
    os.environ["COMMENT_COUNTS_BUCKET"] = "some-bucket"
    try:
        s = store.from_env()
        assert isinstance(s, store.S3Store) and s.bucket == "some-bucket"
    finally:
        os.environ.pop("COMMENT_COUNTS_BUCKET")


def test_s3_uri_and_key_prefixing_without_any_network():
    class FakeS3:
        pass
    s = store.S3Store("b", prefix="proj", client=FakeS3())
    assert s._k("a/b.json") == "proj/a/b.json"
    assert s.uri("a/b.json") == "s3://b/proj/a/b.json"
