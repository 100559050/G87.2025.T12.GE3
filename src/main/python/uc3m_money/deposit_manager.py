"""Deposit manager module"""
import os
import re
import json
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import DEPOSITS_STORE_FILE
from uc3m_money.account_deposit import AccountDeposit
from uc3m_money.singleton_meta import SingletonMeta
from uc3m_money.transfer_manager import TransferManager


class DepositManager(metaclass=SingletonMeta):
    """Class for managing deposit operations"""

    def __init__(self):
        self._transfer = TransferManager()

    def load_json_or_empty(self, file_path: str):
        """Load JSON list from file or return empty list if missing."""
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def append_record(self, file_path: str, record):
        """Append a record to a JSON list in file."""
        records = self.load_json_or_empty(file_path)
        records.append(record)
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as file:
                json.dump(records, file, indent=2)
        except FileNotFoundError as ex:
            raise AccountManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def _load_json_strict(self, file_path: str):
        """Load JSON from file, raising exceptions if file not found or invalid JSON."""
        if not os.path.isfile(file_path):
            raise AccountManagementException("Error: file input not found")
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                return json.load(file)
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def _validate_deposit_payload(self, deposit_data: dict) -> tuple[str, float]:
        """Validate deposit data and return validated IBAN and amount."""
        try:
            deposit_iban = deposit_data["IBAN"]
            deposit_amount = deposit_data["AMOUNT"]
        except KeyError as e:
            raise AccountManagementException("Error - Invalid Key in JSON") from e

        deposit_iban = self._transfer.validate_iban(deposit_iban)
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
        self.append_record(DEPOSITS_STORE_FILE, deposit_obj.to_json())
        return deposit_obj.deposit_signature

    def deposit(self, file_path: str) -> str:
        """Manages deposits received for accounts."""
        deposit_data = self._load_json_strict(file_path)
        deposit_iban, deposit_amount = self._validate_deposit_payload(deposit_data)
        deposit_obj = self._create_deposit(deposit_iban, deposit_amount)
        return self._persist_deposit(deposit_obj)