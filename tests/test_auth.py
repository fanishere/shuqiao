import os
import shutil
import subprocess
import time
import unittest

import jwt
from fastapi.testclient import TestClient

CONTAINER = "shuqiao-test-pg"
PORT = 5441

docker = shutil.which("docker")


def _pg_ready() -> bool:
    result = subprocess.run(
        ["docker", "exec", CONTAINER, "pg_isready", "-U", "shuqiao", "-d", "shuqiao"],
        capture_output=True,
    )
    return result.returncode == 0


def _start_postgres() -> None:
    subprocess.run(
        [
            "docker", "run", "-d", "--rm",
            "--name", CONTAINER,
            "-e", "POSTGRES_USER=shuqiao",
            "-e", "POSTGRES_PASSWORD=shuqiao-test",
            "-e", "POSTGRES_DB=shuqiao",
            "-p", f"{PORT}:5432",
            "postgres:18",
        ],
        check=True,
        capture_output=True,
    )
    try:
        for _ in range(30):
            if _pg_ready():
                break
            time.sleep(1)
        else:
            raise RuntimeError("test postgres never became ready")
        os.environ["DATABASE_URL"] = (
            f"postgresql://shuqiao:shuqiao-test@localhost:{PORT}/shuqiao"
        )
        from app import auth
        auth.init_pool()
    except Exception:
        subprocess.run(["docker", "stop", CONTAINER], capture_output=True)
        raise


def _stop_postgres() -> None:
    from app import auth
    auth.close_pool()
    subprocess.run(["docker", "stop", CONTAINER], capture_output=True)


def setUpModule() -> None:
    if docker is not None:
        _start_postgres()


def tearDownModule() -> None:
    if docker is not None:
        _stop_postgres()


@unittest.skipIf(docker is None, "docker not available")
class AuthTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from app import auth
        from app.main import app
        cls.auth = auth
        cls.client = TestClient(app)

    def setUp(self) -> None:
        with self.auth.db() as conn:
            conn.execute("DELETE FROM refresh_tokens")
            conn.execute("DELETE FROM users")

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

    def refresh(self, token: str):
        return self.client.post("/auth/refresh", json={"refresh_token": token})


class SignupTest(AuthTestCase):
    def test_signup_stores_hashed_password(self) -> None:
        self.signup()
        with self.auth.db() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE username = %s", ("fan",)
            ).fetchone()
        self.assertIsNotNone(row)
        self.assertTrue(self.auth.password_hash.verify("correct horse", row[0]))

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
        claims = jwt.decode(
            body["access_token"], self.auth.SECRET_KEY, algorithms=["HS256"]
        )
        self.assertEqual(claims["sub"], "fan")
        with self.auth.db() as conn:
            n = conn.execute("SELECT count(*) FROM refresh_tokens").fetchone()[0]
        self.assertEqual(n, 1)

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
    def test_refresh_rotates_refresh_token(self) -> None:
        self.signup()
        old = self.login()["refresh_token"]
        response = self.refresh(old)
        self.assertEqual(response.status_code, 200)
        new = response.json()["refresh_token"]
        self.assertNotEqual(new, old)
        self.assertEqual(self.refresh(old).status_code, 401)
        self.assertEqual(self.refresh(new).status_code, 200)

    def test_refresh_token_stored_as_hash_not_plaintext(self) -> None:
        self.signup()
        token = self.login()["refresh_token"]
        with self.auth.db() as conn:
            rows = [r[0] for r in conn.execute("SELECT token_hash FROM refresh_tokens")]
        self.assertEqual(rows, [self.auth._token_hash(token)])

    def test_expired_refresh_token_rejected(self) -> None:
        self.signup()
        token = self.login()["refresh_token"]
        with self.auth.db() as conn:
            conn.execute(
                "UPDATE refresh_tokens SET expires_at = now() - interval '1 second'"
            )
        self.assertEqual(self.refresh(token).status_code, 401)

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
        self.assertEqual(self.refresh(tokens["refresh_token"]).status_code, 401)


class PersistenceTest(AuthTestCase):
    def test_tokens_survive_pool_restart(self) -> None:
        self.signup()
        tokens = self.login()
        self.auth.close_pool()
        self.auth.init_pool()
        self.assertEqual(self.refresh(tokens["refresh_token"]).status_code, 200)


if __name__ == "__main__":
    unittest.main()
