import pytest
import allure
from selenium.webdriver.support.ui import WebDriverWait
import time
from datetime import datetime
import json

import use_functions
import Data


def attach_db_query_result(query: str, result, name: str = "Результат SQL-запроса"):
    if result:
        try:
            formatted_result = json.dumps(
                [{k: str(v) if isinstance(v, (datetime,)) else v for k, v in row.items()} for row in result],
                ensure_ascii=False, indent=2)
        except Exception:
            formatted_result = str(result)
    else:
        formatted_result = "Пустой результат"

    allure.attach(
        formatted_result,
        name=name,
        attachment_type=allure.attachment_type.JSON
    )


def execute_query(db_connection, query, params=None):
    cursor = db_connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        pytest.fail(f"Ошибка при выполнении запроса: {e}")
    finally:
        cursor.close()


def wait_for_db_record(db_connection, table, condition, timeout=15):  # Увеличили таймаут
    start_time = datetime.now()
    for i in range(timeout):
        result = execute_query(db_connection, f"SELECT * FROM {table} WHERE {condition} ORDER BY created DESC LIMIT 1")
        if result:
            elapsed = (datetime.now() - start_time).total_seconds()
            allure.attach(
                f"Запись найдена за {elapsed:.1f} секунд\nПопытка: {i + 1}",
                name="Время ожидания",
                attachment_type=allure.attachment_type.TEXT
            )
            return result[0]
        time.sleep(1)
    pytest.fail(f"Запись не появилась в {table} за {timeout} секунд. Условие: {condition}")



