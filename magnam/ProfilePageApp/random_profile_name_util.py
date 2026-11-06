import random
from .globals import *


def int_to_roman(num):
    """Converts an integer from 1 to 100 into a Roman Numeral string."""
    val = [100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ""
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num


def generate_random_profile_name():
    """
    Generates a funny, randomized profile name adhering to:
    {roman_numeral}. {Adjective} {Noun1} ({Noun2 Noun3}) #{5-digit-id}
    """
    roman = int_to_roman(random.randint(1, 100))
    adj = random.choice(ADJECTIVES)
    noun1 = random.choice(NOUNS_ANIMAL)
    noun2 = random.choice(NOUNS_PHYSICAL)
    noun3 = random.choice(NOUNS_AGENT)
    collision_id = f"{random.randint(0, 99999):05d}"

    return f"{roman}. {adj} {noun1} ({noun2} {noun3}) #{collision_id}"
