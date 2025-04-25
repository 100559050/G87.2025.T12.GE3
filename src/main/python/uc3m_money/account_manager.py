"""Account manager module """
import os.path
import re
from datetime import datetime, timezone
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import (
    TRANSACTIONS_STORE_FILE,
    BALANCES_STORE_FILE,
    DEPOSITS_STORE_FILE
)
from uc3m_money.singleton_meta import SingletonMeta
from uc3m_money.transfer_manager import TransferManager
from uc3m_money.account_deposit import AccountDeposit
from uc3m_money.utils import load_json_or_empty, append_record, validate_iban, load_json_strict

class AccountManager(metaclass=SingletonMeta):
    """Class for providing the methods for managing balances, deposits, and transfers"""
    def __init__(self):
        self._transfer = TransferManager()

    def transfer_request(self, from_iban: str,
                         to_iban: str,
                         concept: str,
                         transfer_type: str,
                         date: str,
                         amount: float) -> str:
        return self._transfer.create_transfer(
            from_iban=from_iban,
            to_iban=to_iban,
            concept=concept,
            transfer_type=transfer_type,
            date=date,
            amount=amount
        )

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

    def build_deposit_object(self, iban: str, amount: float) -> AccountDeposit:
        return AccountDeposit(to_iban=iban, deposit_amount=amount)

    def _save_deposit_record(self, deposit_obj: AccountDeposit) -> str:
        """Persist the deposit and return its signature."""
        append_record(DEPOSITS_STORE_FILE, deposit_obj.to_json())
        return deposit_obj.deposit_signature

    def deposit_into_account(self, file_path: str) -> str:
        """Manages deposits received for accounts."""
        deposit_data = load_json_strict(file_path)
        deposit_iban, deposit_amount = self._validate_deposit_payload(deposit_data)
        deposit_obj = self.build_deposit_object(deposit_iban, deposit_amount)
        return self._save_deposit_record(deposit_obj)

    def _load_transactions(self) -> list:
        """Load transactions from file, ensuring file exists."""
        if not os.path.isfile(TRANSACTIONS_STORE_FILE):
            raise AccountManagementException("Wrong file  or file path")
        return load_json_or_empty(TRANSACTIONS_STORE_FILE)

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

    def _save_balance_record(self, iban: str, balance: float) -> None:
        """Save the calculated balance to the balances file."""
        last_balance = {
            "IBAN": iban,
            "time": datetime.timestamp(datetime.now(timezone.utc)),
            "BALANCE": balance
        }
        append_record(BALANCES_STORE_FILE, last_balance)

    def calculate_balance(self, iban: str) -> bool:
        """Calculate the balance for a given IBAN."""
        iban = validate_iban(iban)
        transactions = self._load_transactions()
        balance = self._calculate_iban_balance(iban, transactions)
        self._save_balance_record(iban, balance)
        return True
