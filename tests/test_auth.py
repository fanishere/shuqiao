import unittest

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


class LoginTest(AuthTestCase):
    def test_login_returns_tokens(self) -> None:
        self.signup()
        response = self.client.post(
            "/auth/login", json={"username": "fan", "password": "correct horse"}
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
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


class RefreshTest(AuthTestCase):
    def login(self) -> dict:
        self.signup()
        response = self.client.post(
            "/auth/login", json={"username": "fan", "password": "correct horse"}
        )
        return response.json()

    def test_refresh_issues_new_access_token(self) -> None:
        tokens = self.login()
        response = self.client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        self.assertEqual(response.status_code, 200)
        claims = jwt.decode(
            response.json()["access_token"], auth.SECRET_KEY, algorithms=["HS256"]
        )
        self.assertEqual(claims["sub"], "fan")

    def test_unknown_refresh_token_rejected(self) -> None:
        response = self.client.post(
            "/auth/refresh", json={"refresh_token": "no-such-token"}
        )
        self.assertEqual(response.status_code, 401)


class LogoutTest(AuthTestCase):
    def test_logout_revokes_refresh_token(self) -> None:
        self.signup()
        tokens = self.client.post(
            "/auth/login", json={"username": "fan", "password": "correct horse"}
        ).json()
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
