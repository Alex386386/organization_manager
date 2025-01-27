from decimal import Decimal


def fractional_part_validator(v: Decimal) -> None:
    if len(str(v).split(".")[-1]) > 6:
        raise ValueError("Числа с точностью больше 6 знаков не принимаются.")
