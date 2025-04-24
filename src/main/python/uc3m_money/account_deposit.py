"""Account deposit module"""
from datetime import datetime, timezone
import hashlib


class AccountDeposit:
    """
    Class representing a deposit into an account.
    Generates a secure deposit signature and provides serialization.
    """
    def __init__(self, to_iban: str, deposit_amount: float):
        self.__alg = "SHA-256"
        self.__type = "DEPOSIT"
        self.__to_iban = to_iban
        self.__deposit_amount = deposit_amount
        self.__deposit_date = datetime.timestamp(datetime.now(timezone.utc))

    @property
    def alg(self) -> str:
        return self.__alg

    @property
    def type(self) -> str:
        return self.__type

    @property
    def to_iban(self) -> str:
        return self.__to_iban

    @property
    def deposit_amount(self) -> float:
        return self.__deposit_amount

    @property
    def deposit_date(self) -> float:
        return self.__deposit_date

    @property
    def deposit_signature(self) -> str:
        """
        Generates a SHA-256 hash to uniquely identify the deposit.
        """
        signature_string = f"{self.to_iban}{self.deposit_amount}{self.deposit_date}"
        return hashlib.sha256(signature_string.encode()).hexdigest()

    def to_json(self) -> dict:
        """
        Serializes the deposit into a dictionary suitable for JSON storage.
        """
        return {
            "alg": self.alg,
            "type": self.type,
            "to_iban": self.to_iban,
            "deposit_amount": self.deposit_amount,
            "deposit_date": self.deposit_date,
            "deposit_signature": self.deposit_signature
        }
