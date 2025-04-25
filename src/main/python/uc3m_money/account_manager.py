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


class DepositService(metaclass=SingletonMeta):
    """Handles deposit processing and persistence."""
    def process_deposit_file(self, file_path: str) -> str:
        """Process a deposit file and return the deposit signature."""
        deposit_data = load_json_strict(file_path)
        deposit_iban, deposit_amount = self._validate_payload(deposit_data)
        deposit = self._create_deposit(deposit_iban, deposit_amount)
        return self._save_deposit(deposit)

    def _validate_payload(self, deposit_data: dict) -> tuple[str, float]:
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

    def _save_deposit(self, deposit_obj: AccountDeposit) -> str:
        """Save the deposit and return its signature."""
        append_record(DEPOSITS_STORE_FILE, deposit_obj.to_json())
        return deposit_obj.deposit_signature


class BalanceService(metaclass=SingletonMeta):
    """Handles balance calculation and persistence."""
    def calculate_and_save_balance(self, iban: str) -> bool:
        """Calculate and save balance for a given IBAN."""
        validated_iban = validate_iban(iban)
        transactions = self._load_transactions()
        balance = self._calculate_balance(validated_iban, transactions)
        self._save_balance(validated_iban, balance)
        return True

    def _load_transactions(self) -> list:
        """Load transactions from file."""
        if not os.path.isfile(TRANSACTIONS_STORE_FILE):
            raise AccountManagementException("Wrong file  or file path")
        return load_json_or_empty(TRANSACTIONS_STORE_FILE)

    def _calculate_balance(self, iban: str, transactions: list) -> float:
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

    def _save_balance(self, iban: str, balance: float) -> None:
        """Save balance record to the balances file."""
        balance_record = {
            "IBAN": iban,
            "time": datetime.timestamp(datetime.now(timezone.utc)),
            "BALANCE": balance
        }
        append_record(BALANCES_STORE_FILE, balance_record)


class AccountManager(metaclass=SingletonMeta):
    """Class for coordinating account management operations."""
    def __init__(self):
        self._transfer = TransferManager()
        self._deposit_service = DepositService()
        self._balance_service = BalanceService()

    def transfer_request(self, from_iban: str,
                         to_iban: str,
                         concept: str,
                         transfer_type: str,
                         date: str,
                         amount: float) -> str:
        """Process a transfer request between accounts."""
        return self._transfer.create_transfer(
            from_iban=from_iban,
            to_iban=to_iban,
            concept=concept,
            transfer_type=transfer_type,
            date=date,
            amount=amount
        )

    def deposit_into_account(self, file_path: str) -> str:
        """Process a deposit from a JSON file into an account."""
        return self._deposit_service.process_deposit_file(file_path)

    def calculate_balance(self, iban: str) -> bool:
        """Calculate and save the balance for an account."""
        return self._balance_service.calculate_and_save_balance(iban)
