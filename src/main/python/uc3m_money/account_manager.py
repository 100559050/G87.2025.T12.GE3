"""Account manager module """
import re
import json
from datetime import datetime, timezone
from uc3m_money.account_management_exception import AccountManagementException
from uc3m_money.account_management_config import (
    TRANSFERS_STORE_FILE,
    DEPOSITS_STORE_FILE,
    TRANSACTIONS_STORE_FILE,
    BALANCES_STORE_FILE
)
from uc3m_money.transfer_request import TransferRequest
from uc3m_money.account_deposit import AccountDeposit
from uc3m_money.singleton_meta import SingletonMeta


class AccountManager(metaclass=SingletonMeta):
    """Class for providing the methods for managing the orders"""
    def __init__(self):
        pass

    def read_json_file(self, file_path):
        """Reads a JSON file and returns its content or an empty list."""
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                return json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    def write_json_file(self, file_path, data):
        """Writes data to a JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8", newline="") as file:
                json.dump(data, file, indent=2)
        except FileNotFoundError as ex:
            raise AccountManagementException("Wrong file or file path") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

    @staticmethod
    def validate_iban(iban_str: str):
        """Validates the control digit of a Spanish IBAN."""
        iban_pattern = re.compile(r"^ES[0-9]{22}")
        result_expression = iban_pattern.fullmatch(iban_str)
        if not result_expression:
            raise AccountManagementException("Invalid IBAN format")
        iban = iban_str
        original_code = iban[2:4]
        iban = iban[:2] + "00" + iban[4:]
        iban = iban[4:] + iban[:4]
        for char, value in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", range(10, 36)):
            iban = iban.replace(char, str(value))
        numeric_iban = int(iban)
        remainder = numeric_iban % 97
        computed_dc = 98 - remainder
        if int(original_code) != computed_dc:
            raise AccountManagementException("Invalid IBAN control digit")
        return iban_str

    def validate_concept(self, concept: str):
        """Validates the concept string for correct format and length."""
        pattern = r"^(?=^.{10,30}$)([a-zA-Z]+(\s[a-zA-Z]+)+)$"
        if not re.fullmatch(pattern, concept):
            raise AccountManagementException("Invalid concept format")

    def validate_transfer_date(self, t_d):
        """Validates the arrival date format using regex."""
        mr = re.compile(r"^(([0-2]\d|3[0-1])\/(0\d|1[0-2])\/\d\d\d\d)$")
        if not mr.fullmatch(t_d):
            raise AccountManagementException("Invalid date format")
        try:
            my_date = datetime.strptime(t_d, "%d/%m/%Y").date()
        except ValueError as ex:
            raise AccountManagementException("Invalid date format") from ex
        if my_date < datetime.now(timezone.utc).date():
            raise AccountManagementException("Transfer date must be today or later.")
        if my_date.year < 2025 or my_date.year > 2050:
            raise AccountManagementException("Invalid date format")
        return t_d

    def validate_transfer_details(self, concept, transfer_type, date, amount):
        """Validates transfer concept, type, date, and amount."""
        self.validate_concept(concept)
        if not re.fullmatch(r"(ORDINARY|INMEDIATE|URGENT)", transfer_type):
            raise AccountManagementException("Invalid transfer type")
        self.validate_transfer_date(date)
        try:
            f_amount = float(amount)
        except ValueError as exc:
            raise AccountManagementException("Invalid transfer amount") from exc
        if '.' in str(f_amount) and len(str(f_amount).split('.')[1]) > 2:
            raise AccountManagementException("Invalid transfer amount")
        if f_amount < 10 or f_amount > 10000:
            raise AccountManagementException("Invalid transfer amount")
        return f_amount

    def is_duplicate_transfer(self, transfer_list, request):
        """Check if the transfer is already in the list."""
        for t_i in transfer_list:
            if (t_i["from_iban"] == request.from_iban and
                t_i["to_iban"] == request.to_iban and
                t_i["transfer_date"] == request.transfer_date and
                t_i["transfer_amount"] == request.transfer_amount and
                t_i["transfer_concept"] == request.transfer_concept and
                t_i["transfer_type"] == request.transfer_type):
                return True
        return False

    def transfer_request(self, from_iban: str,
                         to_iban: str,
                         concept: str,
                         transfer_type: str,
                         date: str,
                         amount: float) -> str:
        """Receives transfer info and stores it into a file."""
        self.validate_iban(from_iban)
        self.validate_iban(to_iban)
        validated_amount = self.validate_transfer_details(concept, transfer_type, date, amount)

        my_request = TransferRequest(
            from_iban=from_iban,
            to_iban=to_iban,
            transfer_concept=concept,
            transfer_type=transfer_type,
            transfer_date=date,
            transfer_amount=validated_amount
        )

        transfer_list = self.read_json_file(TRANSFERS_STORE_FILE)
        if self.is_duplicate_transfer(transfer_list, my_request):
            raise AccountManagementException("Duplicated transfer in transfer list")
        transfer_list.append(my_request.to_json())
        self.write_json_file(TRANSFERS_STORE_FILE, transfer_list)

        return my_request.transfer_code

    def deposit_into_account(self, input_file: str) -> str:
        """Manages deposits received for accounts."""
        try:
            with open(input_file, "r", encoding="utf-8", newline="") as file:
                i_d = json.load(file)
        except FileNotFoundError as ex:
            raise AccountManagementException("Error: file input not found") from ex
        except json.JSONDecodeError as ex:
            raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex

        try:
            deposit_iban = i_d["IBAN"]
            deposit_amount = i_d["AMOUNT"]
        except KeyError as e:
            raise AccountManagementException("Error - Invalid Key in JSON") from e

        deposit_iban = self.validate_iban(deposit_iban)
        if not re.fullmatch(r"^EUR [0-9]{4}\.[0-9]{2}", deposit_amount):
            raise AccountManagementException("Error - Invalid deposit amount")

        d_a_f = float(deposit_amount[4:])
        if d_a_f == 0:
            raise AccountManagementException("Error - Deposit must be greater than 0")

        deposit_obj = AccountDeposit(to_iban=deposit_iban, deposit_amount=d_a_f)
        deposit_list = self.read_json_file(DEPOSITS_STORE_FILE)
        deposit_list.append(deposit_obj.to_json())
        self.write_json_file(DEPOSITS_STORE_FILE, deposit_list)

        return deposit_obj.deposit_signature

    def calculate_balance(self, iban: str) -> bool:
        """Calculate the balance for a given IBAN."""
        iban = self.validate_iban(iban)
        transactions = self.read_json_file(TRANSACTIONS_STORE_FILE)

        iban_found = False
        balance = 0.0
        for transaction in transactions:
            if transaction.get("IBAN") == iban:
                balance += float(transaction.get("amount", 0))
                iban_found = True

        if not iban_found:
            raise AccountManagementException("IBAN not found")

        last_balance = {
            "IBAN": iban,
            "time": datetime.timestamp(datetime.now(timezone.utc)),
            "BALANCE": balance
        }

        balance_list = self.read_json_file(BALANCES_STORE_FILE)
        balance_list.append(last_balance)
        self.write_json_file(BALANCES_STORE_FILE, balance_list)

        return True
