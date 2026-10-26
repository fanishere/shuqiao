import unittest

from fastapi.testclient import TestClient

from app.main import app


class HealthTest(unittest.TestCase):
    def test_health_returns_ok(self) -> None:
        client = TestClient(app)
        self.assertEqual(client.get("/health").json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
