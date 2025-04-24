"""Transfer request module"""
import hashlib
from datetime import datetime, timezone


class TransferRequest:
    """
    Represents a request to transfer money between two IBAN accounts.
    Stores key transfer details, timestamp, and supports serialization.
    """
    def __init__(self, from_iban: str, to_iban: str, transfer_concept: str,
                 transfer_type: str, transfer_date: str, transfer_amount: float):
        self.__from_iban = from_iban
        self.__to_iban = to_iban
        self.__transfer_concept = transfer_concept
        self.__transfer_type = transfer_type
        self.__transfer_date = transfer_date
        self.__transfer_amount = transfer_amount
        self.__time_stamp = datetime.timestamp(datetime.now(timezone.utc))

    @property
    def from_iban(self):
        return self.__from_iban

    @property
    def to_iban(self):
        return self.__to_iban

    @property
    def transfer_concept(self):
        return self.__transfer_concept

    @property
    def transfer_type(self):
        return self.__transfer_type

    @property
    def transfer_date(self):
        return self.__transfer_date

    @property
    def transfer_amount(self):
        return self.__transfer_amount

    @property
    def time_stamp(self):
        return self.__time_stamp

    @property
    def transfer_code(self) -> str:
        """
        Generates a unique transfer code using a hash of the IBANs, timestamp, and amount.
        """
        transfer_string = f"{self.from_iban}{self.to_iban}{self.time_stamp}{self.transfer_amount}"
        return hashlib.md5(transfer_string.encode()).hexdigest()

    def to_json(self) -> dict:
        """
        Serializes the transfer request into a dictionary suitable for JSON storage.
        """
        return {
            "from_iban": self.from_iban,
            "to_iban": self.to_iban,
            "transfer_concept": self.transfer_concept,
            "transfer_type": self.transfer_type,
            "transfer_date": self.transfer_date,
            "transfer_amount": self.transfer_amount,
            "time_stamp": self.time_stamp,
            "transfer_code": self.transfer_code
        }

    def __str__(self) -> str:
        return (
            f"Transfer from {self.from_iban} to {self.to_iban} of {self.transfer_amount} "
            f"on {self.transfer_date} [{self.transfer_type}] - Concept: {self.transfer_concept}"
        )
