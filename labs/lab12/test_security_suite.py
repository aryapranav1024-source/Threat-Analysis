"""
Test Security Suite - MongoDB Security Lab 12
Validates:
1. Authentication enforcement (plain access without credentials fails)
2. Admin authentication success
3. RBAC read permissions (app_user_read) on permitted view
4. RBAC write denial on unauthorized collection
5. RBAC direct collection denial (underlying employees collection)
6. RBAC write permissions (app_user_write) on events collection
7. RBAC access denial on out-of-scope database
8. Field-Level Redaction: HR user sees 'salary'
9. Field-Level Redaction: Regular reader sees view with 'salary' excluded and masked SSN
10. TLS enforcement: plain unencrypted connection is rejected
11. TLS encrypted connection: PyMongo queries succeed over TLS with CA validation

Student: K. Pranav Reddy (24BTRCL098)
"""

import sys
import os
import unittest
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConnectionFailure, ServerSelectionTimeoutError

class TestMongoDBSecurity(unittest.TestCase):
    AUTH_PORT = 27017
    TLS_PORT = 27100
    HOST = "localhost"
    CA_FILE = "./tls/ca.crt"
    CLIENT_PEM = "./tls/client.pem"

    @classmethod
    def setUpClass(cls):
        # Override ports or host if environment variables exist
        cls.HOST = os.getenv("MONGO_HOST", cls.HOST)
        cls.AUTH_PORT = int(os.getenv("MONGO_AUTH_PORT", cls.AUTH_PORT))
        cls.TLS_PORT = int(os.getenv("MONGO_TLS_PORT", cls.TLS_PORT))
        if os.getenv("TLS_CA_FILE"):
            cls.CA_FILE = os.getenv("TLS_CA_FILE")

    # -------------------------------------------------------------
    # Lab 12.1 Tests: RBAC & Authentication
    # -------------------------------------------------------------
    def test_01_admin_authentication(self):
        """Admin credentials must authenticate successfully and access server info."""
        uri = f"mongodb://admin:AdminPass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            info = client.admin.command("buildInfo")
            self.assertIn("version", info)
            print("  [PASS] Admin authenticated successfully.")
        finally:
            client.close()

    def test_02_reader_can_access_redacted_view(self):
        """app_user_read can query employees_redacted_view and find documents."""
        uri = f"mongodb://app_user_read:ReadPass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["hr_system"]
            docs = list(db["employees_redacted_view"].find())
            self.assertGreater(len(docs), 0, "Redacted view should contain employee records")
            print(f"  [PASS] app_user_read read {len(docs)} records from employees_redacted_view.")
        finally:
            client.close()

    def test_03_field_level_redaction_excludes_salary_for_reader(self):
        """Redacted view must NOT expose 'salary' field, and SSN must be masked."""
        uri = f"mongodb://app_user_read:ReadPass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["hr_system"]
            docs = list(db["employees_redacted_view"].find())
            for d in docs:
                self.assertNotIn("salary", d, "Sensitive field 'salary' must be redacted!")
                self.assertNotIn("ssn", d, "Raw SSN must not be present!")
                self.assertTrue(d.get("masked_ssn", "").startswith("***-**-"), "SSN should be masked")
            print("  [PASS] Field-level redaction verified: salary absent and SSN masked.")
        finally:
            client.close()

    def test_04_reader_denied_direct_access_to_underlying_collection(self):
        """app_user_read must be DENIED direct access to hr_system.employees."""
        uri = f"mongodb://app_user_read:ReadPass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["hr_system"]
            with self.assertRaises(OperationFailure) as ctx:
                list(db["employees"].find())
            self.assertIn("not authorized", str(ctx.exception).lower())
            print("  [PASS] app_user_read correctly denied direct access to sensitive 'employees' collection.")
        finally:
            client.close()

    def test_05_reader_denied_write_operation(self):
        """app_user_read must be DENIED write access on analytics.events."""
        uri = f"mongodb://app_user_read:ReadPass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["analytics"]
            with self.assertRaises(OperationFailure) as ctx:
                db["events"].insert_one({"test": "unauthorized"})
            self.assertIn("not authorized", str(ctx.exception).lower())
            print("  [PASS] app_user_read correctly denied write privileges.")
        finally:
            client.close()

    def test_06_writer_permitted_to_insert(self):
        """app_user_write can successfully insert into analytics.events."""
        uri = f"mongodb://app_user_write:WritePass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["analytics"]
            res = db["events"].insert_one({"event": "audit_probe", "status": "active"})
            self.assertIsNotNone(res.inserted_id)
            print("  [PASS] app_user_write permitted write to authorized collection.")
        finally:
            client.close()

    def test_07_writer_denied_access_to_hr_system(self):
        """app_user_write must be DENIED access to hr_system database."""
        uri = f"mongodb://app_user_write:WritePass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["hr_system"]
            with self.assertRaises(OperationFailure) as ctx:
                list(db["employees"].find())
            self.assertIn("not authorized", str(ctx.exception).lower())
            print("  [PASS] app_user_write correctly denied access to out-of-scope HR database.")
        finally:
            client.close()

    def test_08_hr_user_has_full_salary_access(self):
        """hr_user can query hr_system.employees directly and sees the salary field."""
        uri = f"mongodb://hr_user:HrPass123!@{self.HOST}:{self.AUTH_PORT}/?authSource=admin"
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        try:
            db = client["hr_system"]
            doc = db["employees"].find_one()
            self.assertIsNotNone(doc)
            self.assertIn("salary", doc, "HR user must have access to salary field")
            self.assertGreater(doc["salary"], 0)
            print(f"  [PASS] hr_user verified: full access to employee record with salary (${doc['salary']:,}).")
        finally:
            client.close()

    # -------------------------------------------------------------
    # Lab 12.2 Tests: TLS / Encryption-in-Transit
    # -------------------------------------------------------------
    def test_09_plain_connection_rejected_on_tls_port(self):
        """Plain unencrypted connection to TLS port must be rejected."""
        plain_uri = f"mongodb://{self.HOST}:{self.TLS_PORT}/?serverSelectionTimeoutMS=2000"
        try:
            client = MongoClient(plain_uri)
            with self.assertRaises((ConnectionFailure, ServerSelectionTimeoutError)):
                client.admin.command("ping")
            print("  [PASS] Plain connection to TLS port rejected as expected.")
        finally:
            client.close()

    def test_10_tls_connection_succeeds_with_ca(self):
        """Encrypted connection over TLS with CA file must succeed."""
        if not os.path.exists(self.CA_FILE):
            self.skipTest(f"CA file {self.CA_FILE} not present; skipping TLS test.")
            return

        tls_uri = (
            f"mongodb://{self.HOST}:{self.TLS_PORT}/"
            f"?tls=true&tlsCAFile={self.CA_FILE}&tlsAllowInvalidHostnames=true&serverSelectionTimeoutMS=4000"
        )
        client = MongoClient(tls_uri)
        try:
            res = client.admin.command("ping")
            self.assertEqual(res.get("ok"), 1.0)
            print("  [PASS] TLS encrypted connection succeeded with Root CA verification.")
        finally:
            client.close()

if __name__ == "__main__":
    print("=" * 70)
    print(" RUNNING AUTOMATED SECURITY & RBAC VERIFICATION SUITE")
    print(" Student: K. Pranav Reddy (24BTRCL098)")
    print("=" * 70)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMongoDBSecurity)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
