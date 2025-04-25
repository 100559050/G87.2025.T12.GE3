"""Common utility functions for file I/O and validation"""
import os
import re
import json
from uc3m_money.account_management_exception import AccountManagementException

def load_json_or_empty(file_path: str) -> list:
    """Load JSON list from file or return empty list if missing."""
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as ex:
        raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex


def write_json(file_path: str, data) -> None:
    """Write JSON data to file."""
    try:
        with open(file_path, "w", encoding="utf-8", newline="") as file:
            json.dump(data, file, indent=2)
    except FileNotFoundError as ex:
        raise AccountManagementException("Wrong file or file path") from ex


def append_record(file_path: str, record) -> None:
    """Append a record to a JSON list in file."""
    records = load_json_or_empty(file_path)
    records.append(record)
    write_json(file_path, records)


def load_json_strict(file_path: str):
    """Load JSON from file, raising exceptions if file not found or invalid JSON."""
    if not os.path.isfile(file_path):
        raise AccountManagementException("Error: file input not found")
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            return json.load(file)
    except json.JSONDecodeError as ex:
        raise AccountManagementException("JSON Decode Error - Wrong JSON Format") from ex


def validate_iban(iban_str: str) -> str:
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