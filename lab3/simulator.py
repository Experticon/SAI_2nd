from greenhouse import Greenhouse
from knowledge_base import Neo4jDB, PLANT_TYPES

uri = "neo4j+s://ef635998.databases.neo4j.io"
user = "neo4j"
password = "yh1CJiDIRo0njrAyEQWd9MEEzpGcGTFMnRHP2GZf7Fs"

def main():
    # Инициализация базы знаний
    db = Neo4jDB(uri, user, password)
    # db.setup_ontology_and_rules()
    # db.initialize_plant_types()

    # Ввод пользователя: названия растений через пробел
    print("Введите названия растений через пробел:")
    plant_names = input().split()

    # Инициализация теплицы
    greenhouse = Greenhouse(db, plant_names)

    # Запуск симуляции
    greenhouse.run_simulation()

if __name__ == "__main__":
    main()
