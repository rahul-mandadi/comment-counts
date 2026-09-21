import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import run_bedrock


class _TooLongThenOk:
    """Rejects anything over `limit` chars, the way Titan rejects over 8,192
    tokens. A fixed chars-per-token constant killed a real run."""
    def __init__(self, limit):
        self.limit, self.calls = limit, 0

    def invoke_model(self, modelId, body):
        import json, io
        self.calls += 1
        text = json.loads(body)["inputText"]
        if len(text) > self.limit:
            raise RuntimeError("400 Bad Request: Too many input tokens. Max input tokens: 8192")
        return {"body": io.BytesIO(json.dumps({"embedding": [1.0, 0.0]}).encode())}


def test_it_shrinks_until_the_document_fits():
    c = _TooLongThenOk(limit=1000)
    v = run_bedrock.embed_one("x" * 40000, client=c)
    assert v.shape == (2,) and c.calls > 1


def test_a_document_that_fits_costs_one_call():
    c = _TooLongThenOk(limit=10 ** 9)
    run_bedrock.embed_one("short text", client=c)
    assert c.calls == 1


def test_empty_text_does_not_send_an_empty_string():
    import json
    seen = {}

    class Rec(_TooLongThenOk):
        def invoke_model(self, modelId, body):
            seen["t"] = json.loads(body)["inputText"]
            return super().invoke_model(modelId, body)

    run_bedrock.embed_one("", client=Rec(10 ** 9))
    assert seen["t"] != ""
