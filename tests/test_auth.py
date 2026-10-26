import unittest
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app import auth
from app.main import app


class AuthTestCase(unittest.TestCase):
    def setUp(self) -> None:
        auth.users.clear()
        auth.refresh_tokens.clear()
        self.client = TestClient(app)

    def signup(self, username: str = "fan", password: str = "correct horse") -> dict:
        response = self.client.post(
            "/auth/signup", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, username: str = "fan", password: str = "correct horse") -> dict:
        response = self.client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()


class SignupTest(AuthTestCase):
    def test_signup_stores_hashed_password(self) -> None:
        self.signup()
        self.assertIn("fan", auth.users)
        self.assertNotIn("correct horse", auth.users.values())
        self.assertTrue(auth.password_hash.verify("correct horse", auth.users["fan"]))

    def test_duplicate_signup_rejected(self) -> None:
        self.signup()
        response = self.client.post(
            "/auth/signup", json={"username": "fan", "password": "other"}
        )
        self.assertEqual(response.status_code, 409)

    def test_empty_username_or_password_rejected(self) -> None:
        for body in (
            {"username": "", "password": "correct horse"},
            {"username": "fan", "password": ""},
        ):
            response = self.client.post("/auth/signup", json=body)
            self.assertEqual(response.status_code, 422, body)


class LoginTest(AuthTestCase):
    def test_login_returns_tokens(self) -> None:
        self.signup()
        body = self.login()
        self.assertEqual(body["token_type"], "bearer")
        self.assertIn(body["refresh_token"], auth.refresh_tokens)
        claims = jwt.decode(
            body["access_token"], auth.SECRET_KEY, algorithms=["HS256"]
        )
        self.assertEqual(claims["sub"], "fan")

    def test_wrong_password_rejected(self) -> None:
        self.signup()
        response = self.client.post(
            "/auth/login", json={"username": "fan", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)

    def test_unknown_username_rejected(self) -> None:
        response = self.client.post(
            "/auth/login", json={"username": "ghost", "password": "whatever"}
        )
        self.assertEqual(response.status_code, 401)


class RefreshTest(AuthTestCase):
    def refresh(self, token: str):
        return self.client.post("/auth/refresh", json={"refresh_token": token})

    def test_refresh_rotates_refresh_token(self) -> None:
        self.signup()
        old = self.login()["refresh_token"]
        response = self.refresh(old)
        self.assertEqual(response.status_code, 200)
        new = response.json()["refresh_token"]
        self.assertNotEqual(new, old)
        self.assertNotIn(old, auth.refresh_tokens)
        self.assertEqual(self.refresh(old).status_code, 401)
        self.assertEqual(self.refresh(new).status_code, 200)

    def test_expired_refresh_token_rejected(self) -> None:
        self.signup()
        token = self.login()["refresh_token"]
        username, _ = auth.refresh_tokens[token]
        auth.refresh_tokens[token] = (
            username,
            datetime.now(timezone.utc)
            - auth.REFRESH_TOKEN_TTL
            - timedelta(seconds=1),
        )
        self.assertEqual(self.refresh(token).status_code, 401)
        self.assertNotIn(token, auth.refresh_tokens)

    def test_unknown_refresh_token_rejected(self) -> None:
        self.assertEqual(self.refresh("no-such-token").status_code, 401)


class LogoutTest(AuthTestCase):
    def test_logout_revokes_refresh_token(self) -> None:
        self.signup()
        tokens = self.login()
        response = self.client.request(
            "POST", "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )
        self.assertEqual(response.status_code, 204)
        revoked = self.client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        self.assertEqual(revoked.status_code, 401)


if __name__ == "__main__":
    unittest.main()
