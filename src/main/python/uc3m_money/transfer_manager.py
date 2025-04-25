"""Transfer manager module"""
import re
from datetime import datetime, timezone
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import TRANSFERS_STORE_FILE
from uc3m_money.transfer_request import TransferRequest
from uc3m_money.singleton_meta import SingletonMeta
from uc3m_money.utils import append_record, validate_iban, load_json_or_empty


class TransferManager(metaclass=SingletonMeta):
    """Class for managing transfer operations"""
    def __init__(self):
        pass

    def validate_concept(self, concept: str):
        """Validates the concept string for correct format and length."""
        pattern = r"^(?=^.{10,30}$)([a-zA-Z]+(\s[a-zA-Z]+)+)$"
        if not re.fullmatch(pattern, concept):
            raise AccountManagementException("Invalid concept format")

    def validate_transfer_date(self, date_str):
        """Validates that the transfer date has a correct format and is not in the past"""
        date_pattern = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        if not date_pattern.fullmatch(date_str):
            raise AccountManagementException("Invalid date format")
        try:
            transfer_date = datetime.strptime(date_str, "%d/%m/%Y").date()
        except ValueError as ex:
            raise AccountManagementException("Invalid date format") from ex
        if transfer_date < datetime.now(timezone.utc).date():
            raise AccountManagementException("Transfer date must be today or later.")
        if transfer_date.year < 2025 or transfer_date.year > 2050:
            raise AccountManagementException("Invalid date format")
        return date_str

    def _validate_transfer_amount(self, amount) -> float:
        try:
            amount = float(amount)
        except ValueError as exc:
            raise AccountManagementException("Invalid transfer amount") from exc
        if '.' in str(amount) and len(str(amount).split('.')[1]) > 2:
            raise AccountManagementException("Invalid transfer amount")
        if amount < 10 or amount > 10000:
            raise AccountManagementException("Invalid transfer amount")
        return amount

    def validate_transfer_parameters(self, concept, transfer_type, date, amount):
        """Validates transfer concept, type, date, and amount."""
        self.validate_concept(concept)
        if not re.fullmatch(r"(ORDINARY|INMEDIATE|URGENT)", transfer_type):
            raise AccountManagementException("Invalid transfer type")
        self.validate_transfer_date(date)
        validated_amount = self._validate_transfer_amount(amount)
        return validated_amount

    def is_duplicate_transfer(self, transfer_list, request):
        """Check if the transfer is already in the list."""
        for existing in transfer_list:
            if (existing["from_iban"] == request.from_iban and
                existing["to_iban"] == request.to_iban and
                existing["transfer_date"] == request.transfer_date and
                existing["transfer_amount"] == request.transfer_amount and
                existing["transfer_concept"] == request.transfer_concept and
                existing["transfer_type"] == request.transfer_type):
                return True
        return False

    def create_transfer(self, from_iban: str,
                       to_iban: str,
                       concept: str,
                       transfer_type: str,
                       date: str,
                       amount: float) -> str:
        """Creates and stores a transfer request."""
        validate_iban(from_iban)
        validate_iban(to_iban)
        validated_amount = self.validate_transfer_parameters(concept, transfer_type, date, amount)

        transfer = TransferRequest(
            from_iban=from_iban,
            transfer_type=transfer_type,
            to_iban=to_iban,
            transfer_concept=concept,
            transfer_date=date,
            transfer_amount=validated_amount
        )

        transfer_list = load_json_or_empty(TRANSFERS_STORE_FILE)
        if self.is_duplicate_transfer(transfer_list, transfer):
            raise AccountManagementException("Duplicated transfer in transfer list")
        append_record(TRANSFERS_STORE_FILE, transfer.to_json())

        return transfer.transfer_code