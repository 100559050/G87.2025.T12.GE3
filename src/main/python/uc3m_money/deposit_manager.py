"""Deposit manager module"""
import re
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import DEPOSITS_STORE_FILE
from uc3m_money.account_deposit import AccountDeposit
from uc3m_money.singleton_meta import SingletonMeta
from uc3m_money.utils import append_record, load_json_strict, validate_iban


class DepositManager(metaclass=SingletonMeta):
    """Class for managing deposit operations"""
    def __init__(self):
        pass

    def _validate_deposit_payload(self, deposit_data: dict) -> tuple[str, float]:
        """Validate deposit data and return validated IBAN and amount."""
        try:
            deposit_iban = deposit_data["IBAN"]
            deposit_amount = deposit_data["AMOUNT"]
        except KeyError as e:
            raise AccountManagementException("Error - Invalid Key in JSON") from e

        deposit_iban = validate_iban(deposit_iban)
        if not re.fullmatch(r"^EUR [0-9]{4}\.[0-9]{2}", deposit_amount):
            raise AccountManagementException("Error - Invalid deposit amount")

        deposit_amount_float = float(deposit_amount[4:])
        if deposit_amount_float == 0:
            raise AccountManagementException("Error - Deposit must be greater than 0")

        return deposit_iban, deposit_amount_float

    def _create_deposit(self, iban: str, amount: float) -> AccountDeposit:
        """Create an AccountDeposit object with validated data."""
        return AccountDeposit(to_iban=iban, deposit_amount=amount)

    def _persist_deposit(self, deposit_obj: AccountDeposit) -> str:
        """Persist the deposit and return its signature."""
        append_record(DEPOSITS_STORE_FILE, deposit_obj.to_json())
        return deposit_obj.deposit_signature

    def deposit(self, file_path: str) -> str:
        """Manages deposits received for accounts."""
        deposit_data = load_json_strict(file_path)
        deposit_iban, deposit_amount = self._validate_deposit_payload(deposit_data)
        deposit_obj = self._create_deposit(deposit_iban, deposit_amount)
        return self._persist_deposit(deposit_obj)