from __future__ import annotations

def short_number(value: int | float) -> str:
    """
    Форматирует число так, что всё, что >= 1000,
    отображается в тысячах с суффиксом 'k' и
    группировкой цифр пробелами:
      100     -> "100"
      1_000   -> "1k"
      15_000  -> "15k"
      1_200_000 -> "1 200k"
      12_400_000 -> "12 400k"
      124_000_000 -> "124 000k"
      1_000_000_000 -> "1 000 000k"
      1_000_000_000_000 -> "1 000 000 000k"
    """
    value = int(value)
    if value >= 1_000:
        thousands = value // 1_000
        # группируем пробелами по три цифры
        grouped = f"{thousands:,}".replace(",", " ")
        return f"{grouped}k"
    return str(value)
