""""Account deposit module"""
from datetime import datetime, timezone
import hashlib


class AccountDeposit:
    """
    Class representing a deposit into an account.
    Generates a secure deposit signature and provides serialization.
    """
    def __init__(self, to_iban: str, deposit_amount: float):
        """Initialize the deposit with IBAN, amount, and timestamp."""
        self.__alg = "SHA-256"
        self.__type = "DEPOSIT"
        self.__to_iban = to_iban
        self.__deposit_amount = deposit_amount
        self.__deposit_date = datetime.timestamp(datetime.now(timezone.utc))

    @property
    def alg(self) -> str:
        """Returns the algorithm used for signature generation."""
        return self.__alg

    @property
    def type(self) -> str:
        """Returns the type of transaction (DEPOSIT)."""
        return self.__type

    @property
    def to_iban(self) -> str:
        """Returns the recipient IBAN of the deposit."""
        return self.__to_iban

    @property
    def deposit_amount(self) -> float:
        """Returns the amount of the deposit."""
        return self.__deposit_amount

    @property
    def deposit_date(self) -> float:
        """Returns the timestamp of when the deposit was created."""
        return self.__deposit_date

    def __signature_string(self) -> str:
        """Composes the string to be used for generating the signature."""
        return "{alg:" + str(self.__alg) + ",typ:" + str(self.__type) + ",iban:" + \
               str(self.__to_iban) + ",amount:" + str(self.__deposit_amount) + \
               ",deposit_date:" + str(self.__deposit_date) + "}"

    @property
    def deposit_signature(self) -> str:
        """Returns the SHA-256 signature of the deposit."""
        return hashlib.sha256(self.__signature_string().encode()).hexdigest()

    def to_json(self) -> dict:
        """Serializes the deposit into a dictionary suitable for JSON storage."""
        return {
            "alg": self.alg,
            "type": self.type,
            "to_iban": self.to_iban,
            "deposit_amount": self.deposit_amount,
            "deposit_date": self.deposit_date,
            "deposit_signature": self.deposit_signature
        }