@allure.feature("База данных")
@allure.story("Сохранение успешного платежа")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("button_text", Data.button_texts)
def test_db_ui_payment_approved_stored(driver, db_connection, button_text):
    wait = WebDriverWait(driver, 10)
    with allure.step("Открываем страницу приложения и заполняем форму с невалидной картой"):
        allure.attach(driver.current_url, name="Текущий URL", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Заполняем форму валидными данными"):
        use_functions.fill_form(driver, button_text, Data.valid_data)
        allure.attach(
            json.dumps(Data.valid_data, ensure_ascii=False, indent=2),
            name="Тело формы",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Ожидаем сохранения данных в БД"):
        time.sleep(15)

    with allure.step("Проверяем наличие записи в БД"):
        if button_text == "Купить":
            payment = wait_for_db_record(db_connection, "payment_entity", "status = 'APPROVED'")
            attach_db_query_result(
                "SELECT * FROM payment_entity WHERE status = 'APPROVED' ORDER BY created DESC LIMIT 1", [payment],
                "Данные платежа")

            order = wait_for_db_record(db_connection, "order_entity", f"payment_id = '{payment['transaction_id']}'")
            attach_db_query_result("SELECT * FROM order_entity", [order], "Данные заказа")

            assert order is not None, "Связанный заказ не найден"
            allure.attach(f"transaction_id: {payment['transaction_id']}", name="ID платежа",
                          attachment_type=allure.attachment_type.TEXT)

        elif button_text == "Купить в кредит":
            credit = wait_for_db_record(db_connection, "credit_request_entity", "status = 'APPROVED'")
            attach_db_query_result(
                "SELECT * FROM credit_request_entity WHERE status = 'APPROVED' ORDER BY created DESC LIMIT 1", [credit],
                "Данные кредита")

            order = wait_for_db_record(db_connection, "order_entity", f"credit_id = '{credit['bank_id']}'")
            attach_db_query_result("SELECT * FROM order_entity", [order], "Данные заказа")

            assert order is not None, "Связанный заказ не найден"
            allure.attach(f"bank_id: {credit['bank_id']}", name="ID кредита",
                          attachment_type=allure.attachment_type.TEXT)
        else:
            pytest.fail(f"Неизвестная кнопка: {button_text}")

    with allure.step("Итоговая проверка"):
        if button_text == "Купить":
            payment_status = execute_query(db_connection, "SELECT status FROM payment_entity WHERE transaction_id = %s",
                                           [payment['transaction_id']])
            assert payment_status[0]['status'] == 'APPROVED', "Статус платежа не APPROVED"
        elif button_text == "Купить в кредит":
            credit_status = execute_query(db_connection, "SELECT status FROM credit_request_entity WHERE bank_id = %s",
                                          [credit['bank_id']])
            assert credit_status[0]['status'] == 'APPROVED', "Статус кредита не APPROVED"

    allure.title(f"Успешная оплата через '{button_text}' сохраняется в БД")


@allure.feature("База данных")
@allure.story("Сохранение отклонённого платежа")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("button_text", Data.button_texts)
def test_db_ui_payment_declined_stored(driver, db_connection, button_text):
    wait = WebDriverWait(driver, 10)
    with allure.step("Открываем страницу приложения и заполняем форму с невалидной картой"):
        use_functions.fill_form(driver, button_text, Data.invalid_data)

    with allure.step("Ожидаем сохранения в БД"):
        time.sleep(15)

    with allure.step("Проверяем наличие записи со статусом DECLINED"):
        if button_text == "Купить":
            payment = wait_for_db_record(db_connection, "payment_entity", "status = 'DECLINED'")
            attach_db_query_result("SELECT * FROM payment_entity WHERE status = 'DECLINED'", [payment],
                                   "Данные отклонённого платежа")

            order = wait_for_db_record(db_connection, "order_entity", f"payment_id = '{payment['transaction_id']}'")
            attach_db_query_result("SELECT * FROM order_entity", [order], "Данные заказа")

            assert order is not None, "Связанный заказ не найден"
            allure.attach(f"transaction_id: {payment['transaction_id']}", name="ID платежа",
                          attachment_type=allure.attachment_type.TEXT)

        elif button_text == "Купить в кредит":
            credit = wait_for_db_record(db_connection, "credit_request_entity", "status = 'DECLINED'")
            attach_db_query_result("SELECT * FROM credit_request_entity WHERE status = 'DECLINED'", [credit],
                                   "Данные отклонённого кредита")

            order = wait_for_db_record(db_connection, "order_entity", f"credit_id = '{credit['bank_id']}'")
            attach_db_query_result("SELECT * FROM order_entity", [order], "Данные заказа")

            assert order is not None, "Связанный заказ не найден"
            allure.attach(f"bank_id: {credit['bank_id']}", name="ID кредита",
                          attachment_type=allure.attachment_type.TEXT)
        else:
            pytest.fail(f"Неизвестная кнопка: {button_text}")

    allure.title(f"Отклонённая оплата через '{button_text}' сохраняется в БД")


@allure.feature("База данных")
@allure.story("Уникальность ID операций")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("button_text", Data.button_texts)
def test_db_ui_transaction_id_unique(driver, db_connection, button_text):
    wait = WebDriverWait(driver, 10)
    with allure.step("Открываем страницу приложения, заполняем форму валидными данными и отправляем две заявки"):
        ids = []
        for i in range(2):
            with allure.step(f"Платёж #{i + 1}"):
                use_functions.fill_form(driver, button_text, Data.valid_data)
                time.sleep(15)
                driver.refresh()

    with allure.step("Получаем последние две записи из БД"):
        if button_text == "Купить":
            query = "SELECT transaction_id, created FROM payment_entity WHERE status = 'APPROVED' ORDER BY created DESC LIMIT 2"
            payments = execute_query(db_connection, query)
            ids = [p["transaction_id"] for p in payments]
            attach_db_query_result(query, payments, "Последние два платежа")
        elif button_text == "Купить в кредит":
            query = "SELECT bank_id, created FROM credit_request_entity WHERE status = 'APPROVED' ORDER BY created DESC LIMIT 2"
            credits = execute_query(db_connection, query)
            ids = [c["bank_id"] for c in credits]
            attach_db_query_result(query, credits, "Последние два кредита")
        else:
            pytest.fail(f"Неизвестная кнопка: {button_text}")

    with allure.step("Проверяем уникальность ID"):
        assert len(ids) >= 2, "Не найдено двух платежей в БД"
        assert ids[0] != ids[1], f"Обнаружены дубликаты ID: {ids}"
        allure.attach(
            json.dumps({"ids": ids, "count": len(ids), "unique": len(set(ids))}, indent=2),
            name="Анализ ID",
            attachment_type=allure.attachment_type.JSON
        )

    allure.title(f"ID операций через '{button_text}' являются уникальными")


@allure.feature("База данных")
@allure.story("Корректность времени создания записи")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.parametrize("button_text", Data.button_texts)
def test_db_ui_created_timestamp_correct(driver, db_connection, button_text):
    with allure.step("Фиксируем время до отправки"):
        start_time = datetime.now()
        allure.attach(str(start_time), name="Время начала", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Открываем страницу приложения, заполняем форму валидными данными и отправляем две заявки"):
        use_functions.fill_form(driver, button_text, Data.valid_data)
        time.sleep(15)
        end_time = datetime.now()
        allure.attach(str(end_time), name="Время окончания", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Получаем запись из БД"):
        if button_text == "Купить":
            record = wait_for_db_record(db_connection, "payment_entity", "status = 'APPROVED'")
        elif button_text == "Купить в кредит":
            record = wait_for_db_record(db_connection, "credit_request_entity", "status = 'APPROVED'")
        else:
            pytest.fail(f"Неизвестная кнопка: {button_text}")

        created = record["created"]

    with allure.step("Проверяем корректность поля 'created'"):
        assert isinstance(created, datetime), f"Поле 'created' не является datetime: {type(created)}"

        time_diff = (end_time - created).total_seconds()
        assert 0 <= time_diff < 60, f"Время создания некорректно: отклонение {time_diff:.1f} сек"

        details = {
            "created": str(created),
            "start_time": str(start_time),
            "end_time": str(end_time),
            "time_diff_sec": time_diff,
            "within_acceptable_range": time_diff < 60,
            "not_in_future": time_diff >= 0
        }

        allure.attach(
            json.dumps(details, indent=2),
            name="Анализ временных меток",
            attachment_type=allure.attachment_type.JSON
        )

    allure.title(f"Время создания записи корректно для '{button_text}'")


@allure.feature("База данных")
@allure.story("Связь заказа с платёжом/кредитом")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.parametrize("button_text", Data.button_texts)
def test_db_order_payment_link_exists(driver, db_connection, button_text):
    with allure.step("Открываем страницу приложения, заполняем форму валидными данными и отправляем две заявки"):
        use_functions.fill_form(driver, button_text, Data.valid_data)
        time.sleep(15)

    with allure.step("Получаем последний заказ из БД"):
        order = wait_for_db_record(db_connection, "order_entity", "1=1")
        attach_db_query_result("SELECT * FROM order_entity ORDER BY created DESC LIMIT 1", [order], "Данные заказа")

    with allure.step("Проверяем ссылку на платёж/кредит"):
        if button_text == "Купить":
            assert order["payment_id"] is not None, "payment_id пустой"
            payment = execute_query(db_connection, "SELECT id, status FROM payment_entity WHERE transaction_id = %s",
                                    [order["payment_id"]])
            assert len(payment) == 1, f"Связанного платежа не существует. Найдено: {len(payment)}"
            attach_db_query_result("SELECT * FROM payment_entity", payment, "Связанный платёж")
            allure.attach(f"payment_id: {order['payment_id']}", name="ID платежа",
                          attachment_type=allure.attachment_type.TEXT)

        elif button_text == "Купить в кредит":
            assert order["credit_id"] is not None, "credit_id пустой"
            credit = execute_query(db_connection, "SELECT id, status FROM credit_request_entity WHERE bank_id = %s",
                                   [order["credit_id"]])
            assert len(credit) == 1, f"Связанного кредита не существует. Найдено: {len(credit)}"
            attach_db_query_result("SELECT * FROM credit_request_entity", credit, "Связанный кредит")
            allure.attach(f"credit_id: {order['credit_id']}", name="ID кредита",
                          attachment_type=allure.attachment_type.TEXT)
        else:
            pytest.fail(f"Неизвестная кнопка: {button_text}")

    with allure.step("Дополнительная валидация"):
        if button_text == "Купить":
            assert order["credit_id"] is None, "Для оплаты картой credit_id должен быть NULL"
            assert order["payment_id"] is not None, "Для оплаты картой payment_id должен быть заполнен"
        elif button_text == "Купить в кредит":
            assert order["payment_id"] is None, "Для кредита payment_id должен быть NULL"
            assert order["credit_id"] is not None, "Для кредита credit_id должен быть заполнен"

    allure.title(f"Связь заказа с платёжом/кредитом подтверждена для '{button_text}'")