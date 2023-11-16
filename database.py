from faker import Faker
from faker.providers import date_time
from tinydb import TinyDB

db = TinyDB('forms_db.json')
templates_table = db.table('templates')

Faker.seed(1234)
fake = Faker()
fake.add_provider(date_time)


def generate_form_item():
    form = {"name": fake.word()}
    for i in range(fake.random_int(min=1, max=5)):
        form[fake.word()] = fake.random_element(["email", "phone", "date", "text"])
    return form


def create_db(count=10):
    existing_data = templates_table.all()
    if not existing_data:
        for _ in range(count):
            form_item = generate_form_item()
            templates_table.insert(form_item)
