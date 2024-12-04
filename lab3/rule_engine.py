from fuzzy_logic import fuzzify_temperature, fuzzify_humidity, defuzzify_watering


class RuleEngine:
    def __init__(self, db_driver):
        """
        Конструктор RuleEngine
        :param db_driver: Экземпляр класса, отвечающего за подключение к Neo4j
        """
        self.db_driver = db_driver

    def process_watering(self, plant_type, temperature, humidity, time_of_day):
        """
        Обрабатывает данные и возвращает рассчитанную влажность
        :param plant_type: Тип растения
        :param temperature: Текущая температура (int)
        :param humidity: Текущая влажность (int)
        :param time_of_day: Время суток (строка)
        :return: Увеличение влажности (float)
        """
        # Фаззификация температуры и влажности
        fuzzified_temperature = fuzzify_temperature(temperature)
        fuzzified_humidity = fuzzify_humidity(humidity)

        print(f"Фаззифицированные данные: температура = {fuzzified_temperature}, влажность = {fuzzified_humidity}")

        # Первичная проверка базовых правил
        basic_rule = self.db_driver.fetch_basic_watering(plant_type, fuzzified_humidity)
        if basic_rule:
            print(f"Базовое правило применено: {basic_rule['rule_name']} — Действие: {basic_rule['action_name']}")
            return defuzzify_watering(basic_rule["action_name"])

        # Углубленная проверка дополнительных условий
        advanced_rule = self.db_driver.fetch_advanced_watering(
            plant_type,
            fuzzified_humidity,
            fuzzified_temperature,
            time_of_day,
        )
        if advanced_rule:
            print(f"Углубленное правило применено: {advanced_rule['rule_name']} — Действие: {advanced_rule['action_name']}")
            return defuzzify_watering(advanced_rule["action_name"])

        print("Нет применимых правил для текущих условий.")
        return 0  # Если правил нет, возвращаем нулевую добавку к влажности
