def triangular_membership(value, left, peak, right):
    """
    Треугольная функция принадлежности.
    :param value: Значение, которое проверяется.
    :param left: Левая граница треугольника.
    :param peak: Пик треугольника.
    :param right: Правая граница треугольника.
    :return: Степень принадлежности от 0 до 1.
    """
    if left <= value <= peak:
        return (value - left) / (peak - left)
    elif peak < value <= right:
        return (right - value) / (right - peak)
    return 0


def calculate_humidity_decrease(temperature):
    """
    Рассчитывает уменьшение влажности на основе температуры с использованием треугольной функции принадлежности.
    :param temperature: Текущая температура в теплице.
    :return: Значение уменьшения влажности.
    """
    temp_fuzzy = fuzzify_temperature(temperature)  # Получаем строку: "Низкая", "Средняя", "Высокая"
    if temp_fuzzy == "Низкая":
        return 5  # Уменьшение для низкой температуры
    elif temp_fuzzy == "Средняя":
        return 10  # Уменьшение для средней температуры
    elif temp_fuzzy == "Высокая":
        return 15  # Уменьшение для высокой температуры
    return 0  # На случай непредвиденных ситуаций



def fuzzify_temperature(value):
    """
    Фаззификация температуры с использованием треугольной функции принадлежности.
    Возвращает строку с максимальной степенью принадлежности.
    :param value: Температура (int).
    :return: Строка, соответствующая максимальной степени принадлежности.
    """
    memberships = {
        "Низкая": triangular_membership(value, 0, 10, 15),
        "Средняя": triangular_membership(value, 15, 20, 25),
        "Высокая": triangular_membership(value, 25, 30, 40)
    }
    return max(memberships, key=memberships.get)




def fuzzify_humidity(value):
    """
    Фаззификация влажности с использованием треугольной функции принадлежности.
    Возвращает строку с максимальной степенью принадлежности.
    :param value: Влажность (int).
    :return: Строка, соответствующая максимальной степени принадлежности.
    """
    memberships = {
        "Низкая": triangular_membership(value, 0, 30, 40),
        "Средняя": triangular_membership(value, 40, 55, 70),
        "Высокая": triangular_membership(value, 70, 85, 100)
    }
    return max(memberships, key=memberships.get)



def defuzzify_watering(level):
    """
    Дефаззификация действия полива на основе треугольной функции принадлежности.
    :param level: Уровень полива (строка).
    :return: Числовое значение полива.
    """
    watering_levels = {
        "Полив минимальный": (0, 5, 10),
        "Полив умеренный": (10, 15, 20),
        "Полив сильный": (20, 25, 30)
    }
    if level in watering_levels:
        left, peak, right = watering_levels[level]
        return triangular_membership(peak, left, peak, right) * peak
    return 0
