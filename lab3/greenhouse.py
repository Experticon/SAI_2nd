import random
import time
import random

from fuzzy_logic import calculate_humidity_decrease
from rule_engine import RuleEngine


class Sensor:
    def generate_temperature(self):
        """Генерация температуры"""
        return random.randint(5, 35)


class Plant:
    def __init__(self, name, plant_type, growth_days):
        self.name = name
        self.plant_type = plant_type
        self.growth_days = growth_days
        self.current_days = 0
        self.humidity = 100  # Начальная влажность 0%

    def grow(self):
        """Увеличивает количество дней роста."""
        self.current_days += 1
        return self.current_days >= self.growth_days

    def update_humidity(self, temperature):
        """
        Уменьшает влажность, используя фаззификацию температуры.
        :param temperature: Текущая температура в теплице.
        """
        humidity_decrease = calculate_humidity_decrease(temperature)
        self.humidity = max(0, self.humidity - humidity_decrease)  # Влажность не может быть отрицательной


class Greenhouse:
    def __init__(self, db, plant_names):
        self.db = db
        self.sensor = Sensor()
        self.rule_engine = RuleEngine(db)
        self.plants = self._initialize_plants(plant_names)
        self.day_count = 0
        self.time_of_day = "утро"

    def _initialize_plants(self, plant_names):
        """Создаёт объекты растений на основе ввода."""
        plants = []
        for name in plant_names:
            info = self.db.get_plant_info(name)
            if info:
                print(f"Растение '{info['name']}' отнесено к категории '{info['category']}', "
                      f"время роста: {info['growth_time_days']} дней.")
                plants.append(Plant(name, info["category"], info["growth_time_days"]))
            else:
                print(f"Растение '{name}' не найдено в базе знаний.")
                plants.append(Plant(name, "Другие растения", 5))  # Стандартное время роста для неизвестных растений
        return plants

    def _change_time_of_day(self):
        """Меняет время суток."""
        time_cycle = ["ночь", "утро", "день", "вечер"]
        self.time_of_day = time_cycle[(time_cycle.index(self.time_of_day) + 1) % len(time_cycle)]

        # При смене на ночь добавляем день и проверяем рост растений
        if self.time_of_day == "ночь":
            self.day_count += 1
            for plant in self.plants[:]:
                if plant.grow():
                    print(f"Растение '{plant.name}' полностью выросло!")
                    self.plants.remove(plant)

    def run_simulation(self):
        """Запускает симуляцию теплицы."""
        print("Начало симуляции теплицы...")
        while self.plants:
            print(f"\nДень {self.day_count}, {self.time_of_day.capitalize()}")

            # Генерация температуры
            temperature = self.sensor.generate_temperature()
            print(f"Температура: {temperature}°C")

            for plant in self.plants:
                # Вывод состояния растения до полива
                print(f"До полива: Растение '{plant.name}' (тип: {plant.plant_type}) — "
                      f"день роста: {plant.current_days}/{plant.growth_days}, "
                      f"влажность: {plant.humidity}%")

                # Обновляем влажность на основе температуры
                plant.update_humidity(temperature)

                # Определяем необходимость полива через правила
                additional_humidity = self.rule_engine.process_watering(
                    plant_type=plant.plant_type,
                    temperature=temperature,
                    humidity=plant.humidity,
                    time_of_day=self.time_of_day,
                )

                # Применяем полив
                plant.humidity = min(100, plant.humidity + additional_humidity)  # Влажность не должна превышать 100%

                # Вывод состояния растения после полива
                print(f"После полива: Растение '{plant.name}' (тип: {plant.plant_type}) — "
                      f"день роста: {plant.current_days}/{plant.growth_days}, "
                      f"влажность: {plant.humidity}%")

            # Если все растения выросли, завершаем симуляцию
            if not self.plants:
                print("Все растения выращены. Симуляция завершена.")
                break

            # Пауза и смена времени суток
            time.sleep(1)  # Замедление для удобства чтения
            self._change_time_of_day()
