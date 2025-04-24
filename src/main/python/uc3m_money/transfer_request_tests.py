import unittest
from uc3m_money.transfer_request import TransferRequest
import hashlib
from datetime import datetime


class TestTransferRequest(unittest.TestCase):

    def setUp(self):
        self.request = TransferRequest(
            from_iban="ES9121000418450200051332",
            to_iban="ES7921000813610123456789",
            transfer_concept="Test payment",
            transfer_type="ORDINARY",
            transfer_date="25/12/2025",
            transfer_amount=250.75
        )

    def test_attributes_assignment(self):
        self.assertEqual(self.request.from_iban, "ES9121000418450200051332")
        self.assertEqual(self.request.to_iban, "ES7921000813610123456789")
        self.assertEqual(self.request.transfer_concept, "Test payment")
        self.assertEqual(self.request.transfer_type, "ORDINARY")
        self.assertEqual(self.request.transfer_date, "25/12/2025")
        self.assertEqual(self.request.transfer_amount, 250.75)

    def test_transfer_code_is_md5(self):
        code = self.request.transfer_code
        self.assertEqual(len(code), 32)  # MD5 hash length
        self.assertTrue(all(c in "0123456789abcdef" for c in code))

    def test_transfer_code_determinism(self):
        repeat_request = TransferRequest(
            from_iban=self.request.from_iban,
            to_iban=self.request.to_iban,
            transfer_concept=self.request.transfer_concept,
            transfer_type=self.request.transfer_type,
            transfer_date=self.request.transfer_date,
            transfer_amount=self.request.transfer_amount
        )
        # force same timestamp
        repeat_request._TransferRequest__time_stamp = self.request.time_stamp
        self.assertEqual(self.request.transfer_code, repeat_request.transfer_code)

    def test_to_json_output(self):
        json_obj = self.request.to_json()
        self.assertEqual(json_obj["from_iban"], self.request.from_iban)
        self.assertEqual(json_obj["to_iban"], self.request.to_iban)
        self.assertEqual(json_obj["transfer_concept"], self.request.transfer_concept)
        self.assertEqual(json_obj["transfer_type"], self.request.transfer_type)
        self.assertEqual(json_obj["transfer_date"], self.request.transfer_date)
        self.assertEqual(json_obj["transfer_amount"], self.request.transfer_amount)
        self.assertEqual(json_obj["time_stamp"], self.request.time_stamp)
        self.assertEqual(json_obj["transfer_code"], self.request.transfer_code)


if __name__ == '__main__':
    unittest.main()