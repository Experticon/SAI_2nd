from neo4j import GraphDatabase

class Neo4jDB:
    def __init__(self, uri, user, password):
        """
        Инициализация подключения к Neo4j.
        :param uri: URI для подключения к Neo4j.
        :param user: Имя пользователя.
        :param password: Пароль.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """
        Закрытие подключения к базе данных.
        """
        self.driver.close()

    def fetch_basic_watering(self, plant_type, fuzzified_humidity):
        """
        Получает базовые правила полива из базы данных.
        :param plant_type: Тип растения.
        :param fuzzified_humidity: Фаззифицированное значение влажности.
        :return: Словарь с правилом и действием, либо None, если правило не найдено.
        """
        query = """
        MATCH (rule:Rule {type: "basic"})-[:HAS_CONDITION]->(condition:Condition)
        WHERE condition.plant_type = $plant_type AND condition.humidity_level = $fuzzified_humidity
        MATCH (rule)-[:REQUIRES_ACTION]->(action:Action)
        RETURN rule.name AS rule_name, action.name AS action_name
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, plant_type=plant_type, fuzzified_humidity=fuzzified_humidity)
            record = result.single()
            if record:
                return {"rule_name": record["rule_name"], "action_name": record["action_name"]}
            return None

    def fetch_advanced_watering(self, plant_type, fuzzified_humidity, fuzzified_temperature, time_of_day):
        """
        Получает углубленные правила полива из базы данных.
        :param plant_type: Тип растения.
        :param fuzzified_humidity: Фаззифицированное значение влажности.
        :param fuzzified_temperature: Фаззифицированное значение температуры.
        :param time_of_day: Время суток.
        :return: Словарь с правилом и действием, либо None, если правило не найдено.
        """
        query = """
        MATCH (rule:Rule {type: "advanced"})-[:HAS_CONDITION]->(condition:Condition)
        WHERE condition.plant_type = $plant_type AND 
              condition.humidity_level = $fuzzified_humidity AND 
              condition.temperature = $fuzzified_temperature AND 
              condition.time_of_day = $time_of_day
        MATCH (rule)-[:REQUIRES_ACTION]->(action:Action)
        RETURN rule.name AS rule_name, action.name AS action_name
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(
                query,
                plant_type=plant_type,
                fuzzified_humidity=fuzzified_humidity,
                fuzzified_temperature=fuzzified_temperature,
                time_of_day=time_of_day,
            )
            record = result.single()
            if record:
                return {"rule_name": record["rule_name"], "action_name": record["action_name"]}
            return None

    def setup_ontology_and_rules(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")  # Очистка базы для примера

            for rule in WATERING_RULES:
                conditions = rule["conditions"]
                action_name = rule["action"]
                rule_type = rule["type"]

                # Создаем правило с учетом типа
                session.run("""
                MERGE (action:Action {name: $action_name})
                MERGE (rule:Rule {name: $rule_name, type: $rule_type})
                """, action_name=action_name, rule_name=rule["name"], rule_type=rule_type)

                # Создаем узел Condition с полным набором свойств
                condition_properties = {k: v for k, v in conditions.items() if v is not None}
                if condition_properties:  # Создаем только если есть свойства
                    # Генерация строк для MERGE и передачи параметров
                    condition_merge = "MERGE (condition:Condition {" + ", ".join(
                        [f"{key}: ${key}" for key in condition_properties.keys()]
                    ) + "})"

                    # Выполнение запроса с передачей параметров
                    session.run(condition_merge, **condition_properties)

                    # Связываем правило с этим условием
                    condition_match = "MATCH (condition:Condition {" + ", ".join(
                        [f"{key}: ${key}" for key in condition_properties.keys()]
                    ) + "})"
                    session.run(f"""
                    MATCH (rule:Rule {{name: $rule_name}})
                    {condition_match}
                    MERGE (rule)-[:HAS_CONDITION]->(condition)
                    """, rule_name=rule["name"], **condition_properties)

                # Связываем правило с действием
                session.run("""
                MATCH (rule:Rule {name: $rule_name})
                MATCH (action:Action {name: $action_name})
                MERGE (rule)-[:REQUIRES_ACTION]->(action)
                """, rule_name=rule["name"], action_name=action_name)

    def initialize_plant_types(self):
        """
        Инициализирует категории растений, соответствующие им растения и время роста в базе знаний.
        """
        with self.driver.session() as session:
            # Создание узлов категорий и растений
            for plant_type, data in PLANT_TYPES.items():
                growth_time_days = data["growth_time_days"]
                plants = data["plants"]

                # Создаем узел категории с временем роста
                session.run("""
                MERGE (category:Category {name: $plant_type})
                SET category.growth_time_days = $growth_time_days
                """, plant_type=plant_type, growth_time_days=growth_time_days)

                # Создаем узлы растений и связываем с категориями
                for plant in plants:
                    session.run("""
                    MERGE (plant:Plant {name: $plant_name})
                    MERGE (category:Category {name: $plant_type})
                    MERGE (plant)-[:BELONGS_TO]->(category)
                    """, plant_name=plant, plant_type=plant_type)

    def get_plant_info(self, plant_name):
        """
        Ищет информацию о растении по имени.
        :param plant_name: Название растения.
        :return: Словарь с информацией о растении или None, если растение не найдено.
        """
        with self.driver.session() as session:
            query = """
            MATCH (plant:Plant {name: $plant_name})
            OPTIONAL MATCH (plant)-[:BELONGS_TO]->(category:Category)
            RETURN plant.name AS name, 
                   category.name AS category,
                   category.growth_time_days AS growth_time_days
            """
            result = session.run(query, plant_name=plant_name).single()
            if result:
                return {
                    "name": result["name"],
                    "category": result["category"] or "Другие растения",
                    "growth_time_days": result["growth_time_days"] or 0  # Если время роста не указано
                }
            return None


PLANT_TYPES = {
    "Засухоустойчивые растения": {
        "plants": ["Кактус", "Алоэ", "Агавы"],
        "growth_time_days": 15
    },
    "Влаголюбивые растения": {
        "plants": ["Папоротник", "Калатея", "Маранта"],
        "growth_time_days": 13
    },
    "Растения с глубокими корнями": {
        "plants": ["Дуб", "Орех", "Каштан"],
        "growth_time_days": 20
    },
    "Плодоносящие растения": {
        "plants": ["Томат", "Огурец", "Перец"],
        "growth_time_days": 11
    },
    "Цветущие растения": {
        "plants": ["Роза", "Орхидея", "Лилия"],
        "growth_time_days": 7
    },
    "Тропические растения": {
        "plants": ["Банан", "Манго", "Ананас"],
        "growth_time_days": 25
    },
    "Листовые декоративные растения": {
        "plants": ["Фикус", "Драцена", "Монстера"],
        "growth_time_days": 18
    },
    "Другие растения": {
        "plants": [],
        "growth_time_days": 5  # По умолчанию
    }
}

WATERING_RULES = [
    {
        "name": "Полив влаголюбивых растений при средней влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Влаголюбивые растения",
            "temperature": None,
            "humidity_level": "Средняя",
            "time_of_day": None
        },
        "action": "Полив умеренный"
    },
    {
        "name": "Полив засухоустойчивых растений при низкой влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Засухоустойчивые растения",
            "temperature": None,
            "humidity_level": "Низкая",
            "time_of_day": None
        },
        "action": "Полив минимальный"
    },
    {
        "name": "Полив тропических растений при средней влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Тропические растения",
            "temperature": None,
            "humidity_level": "Средняя",
            "time_of_day": None
        },
        "action": "Полив сильный"
    },
    {
        "name": "Полив цветущих растений при низкой влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Цветущие растения",
            "temperature": None,
            "humidity_level": "Низкая",
            "time_of_day": None
        },
        "action": "Полив умеренный"
    },
    {
        "name": "Полив плодоносящих растений при низкой влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Плодоносящие растения",
            "temperature": None,
            "humidity_level": "Низкая",
            "time_of_day": None
        },
        "action": "Полив сильный"
    },
    {
        "name": "Полив листовых декоративных растений при низкой влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Листовые декоративные растения",
            "temperature": None,
            "humidity_level": "Низкая",
            "time_of_day": None
        },
        "action": "Полив минимальный"
    },
    {
        "name": "Полив растений с глубокими корнями при средней влажности",
        "type": "basic",
        "conditions": {
            "plant_type": "Растения с глубокими корнями",
            "temperature": None,
            "humidity_level": "Средняя",
            "time_of_day": None
        },
        "action": "Полив умеренный"
    },
    {
        "name": "Полив засухоустойчивых при жаре",
        "type": "advanced",
        "conditions": {
            "plant_type": "Засухоустойчивые растения",
            "temperature": "Высокая",
            "humidity_level": "Низкая",
            "time_of_day": "Утро"
        },
        "action": "Полив слабый"
    },
    {
        "name": "Полив засухоустойчивых при нормальной температуре",
        "type": "advanced",
        "conditions": {
            "plant_type": "Засухоустойчивые растения",
            "temperature": "Средняя",
            "humidity_level": "Низкая",
            "time_of_day": "Вечер"
        },
        "action": "Полив минимальный"
    },
    {
        "name": "Полив влаголюбивых растений при жаре",
        "type": "advanced",
        "conditions": {
            "plant_type": "Влаголюбивые растения",
            "temperature": "Высокая",
            "humidity_level": "Средняя",
            "time_of_day": "День"
        },
        "action": "Полив сильный"
    },
    {
        "name": "Полив влаголюбивых растений при нормальной температуре",
        "type": "advanced",
        "conditions": {
            "plant_type": "Влаголюбивые растения",
            "temperature": "Средняя",
            "humidity_level": "Средняя",
            "time_of_day": "Вечер"
        },
        "action": "Полив умеренный"
    },
    {
        "name": "Полив цветущих растений утром при низкой влажности",
        "type": "advanced",
        "conditions": {
            "plant_type": "Цветущие растения",
            "temperature": "Средняя",
            "humidity_level": "Низкая",
            "time_of_day": "Утро"
        },
        "action": "Полив умеренный"
    },
    {
        "name": "Полив плодоносящих растений при высокой температуре",
        "type": "advanced",
        "conditions": {
            "plant_type": "Плодоносящие растения",
            "temperature": "Высокая",
            "humidity_level": "Низкая",
            "time_of_day": "Утро"
        },
        "action": "Полив сильный"
    },
    {
        "name": "Полив тропических растений в жару днем",
        "type": "advanced",
        "conditions": {
            "plant_type": "Тропические растения",
            "temperature": "Высокая",
            "humidity_level": "Средняя",
            "time_of_day": "День"
        },
        "action": "Полив очень сильный"
    },
    {
        "name": "Полив тропических растений вечером при средней температуре",
        "type": "advanced",
        "conditions": {
            "plant_type": "Тропические растения",
            "temperature": "Средняя",
            "humidity_level": "Средняя",
            "time_of_day": "Вечер"
        },
        "action": "Полив сильный"
    },
    {
        "name": "Полив растений с глубокими корнями утром при низкой влажности",
        "type": "advanced",
        "conditions": {
            "plant_type": "Растения с глубокими корнями",
            "temperature": "Средняя",
            "humidity_level": "Средняя",
            "time_of_day": "Утро"
        },
        "action": "Полив умеренный"
    },
    {
        "name": "Полив листовых декоративных растений вечером при низкой влажности",
        "type": "advanced",
        "conditions": {
            "plant_type": "Листовые декоративные растения",
            "temperature": "Низкая",
            "humidity_level": "Низкая",
            "time_of_day": "Вечер"
        },
        "action": "Полив минимальный"
    }
]
