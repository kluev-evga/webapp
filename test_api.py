import io
import json
from contextlib import nullcontext as does_not_raise
from datetime import datetime

import httpx
import pytest
import qrcode
from faker import Faker
from faker.providers import date_time

fake = Faker()
fake.add_provider(date_time)


async def send_data(payload):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(payload))
    qr.make(fit=True)

    img_path = "body.jpg"
    qr.make_image(fill_color="black", back_color="white").save(img_path)

    img_buffer = io.BytesIO()
    with open(img_path, "rb") as img_file:
        img_buffer.write(img_file.read())
    img_buffer.seek(0)

    async with httpx.AsyncClient() as client:
        files = {"file": ("body.jpg", img_buffer, "image/jpeg")}
        response = await client.post("http://localhost:8000/get_form", files=files)

    return response


@pytest.mark.asyncio
async def test_valid_date():
    valid_date = datetime.now().strftime("%Y-%m-%d")
    fake_data = {"date_field": valid_date}
    response = await send_data(fake_data)
    assert response.status_code == 200
    assert response.json() == {"date_field": "date"}


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_date", [
    "2022-01-01 12:30:45",  # с временем
    "01-01-2022",  # неверный порядок
    "2022-13-01",  # некорректный месяц
    "2022-01-32",  # некорректный день
    "2022/01/01",  # другой разделитель
])
async def test_invalid_date(invalid_date):
    fake_data = {"invalid_date": invalid_date}
    response = await send_data(fake_data)
    assert response.status_code == 200
    assert response.json() == {"invalid_date": "text"}


@pytest.mark.asyncio
@pytest.mark.parametrize("valid_email", [
    "user@example.com",
    "john.doe@example.co.uk",
])
async def test_valid_email(valid_email):
    fake_data = {"email_field": valid_email}
    response = await send_data(fake_data)
    assert response.status_code == 200
    assert response.json() == {"email_field": "email"}


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_email", [
    "alice.smith@example",  # нет ru/com ...
    "invalid.email.com",  # нет @
    "user@.com",  # нет домена
    "@example.com",  # нет имени
])
async def test_invalid_email(invalid_email):
    fake_data = {"email_field": invalid_email}
    response = await send_data(fake_data)
    assert response.status_code == 200
    assert response.json() == {"email_field": "text"}


@pytest.mark.asyncio
async def test_valid_phone_number():
    fake_data = {"phone_field": "+7 123 456 78 90"}
    response = await send_data(fake_data)
    assert response.status_code == 200
    assert response.json() == {"phone_field": "phone"}


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_phone_number", [
    "+7 123",  # Неполные цифры
    "+7 123 456",  # Неполные цифры
    "+7 123 456 789",  # Лишние цифры
    "+7 12 345 678 90",  # Лишние цифры
    "+7 123-456-78-90",  # тире
    "+7 (123) 456-7890",  # Скобки
])
async def test_invalid_phone_number(invalid_phone_number):
    fake_data = {"phone_field": invalid_phone_number}
    response = await send_data(fake_data)
    assert response.status_code == 200
    assert response.json() == {"phone_field": "text"}


def generate_fake_data(form_item):
    data = {}
    for field_name, field_type in form_item.items():
        if field_type == "email":
            fake_value = fake.email()
        elif field_type == "phone":
            fake_value = '+7 ' + ''.join(
                str(num) if i not in (2, 5, 7) else str(num) + ' '
                for i, num in enumerate([fake.random_int(0, 9)] * 10)
            )
        elif field_type == "date":
            fake_value = fake.date_this_decade()
        else:
            fake_value = fake.word()
        data[field_name] = fake_value
    return data


@pytest.mark.asyncio
@pytest.mark.parametrize("form_name, test_data, expectation", [
    # форма 1
    ("star", {"account": "email", "whether": "email", "remain": "email", "billion": "email"}, does_not_raise()),
    # форма 1, больше полей, чем в форме:
    ("star", {"account": "email", "whether": "email", "remain": "email", "billion": "email", "gazilion": "text"}, does_not_raise()),
    # форма 1 - меньше полей == не подходит:
    ("star", {"account": "email", "whether": "email", "remain": "email"}, pytest.raises(AssertionError)),
    # форма 2
    ("space", {"adult": "phone", "story": "email", "half": "email"}, does_not_raise()),
])
async def test_get_form_name(test_data, form_name, expectation):
    fake_data = generate_fake_data(test_data)
    response = await send_data(fake_data)
    with expectation:
        assert response.status_code == 200
        assert response.json() == {"template_name": form_name}
