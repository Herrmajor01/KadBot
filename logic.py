from db import get_case_numbers
from parser import process_case
import time
import random


def main_process_cases():
    cases = get_case_numbers()
    for case_number in cases:
        process_case(case_number)
        time.sleep(random.uniform(0.3, 0.7))  # не нагружаем сайт


if __name__ == "__main__":
    main_process_cases()
