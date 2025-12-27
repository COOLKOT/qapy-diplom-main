import pytest
import requests
from requests.exceptions import ConnectionError, Timeout
from datetime import datetime
import allure
from allure_commons.types import AttachmentType
import json


# --- URLs ---
url_payment = "http://localhost:9999/payment"
url_credit = "http://localhost:9999/credit"

# --- Валидные и невалидные данные ---
valid_data_card = {
    "number": "4444 4444 4444 4441",
    "year": "25",
    "month": "12",
    "holder": "Andrey",
    "cvc": "555"
}

invalid_data_card = {
    "number": "4444 4444 4444 4442",
    "year": "25",
    "month": "12",
    "holder": "Andrey",
    "cvc": "555"
}

invalid_body_request = {
    "number": "4444 4444 4444 4444",
    "year": "24",
    "month": "13",
    "holder": "",
    "cvc": "1-2"
}


def send_request(url, data):
    try:
        response = requests.post(url, json=data, timeout=10)
        return response
    except ConnectionError:
        pytest.fail("Не удалось подключиться к сервису")
    except Timeout:
        pytest.fail("Таймаут подключения к сервису")
    except Exception as e:
        pytest.fail(f"Неизвестная ошибка: {e}")

def attach_request_response(url, payload, response):
    if payload:
        allure.attach(
            json.dumps(payload, ensure_ascii=False, indent=2),
            name="Тело запроса",
            attachment_type=AttachmentType.JSON
        )
    if response:
        allure.attach(
            f"Status: {response.status_code}\n\n" + response.text,
            name="Ответ сервера",
            attachment_type=AttachmentType.TEXT
        )


# Отправка не-JSON
@allure.feature("API")
@allure.story("Формат данных")
@allure.title("Отправка не-JSON: статус 400 или 415")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_invalid_content_type(url):
    with allure.step("Отправка запроса с Content-Type: text/plain"):
        try:
            response = requests.post(url, data="not json", headers={"Content-Type": "text/plain"})
            assert response.status_code in [400, 415], f"Ожидался 400 или 415, получен {response.status_code}"
            attach_request_response(url, "not json", response)
        except Exception:
            pytest.fail("Ошибка при отправке не-JSON")


# Успешная оплата
@allure.feature("API")
@allure.story("Оплата по карте")
@allure.title("Успешная оплата: статус 200, APPROVED")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_payment_approved(url):
    with allure.step("Отправка валидных данных на платеж"):
        response = send_request(url, valid_data_card)
        data = response.json()
        assert response.status_code == 200
        assert data["status"] == "APPROVED"

        with allure.step("Операция оплаты"):
            operation = "кредита" if url == url_credit else "дебетовой карты"
            allure.attach(operation, name="Тип операции", attachment_type=AttachmentType.TEXT)

        attach_request_response(url, valid_data_card, response)


# Отклонённый платёж
@allure.feature("API")
@allure.story("Оплата по карте")
@allure.title("Отклонённый платёж: статус 200, DECLINED")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_payment_declined(url):
    with allure.step("Отправка данных с отклонённой картой"):
        response = send_request(url, invalid_data_card)
        data = response.json()
        assert response.status_code == 200
        assert data["status"] == "DECLINED"

        allure.dynamic.description(
            "Тест проверяет, что карта из чёрного списка (4444 4444 4444 4442) отклоняется системой."
        )

        attach_request_response(url, invalid_data_card, response)


# Некорректное тело запроса
@allure.feature("API")
@allure.story("Валидация запроса")
@allure.title("Некорректное тело запроса: статус 400")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_invalid_request_body(url):
    with allure.step("Отправка запроса с невалидным телом"):
        response = send_request(url, invalid_body_request)
        assert response.status_code == 400
        attach_request_response(url, invalid_body_request, response)


# Проверка валидации номера карты
@allure.feature("API")
@allure.story("Валидация номера карты")
@allure.title("Невалидная длина номера карты: статус 400")
@pytest.mark.parametrize("url", [url_payment, url_credit])
@pytest.mark.parametrize("card_number", [
    "4444 4444 4444 444",
    "4444 4444 4444 44444",
    "",
    "!@#$ !@#$ $#@! $%^&",
    "aaaa aaaa aaaa aaaa",
])
def test_invalid_card_number_length(url, card_number):
    with allure.step(f"Проверка номера карты: {card_number}"):
        payload = valid_data_card.copy()
        payload["number"] = card_number
        response = send_request(url, payload)
        assert response.status_code == 400
        attach_request_response(url, payload, response)

        # Добавляем категоризацию ошибки
        if len(card_number.replace(" ", "")) < 16:
            error_type = "Недостаточная длина"
        elif len(card_number.replace(" ", "")) > 16:
            error_type = "Избыточная длина"
        else:
            error_type = "Неверный формат"

        allure.attach(error_type, name="Тип ошибки", attachment_type=AttachmentType.TEXT)


