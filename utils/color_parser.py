"""
Color raqamini normalizatsiya qilish moduli.
Turli formatdagi color raqamlarini standart formatga keltiradi.

Qabul qilinadigan formatlar:
  - "23/33"        — to'g'ri format
  - "23 33"        — bo'sh joy bilan
  - "2333"         — slashsiz (agar 4 yoki undan ko'p raqam bo'lsa)
  - "#23/33"       — hashtag bilan
  - "color 23/33"  — "color" so'zi bilan
  - "23/33 color"  — "color" oxirida
"""

import re
from typing import Optional


def normalize_color_code(text: str) -> Optional[str]:
    """
    Berilgan matndan color raqamini ajratib,
    standart 'XX/YYY' formatiga keltiradi.

    Agar color raqam topilmasa, None qaytaradi.
    standart 'XX/YYY' formatiga va barcha ortiqcha belgilarsiz holatga keltiradi.
    """
    if not text or not text.strip():
        return None

    # Matnni tozalash, harflar, hashtaglar, belgilar, probellardan tozalash
    cleaned = text.replace('#', '').replace('*', '').replace('&', '').strip().upper()
    
    # "color" va "цвет" so'zlarini olib tashlash
    cleaned = re.sub(r'\b(color|цвет)\b', '', cleaned, flags=re.IGNORECASE).strip()
    
    # Ortiqcha harflarni butunlay olib tashlash (faqat raqam va slashlarni qoldirish)
    cleaned = re.sub(r'[^0-9/]', '', cleaned)

    # Format 1: XX/YYY (slash bilan)
    match = re.search(r'(\d+)\s*/\s*(\d+)', cleaned)
    if match:
        try:
            part1 = str(int(match.group(1)))
            part2 = str(int(match.group(2)))
            return f"{part1}/{part2}"
        except ValueError:
            pass

    # Format 2: XX YYY (bo'sh joy bilan)
    match = re.search(r'(\d+)\s+(\d+)', cleaned)
    if match:
        try:
            part1 = str(int(match.group(1)))
            part2 = str(int(match.group(2)))
            return f"{part1}/{part2}"
        except ValueError:
            pass

    # Format 3: XXYY yoki XXYYY (slashsiz)
    match = re.search(r'(\d{3,})', cleaned)
    if match:
        digits = match.group(1)
        result = _split_digits(digits)
        if result:
            parts = result.split('/')
            try:
                p1 = str(int(parts[0]))
                p2 = str(int(parts[1]))
                return f"{p1}/{p2}"
            except ValueError:
                pass

    # Faqat bitta raqam bo'lsa (slashsiz va qisqa)
    if cleaned.isdigit():
        return str(int(cleaned))

    return None


def _split_digits(digits: str) -> Optional[str]:
    """
    Bitishgan raqamlarni XX/YY formatiga ajratadi.
    
    Strategiya:
    - 4 ta raqam: 2/2 ajratish (masalan: 2333 -> 23/33)
    - 5 ta raqam: 2/3 ajratish (masalan: 70830 -> 70/830)
    - 6 ta raqam: 3/3 ajratish (masalan: 100200 -> 100/200)
    - 3 ta raqam: 1/2 ajratish (masalan: 233 -> 2/33)
    """
    length = len(digits)

    if length == 4:
        # 2/2: masalan "2333" -> "23/33"
        return f"{digits[:2]}/{digits[2:]}"
    elif length == 5:
        # 2/3: masalan "70830" -> "70/830"
        return f"{digits[:2]}/{digits[2:]}"
    elif length == 6:
        # 3/3: masalan "100200" -> "100/200"
        return f"{digits[:3]}/{digits[3:]}"
    elif length == 3:
        # 1/2: masalan "233" -> "2/33"
        return f"{digits[:1]}/{digits[1:]}"
    elif length > 6:
        # Juda uzun — o'rtadan ajratamiz
        mid = length // 2
        return f"{digits[:mid]}/{digits[mid:]}"

    return None


def is_color_query(text: str) -> bool:
    """
    Berilgan matn color raqam so'rovi ekanligini tekshiradi.
    
    True qaytaradi agar matnda:
    - Raqam + slash + raqam bor
    - Yoki "color" so'zi bor
    - Yoki faqat raqamlardan iborat (3+ ta raqam)
    """
    if not text or not text.strip():
        return False

    cleaned = text.strip().lower()

    # Buyruqlarni e'tiborsiz qoldirish
    if cleaned.startswith('/'):
        return False

    # "color" so'zi bor
    if 'color' in cleaned:
        return True

    # Raqam/raqam formati bor
    if re.search(r'\d+\s*/\s*\d+', cleaned):
        return True

    # "#" dan keyin raqamlar
    if re.search(r'#\s*\d+', cleaned):
        return True

    # Faqat raqamlar va bo'sh joylardan iborat (kamida 2 ta raqam)
    digits_only = re.sub(r'[\s/#]', '', cleaned)
    if digits_only.isdigit() and len(digits_only) >= 2:
        return True

    # Raqam bo'sh joy raqam formati
    if re.search(r'^\d+\s+\d+$', cleaned):
        return True

    return False
