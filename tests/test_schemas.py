import unittest
from shared.schemas.base_entities import VerificationStatus, Provenance

class TestSchemas(unittest.TestCase):
    def test_provenance_instantiation(self):
        prov = Provenance(source_type="test", verification_status=VerificationStatus.VERIFIED)
        self.assertEqual(prov.source_type, "test")
        self.assertEqual(prov.verification_status, VerificationStatus.VERIFIED)

if __name__ == "__main__":
    unittest.main()
