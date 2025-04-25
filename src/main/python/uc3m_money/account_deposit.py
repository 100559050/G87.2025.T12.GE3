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
        self.__algorithm = "SHA-256"
        self.__transaction_type = "DEPOSIT"
        self.__to_iban = to_iban
        self.__deposit_amount = deposit_amount
        self.__deposit_date = datetime.timestamp(datetime.now(timezone.utc))

    @property
    def algorithm(self) -> str:
        """Returns the algorithm used for signature generation."""
        return self.__algorithm

    @property
    def transaction_type(self) -> str:
        return self.__transaction_type

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

    def __compose_signature_string(self) -> str:
        return (
            f"{{alg:{self.__algorithm},typ:{self.__transaction_type},"
            f"iban:{self.__to_iban},amount:{self.__deposit_amount},"
            f"deposit_date:{self.__deposit_date}}}"
        )

    @property
    def deposit_signature(self) -> str:
        """SHA-256 hash uniquely identifying this deposit"""
        return hashlib.sha256(self.__compose_signature_string().encode()).hexdigest()

    def to_json(self) -> dict:
        """Returns a JSON-serializable dictionary of the deposit"""
        return {
            "alg": self.algorithm,
            "type": self.transaction_type,
            "to_iban": self.__to_iban,
            "deposit_amount": self.__deposit_amount,
            "deposit_date": self.__deposit_date,
            "deposit_signature": self.deposit_signature
        }