# Пустое тело запроса
@allure.feature("API")
@allure.story("Валидация запроса")
@allure.title("Пустое тело запроса: статус 400")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_empty_request_body(url):
    with allure.step("Отправка пустого JSON-тела"):
        response = send_request(url, None)
        assert response.status_code == 400
        attach_request_response(url, None, response)


# Неверный формат владельца
@allure.feature("API")
@allure.story("Валидация владельца")
@allure.title("Невалидное имя владельца: ожидается DECLINED")
@pytest.mark.parametrize("url", [url_payment, url_credit])
@pytest.mark.parametrize("holder_value", [
    "Andrey123",
    "Andrey!!!!",
    "12345",
    "!@#$%^&*()_",
    "Андрей"
])
def test_invalid_holder(url, holder_value):
    with allure.step(f"Проверка владельца: {holder_value}"):
        payload = valid_data_card.copy()
        payload["holder"] = holder_value
        response = send_request(url, payload)
        data = response.json()
        assert response.status_code == 200
        assert data["status"] == "DECLINED"
        attach_request_response(url, payload, response)

        # Добавляем тип ошибки
        if not holder_value.isalpha():
            error_reason = "Содержит цифры или символы"
        elif not holder_value.isascii():
            error_reason = "Использует кириллицу"
        else:
            error_reason = "Неизвестно"

        allure.attach(error_reason, name="Причина отклонения", attachment_type=AttachmentType.TEXT)


# Просроченная карта
@allure.feature("API")
@allure.story("Валидация срока действия")
@allure.title("Просроченная карта: статус DECLINED")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_expired_card(url):
    with allure.step("Проверка карты с годом 24 (просрочена)"):
        payload = valid_data_card.copy()
        payload["year"] = "24"
        response = send_request(url, payload)
        data = response.json()
        assert response.status_code == 200
        assert data["status"] == "DECLINED"
        attach_request_response(url, payload, response)

        # Добавляем информацию о сроке
        current_year = datetime.now().strftime("%y")
        allure.attach(
            f"Текущий год: {current_year}, Год карты: 24 → просрочена",
            name="Анализ срока действия",
            attachment_type=AttachmentType.TEXT
        )


# Карта сроком более 5 лет
@allure.feature("API")
@allure.story("Валидация срока действия")
@allure.title("Карта более 5 лет: статус DECLINED")
@pytest.mark.parametrize("url", [url_payment, url_credit])
def test_expired_card_old(url):
    with allure.step("Проверка карты сроком >5 лет"):
        current_year = int(datetime.now().strftime("%y"))
        payload = valid_data_card.copy()
        payload["year"] = str(current_year + 6)
        response = send_request(url, payload)
        data = response.json()
        assert response.status_code == 200
        assert data["status"] == "DECLINED"
        attach_request_response(url, payload, response)

        allure.attach(
            f"Максимально допустимый год: {current_year + 5}, передан: {payload['year']} → отклонено",
            name="Проверка срока действия",
            attachment_type=AttachmentType.TEXT
        )


# Неверная длина CVC
@allure.feature("API")
@allure.story("Валидация CVC")
@allure.title("Неверная длина CVC: ожидается DECLINED")
@pytest.mark.parametrize("url", [url_payment, url_credit])
@pytest.mark.parametrize("cvc", ["", "1", "12", "1234"])
def test_invalid_cvc_length(url, cvc):
    with allure.step(f"Проверка CVC: {cvc}"):
        payload = valid_data_card.copy()
        payload["cvc"] = cvc
        response = send_request(url, payload)
        data = response.json()
        assert response.status_code == 200
        assert data["status"] == "DECLINED"
        attach_request_response(url, payload, response)

        # Уточняем тип ошибки
        if len(cvc) == 0:
            reason = "Пустое значение"
        elif len(cvc) < 3:
            reason = "Слишком короткий"
        else:
            reason = "Слишком длинный"

        allure.attach(reason, name="Причина ошибки", attachment_type=AttachmentType.TEXT)