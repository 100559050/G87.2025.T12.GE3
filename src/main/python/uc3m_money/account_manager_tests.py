import unittest
from uc3m_money.account_manager import AccountManager
from uc3m_money.account_management_exception import AccountManagementException
from datetime import datetime, timedelta

class TestAccountManager(unittest.TestCase):

    def setUp(self):
        self.manager = AccountManager()

    # ---------- validate_iban ----------
    def test_validate_valid_iban(self):
        valid_iban = "ES9121000418450200051332"
        self.assertEqual(self.manager.validate_iban(valid_iban), valid_iban)

    def test_validate_invalid_iban_format(self):
        with self.assertRaises(AccountManagementException):
            self.manager.validate_iban("ES123")

    def test_validate_invalid_iban_control_digit(self):
        with self.assertRaises(AccountManagementException):
            self.manager.validate_iban("ES0021000418450200051332")

    # ---------- validate_concept ----------
    def test_valid_concept(self):
        try:
            self.manager.validate_concept("Transfer payment")
        except AccountManagementException:
            self.fail("validate_concept() raised Exception unexpectedly!")

    def test_invalid_concept_too_short(self):
        with self.assertRaises(AccountManagementException):
            self.manager.validate_concept("Too short")

    def test_invalid_concept_format(self):
        with self.assertRaises(AccountManagementException):
            self.manager.validate_concept("invalid123concept")

    # ---------- validate_transfer_date ----------
    def test_valid_transfer_date_today(self):
        today = datetime.now().strftime("%d/%m/%Y")
        self.assertEqual(self.manager.validate_transfer_date(today), today)

    def test_valid_transfer_date_future(self):
        future_date = (datetime.now() + timedelta(days=5)).strftime("%d/%m/%Y")
        self.assertEqual(self.manager.validate_transfer_date(future_date), future_date)

    def test_transfer_date_past(self):
        past_date = (datetime.now() - timedelta(days=5)).strftime("%d/%m/%Y")
        with self.assertRaises(AccountManagementException):
            self.manager.validate_transfer_date(past_date)

    def test_invalid_date_format(self):
        with self.assertRaises(AccountManagementException):
            self.manager.validate_transfer_date("2024-12-25")

    def test_invalid_year_range(self):
        bad_year = "01/01/2020"
        with self.assertRaises(AccountManagementException):
            self.manager.validate_transfer_date(bad_year)


if __name__ == '__main__':
    unittest.main()
