"""Account manager module """
import os.path
import re
import json
from datetime import datetime, timezone
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import (
    TRANSACTIONS_STORE_FILE,
    BALANCES_STORE_FILE
)
from uc3m_money.singleton_meta import SingletonMeta
from uc3m_money.transfer_manager import TransferManager
from uc3m_money.deposit_manager import DepositManager


class AccountManager(metaclass=SingletonMeta):
    """Class for providing the methods for managing the orders"""

    def __init__(self):
        self._transfer = TransferManager()
        self._deposit = DepositManager()

    def load_json_or_empty(self, file_path: str):
        """Load JSON list from file or return empty list if missing."""
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def write_json(self, file_path: str, data):
        """Write JSON data to file."""
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as file:
                json.dump(data, file, indent=2)
        except FileNotFoundError as ex:
            raise AccountManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def append_record(self, file_path: str, record):
        """Append a record to a JSON list in file."""
        records = self.load_json_or_empty(file_path)
        records.append(record)
        self.write_json(file_path, records)

    def transfer_request(self, from_iban: str,
                         to_iban: str,
                         concept: str,
                         transfer_type: str,
                         date: str,
                         amount: float) -> str:
        """Delegates transfer request to TransferManager."""
        return self._transfer.create_transfer(
            from_iban=from_iban,
            to_iban=to_iban,
            concept=concept,
            transfer_type=transfer_type,
            date=date,
            amount=amount
        )

    def deposit_into_account(self, file_path: str) -> str:
        """Delegates deposit operation to DepositManager."""
        return self._deposit.deposit(file_path)

    def _load_transactions(self) -> list:
        """Load transactions from file, ensuring file exists."""
        if not os.path.isfile(TRANSACTIONS_STORE_FILE):
            raise AccountManagementException("Wrong file  or file path")
        return self.load_json_or_empty(TRANSACTIONS_STORE_FILE)

    def _calculate_iban_balance(self, iban: str, transactions: list) -> float:
        """Calculate balance for given IBAN from transactions."""
        iban_found = False
        balance = 0.0
        for transaction in transactions:
            if transaction.get("IBAN") == iban:
                balance += float(transaction.get("amount", 0))
                iban_found = True

        if not iban_found:
            raise AccountManagementException("IBAN not found")

        return balance

    def _persist_balance(self, iban: str, balance: float) -> None:
        """Save the calculated balance to the balances file."""
        last_balance = {
            "IBAN": iban,
            "time": datetime.timestamp(datetime.now(timezone.utc)),
            "BALANCE": balance
        }
        self.append_record(BALANCES_STORE_FILE, last_balance)

    def calculate_balance(self, iban: str) -> bool:
        """Calculate the balance for a given IBAN."""
        iban = self._transfer.validate_iban(iban)
        transactions = self._load_transactions()
        balance = self._calculate_iban_balance(iban, transactions)
        self._persist_balance(iban, balance)
        return True
