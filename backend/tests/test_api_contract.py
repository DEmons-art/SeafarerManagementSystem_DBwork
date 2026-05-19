from datetime import UTC, datetime, timedelta
from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import create_app


class MvpApiContractTests(TestCase):
    def setUp(self):
        self.app = create_app(
            database_url="sqlite:///:memory:",
            create_tables=True,
            seed_demo=True,
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.state.engine.dispose()

    def login(self, username="manager", password="manager123") -> str:
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]["access_token"]

    def auth(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def create_crew(self, token: str, username="crew01") -> dict:
        id_suffix = sum(ord(char) for char in username) % 10000
        response = self.client.post(
            "/api/crews",
            headers=self.auth(token),
            json={
                "username": username,
                "password": "123456",
                "name": "张三",
                "gender": "男",
                "id_card": f"11010119900101{id_suffix:04d}",
                "phone": "13800000001",
                "position": "水手",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]

    def add_certificate(
        self,
        token: str,
        crew_id: int,
        certificate_type="STCW",
        expires_in_days=120,
    ) -> dict:
        response = self.client.post(
            "/api/certificates",
            headers=self.auth(token),
            json={
                "crew_id": crew_id,
                "certificate_type": certificate_type,
                "certificate_no": f"{certificate_type}-{crew_id}-{expires_in_days}",
                "issued_at": "2026-01-01",
                "expires_at": (
                    datetime.now(UTC).date() + timedelta(days=expires_in_days)
                ).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]

    def create_job(self, token: str, required_certificates=None) -> dict:
        required_certificates = required_certificates or ["STCW"]
        response = self.client.post(
            "/api/jobs",
            headers=self.auth(token),
            json={
                "title": "远洋水手",
                "ship_name": "东方一号",
                "route": "青岛-新加坡",
                "required_position": "水手",
                "required_certificates": required_certificates,
                "headcount": 1,
                "onboard_at": "2026-06-01T08:00:00",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]

    def test_login_returns_jwt_identity_and_rejects_bad_password(self):
        response = self.client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "manager123"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["token_type"], "bearer")
        self.assertGreater(len(body["data"]["access_token"].split(".")), 2)
        self.assertEqual(body["data"]["user"]["role"], "manager")
        self.assertIn("charset=utf-8", response.headers["content-type"].lower())

        bad_response = self.client.post(
            "/api/auth/login",
            json={"username": "manager", "password": "wrong"},
        )
        self.assertEqual(bad_response.status_code, 401)
        self.assertFalse(bad_response.json()["success"])

    def test_token_and_role_permissions_are_enforced(self):
        response = self.client.get("/api/crews")
        self.assertEqual(response.status_code, 401)

        owner_token = self.login("owner", "owner123")
        forbidden = self.client.post(
            "/api/crews",
            headers=self.auth(owner_token),
            json={
                "username": "crew02",
                "password": "123456",
                "name": "李四",
                "gender": "男",
                "id_card": "110101199001019999",
                "position": "水手",
            },
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_crew_crud_uses_soft_delete(self):
        manager_token = self.login()
        crew = self.create_crew(manager_token)

        update_response = self.client.put(
            f"/api/crews/{crew['id']}",
            headers=self.auth(manager_token),
            json={"phone": "13900000002", "position": "机工"},
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["data"]["position"], "机工")

        delete_response = self.client.delete(
            f"/api/crews/{crew['id']}",
            headers=self.auth(manager_token),
        )
        self.assertEqual(delete_response.status_code, 200)

        detail = self.client.get(
            f"/api/crews/{crew['id']}",
            headers=self.auth(manager_token),
        ).json()["data"]
        self.assertEqual(detail["status"], "inactive")

    def test_certificate_alerts_return_expiring_certificates(self):
        manager_token = self.login()
        cert_token = self.login("cert_admin", "cert123")
        crew = self.create_crew(manager_token)

        self.add_certificate(cert_token, crew["id"], "STCW", expires_in_days=15)
        self.add_certificate(cert_token, crew["id"], "GMDSS", expires_in_days=120)

        response = self.client.get(
            "/api/certificates/alerts",
            headers=self.auth(cert_token),
        )

        self.assertEqual(response.status_code, 200)
        alerts = response.json()["data"]
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["certificate_type"], "STCW")
        self.assertTrue(alerts[0]["is_expiring_soon"])

    def test_job_matching_requires_available_crew_and_valid_certificates(self):
        manager_token = self.login()
        cert_token = self.login("cert_admin", "cert123")
        owner_token = self.login("owner", "owner123")
        eligible = self.create_crew(manager_token, username="eligible")
        expired = self.create_crew(manager_token, username="expired")
        missing = self.create_crew(manager_token, username="missing")

        self.add_certificate(cert_token, eligible["id"], "STCW", expires_in_days=120)
        self.add_certificate(cert_token, expired["id"], "STCW", expires_in_days=-1)
        self.add_certificate(cert_token, missing["id"], "GMDSS", expires_in_days=120)
        job = self.create_job(owner_token, required_certificates=["STCW"])

        response = self.client.get(
            f"/api/jobs/{job['id']}/matches",
            headers=self.auth(manager_token),
        )

        self.assertEqual(response.status_code, 200)
        matches = response.json()["data"]
        self.assertEqual([item["id"] for item in matches], [eligible["id"]])

    def test_dispatch_flow_updates_crew_job_and_voyage_state(self):
        manager_token = self.login()
        cert_token = self.login("cert_admin", "cert123")
        owner_token = self.login("owner", "owner123")
        crew = self.create_crew(manager_token)
        self.add_certificate(cert_token, crew["id"], "STCW", expires_in_days=120)
        job = self.create_job(owner_token, required_certificates=["STCW"])

        dispatch_response = self.client.post(
            "/api/dispatches",
            headers=self.auth(manager_token),
            json={"job_id": job["id"], "crew_id": crew["id"]},
        )
        self.assertEqual(dispatch_response.status_code, 200, dispatch_response.text)
        dispatch = dispatch_response.json()["data"]
        self.assertEqual(dispatch["status"], "pending_owner")

        confirm_response = self.client.put(
            f"/api/dispatches/{dispatch['id']}/confirm",
            headers=self.auth(owner_token),
        )
        self.assertEqual(confirm_response.status_code, 200)
        self.assertEqual(confirm_response.json()["data"]["status"], "confirmed")
        crew_after_confirm = self.client.get(
            f"/api/crews/{crew['id']}",
            headers=self.auth(manager_token),
        ).json()["data"]
        self.assertEqual(crew_after_confirm["status"], "pending")

        onboard_response = self.client.put(
            f"/api/dispatches/{dispatch['id']}/onboard",
            headers=self.auth(manager_token),
        )
        self.assertEqual(onboard_response.status_code, 200)
        self.assertEqual(onboard_response.json()["data"]["status"], "onboard")
        crew_after_onboard = self.client.get(
            f"/api/crews/{crew['id']}",
            headers=self.auth(manager_token),
        ).json()["data"]
        self.assertEqual(crew_after_onboard["status"], "at_sea")

        offboard_response = self.client.put(
            f"/api/dispatches/{dispatch['id']}/offboard",
            headers=self.auth(manager_token),
        )
        self.assertEqual(offboard_response.status_code, 200)
        self.assertEqual(offboard_response.json()["data"]["status"], "offboard")
        crew_after_offboard = self.client.get(
            f"/api/crews/{crew['id']}",
            headers=self.auth(manager_token),
        ).json()["data"]
        self.assertEqual(crew_after_offboard["status"], "available")

    def test_dispatch_rejects_duplicate_expired_certificate_and_wrong_owner(self):
        manager_token = self.login()
        cert_token = self.login("cert_admin", "cert123")
        owner_token = self.login("owner", "owner123")
        other_owner_token = self.login("other_owner", "owner123")
        crew = self.create_crew(manager_token)
        self.add_certificate(cert_token, crew["id"], "STCW", expires_in_days=-1)
        job = self.create_job(owner_token, required_certificates=["STCW"])

        expired_response = self.client.post(
            "/api/dispatches",
            headers=self.auth(manager_token),
            json={"job_id": job["id"], "crew_id": crew["id"]},
        )
        self.assertEqual(expired_response.status_code, 400)

        self.add_certificate(cert_token, crew["id"], "STCW", expires_in_days=120)
        dispatch = self.client.post(
            "/api/dispatches",
            headers=self.auth(manager_token),
            json={"job_id": job["id"], "crew_id": crew["id"]},
        ).json()["data"]
        duplicate_response = self.client.post(
            "/api/dispatches",
            headers=self.auth(manager_token),
            json={"job_id": job["id"], "crew_id": crew["id"]},
        )
        self.assertEqual(duplicate_response.status_code, 400)

        wrong_owner_response = self.client.put(
            f"/api/dispatches/{dispatch['id']}/confirm",
            headers=self.auth(other_owner_token),
        )
        self.assertEqual(wrong_owner_response.status_code, 403)
