from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest
import allure
from selenium.common.exceptions import TimeoutException
from itertools import product
import json
from datetime import datetime
import re

import Data
import use_functions


@pytest.mark.parametrize("button_text", Data.button_texts)
@allure.feature("UI")
@allure.story("Успешная оплата по карте")
@allure.severity(allure.severity_level.CRITICAL)
def test_payment_approved(driver, button_text):
    wait = WebDriverWait(driver, 15)
    with allure.step("Открываем страницу приложения и заполняем форму валидными данными"):
        use_functions.fill_form(driver, button_text, Data.valid_data)
        allure.attach(
            json.dumps(Data.valid_data, ensure_ascii=False, indent=2),
            name="Тело формы",
            attachment_type=allure.attachment_type.JSON
        )
    with allure.step("Ожидаем подтверждение успеха от банка"):
        try:
            success_message = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[normalize-space()='Операция одобрена Банком.']"))
            )
            assert success_message.is_displayed(), "Сообщение об успехе не отображается"
            allure.attach(success_message.text, name="Текст подтверждения", attachment_type=allure.attachment_type.TEXT)
        except TimeoutException:
            with allure.step("Скриншот при ошибке"):
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="Состояние страницы",
                    attachment_type=allure.attachment_type.PNG
                )
            pytest.fail("Не дождались сообщения 'Операция одобрена Банком.'")

    with allure.step("Проверяем отсутствие сообщения об ошибке"):
        try:
            error_element = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[normalize-space()='Ошибка! Банк отказал в проведении операции.']"))
            )
            assert not error_element.is_displayed(), "Ошибка отобразилась, но не должна"
        except TimeoutException:
            pass

    allure.title(f"Успешная оплата через '{button_text}'")


@pytest.mark.parametrize("button_text", Data.button_texts)
@allure.feature("UI")
@allure.story("Отклоненная оплата по карте")
@allure.severity(allure.severity_level.CRITICAL)
def test_payment_declined(driver, button_text):
    wait = WebDriverWait(driver, 15)

    with allure.step("Открываем страницу приложения и заполняем форму невалидными данными"):
        use_functions.fill_form(driver, button_text, Data.invalid_data)
        allure.attach(
            json.dumps(Data.invalid_data, ensure_ascii=False, indent=2),
            name="Тело формы",
            attachment_type=allure.attachment_type.JSON
        )

    with allure.step("Проверяем отсутствие сообщения об успехе"):
        try:
            success_message = wait.until(
                EC.visibility_of_element_located((By.XPATH, "//div[normalize-space()='Операция одобрена Банком.']"))
            )
            with allure.step("Скриншот при ошибке"):
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="Состояние страницы",
                    attachment_type=allure.attachment_type.PNG
                )
            pytest.fail(
                f"Для кнопки '{button_text}': сообщение об успешной оплате отобразилось, но должно быть отклонено")
        except TimeoutException:
            pass

    with allure.step("Ожидаем сообщение об ошибке от банка"):
        try:
            error_message = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[normalize-space()='Ошибка! Банк отказал в проведении операции.']"))
            )
            assert error_message.is_displayed(), "Сообщение об ошибке не отображается"
            allure.attach(error_message.text, name="Текст ошибки", attachment_type=allure.attachment_type.TEXT)
        except TimeoutException:
            with allure.step("Скриншот при ошибке"):
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="Состояние страницы",
                    attachment_type=allure.attachment_type.PNG
                )
            pytest.fail("Сообщение об ошибке 'Ошибка! Банк отказал в проведении операции.' не появилось")

    allure.title(f"Отклонённая оплата через '{button_text}'")


@pytest.mark.parametrize(
    "test_card_number_error,button_text",
    list(product(Data.test_card_number, Data.button_texts)))
@allure.feature("UI")
@allure.story("Валидация поля 'Номер карты'")
@allure.severity(allure.severity_level.NORMAL)
def test_card_number_invalid(driver, button_text, test_card_number_error):
    cleaned_number = test_card_number_error.replace(" ", "")
    card_num = len(cleaned_number)

    if test_card_number_error.replace(" ", "").isdigit() and card_num == 16:
        pytest.skip(f"Пропуск валидного номера карты: {test_card_number_error}")

    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    with allure.step("Нажимаем кнопку 'Купить'"):
        buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Купить']")))
        buy_button.click()

    with allure.step("Ожидаем появления полей ввода"):
        fields = wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
        )

    card_input = fields[0]
    card_input.clear()

    with allure.step(f"Вводим неверный номер карты: '{test_card_number_error}'"):
        if card_num > 16:
            driver.execute_script("arguments[0].value = arguments[1];", card_input, test_card_number_error)
        else:
            card_input.send_keys(test_card_number_error)

    with allure.step("Заполняем остальные поля валидными данными"):
        for i in range(1, len(fields)):
            if i < len(Data.valid_data):
                fields[i].clear()
                fields[i].send_keys(Data.valid_data[i])

    with allure.step("Нажимаем кнопку 'Продолжить'"):
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
        )
        continue_button.click()

    with allure.step("Ожидаем появление сообщения об ошибке"):
        try:
            card_number_field = wait.until(
                lambda _: card_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']")
            )
            error_message = card_number_field.find_element(By.XPATH, ".//span[@class='input__sub']")
            assert error_message.is_displayed(), "Сообщение об ошибке не отображается"
        except TimeoutException:
            with allure.step("Скриншот при ошибке"):
                allure.attach(
                    driver.get_screenshot_as_png(),
                    name="Состояние страницы",
                    attachment_type=allure.attachment_type.PNG
                )
            pytest.fail("Не появилось сообщение об ошибке в поле 'Номер карты'")

    with allure.step("Проверяем текст ошибки"):
        expected = "Поле обязательно для заполнения" if test_card_number_error == "" else "Неверный формат"
        actual = error_message.text.strip()
        assert actual == expected, f"Ожидалось '{expected}', получено: '{actual}'"
        allure.attach(f"Ожидалось: {expected}\nФактически: {actual}", name="Сравнение", attachment_type=allure.attachment_type.TEXT)

    allure.title(f"Неверный номер карты: '{test_card_number_error}' → '{expected}'")


@pytest.mark.parametrize(
    "test_month_errors, button_text",
    list(product(Data.test_month_errors, Data.button_texts)))
@allure.feature("UI")
@allure.story("Валидация поля 'Месяц'")
@allure.severity(allure.severity_level.NORMAL)
def test_fields_month_error(driver, test_month_errors, button_text):
    if test_month_errors.isdigit() and 1 <= int(test_month_errors) <= 12:
        pytest.skip(f"Пропуск валидного месяца: {test_month_errors}")
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    with allure.step(f"Нажимаем кнопку '{button_text}'"):
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{button_text}']"))
        )
        submit_button.click()

    with allure.step("Ожидаем появления полей ввода"):
        fields = wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
        )

    with allure.step("Заполняем все поля, кроме 'Месяц'"):
        for i in range(len(fields)):
            if i < len(Data.valid_data) and i != 1:
                fields[i].clear()
                fields[i].send_keys(Data.valid_data[i])

    month_field_input = fields[1]
    month_field_input.clear()

    with allure.step(f"Вводим в поле 'Месяц': '{test_month_errors}'"):
        if len(test_month_errors) > 2:
            driver.execute_script("arguments[0].value = arguments[1];", month_field_input, test_month_errors)
        else:
            month_field_input.send_keys(test_month_errors)

    with allure.step("Нажимаем 'Продолжить'"):
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
        )
        continue_button.click()

    with allure.step("Проверяем сообщение об ошибке"):
        month_container = wait.until(
            lambda _: month_field_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']")
        )
        error_message = wait.until(
            lambda _: month_container.find_element(By.XPATH, ".//span[@class='input__sub']")
        )
        assert error_message.is_displayed(), "Сообщение об ошибке не отображается"

    expected = None
    if test_month_errors == "":
        expected = "Поле обязательно для заполнения"
    elif not test_month_errors.isdigit():
        expected = "Неверный формат"
    else:
        month_val = int(test_month_errors)
        if month_val < 1 or 12 < month_val <= 99:
            expected = "Неверно указан срок действия карты"
        else:
            expected = "Неверный формат"

    if expected:
        actual = error_message.text.strip()
        assert actual == expected, f"Ожидалось '{expected}', получено: '{actual}'"
        allure.attach(f"Ожидалось: {expected}\nФактически: {actual}", name="Сравнение", attachment_type=allure.attachment_type.TEXT)

    allure.title(f"Месяц '{test_month_errors}' → '{expected}'")


@pytest.mark.parametrize(
    "test_year_errors, button_text",
    list(product(Data.test_year_errors, Data.button_texts)))
@allure.feature("UI")
@allure.story("Валидация поля 'Год'")
@allure.severity(allure.severity_level.NORMAL)
def test_fields_year_error(driver, button_text, test_year_errors):
    current_year = int(datetime.now().strftime("%y"))
    if test_year_errors.isdigit() and current_year <= int(test_year_errors) <= current_year + 5:
        pytest.skip(f"Валидный год: {test_year_errors}")
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    with allure.step(f"Нажимаем кнопку '{button_text}'"):
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{button_text}']"))
        )
        submit_button.click()

    with allure.step("Ожидаем появления полей ввода"):
        fields = wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
        )

    with allure.step("Заполняем все поля, кроме 'Год'"):
        for i in range(len(fields)):
            if i < len(Data.valid_data) and i != 2:
                fields[i].clear()
                fields[i].send_keys(Data.valid_data[i])

    year_field_input = fields[2]
    year_field_input.clear()

    with allure.step(f"Вводим в поле 'Год': '{test_year_errors}'"):
        if len(test_year_errors) > 2:
            driver.execute_script("arguments[0].value = arguments[1];", year_field_input, test_year_errors)
        else:
            year_field_input.send_keys(test_year_errors)

    with allure.step("Нажимаем 'Продолжить'"):
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
        )
        continue_button.click()

    with allure.step("Проверяем сообщение об ошибке"):
        year_container = wait.until(
            lambda _: year_field_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']")
        )
        error_message = wait.until(
            lambda _: year_container.find_element(By.XPATH, ".//span[@class='input__sub']")
        )
        assert error_message.is_displayed(), "Сообщение об ошибке не отображается"

    if test_year_errors == "":
        expected = "Поле обязательно для заполнения"
    elif not test_year_errors.isdigit():
        expected = "Неверный формат"
    elif len(test_year_errors) != 2:
        expected = "Неверный формат"
    else:
        test_year_int = int(test_year_errors)
        if test_year_int < current_year:
            expected = "Истёк срок действия карты"
        elif test_year_int > current_year + 5:
            expected = "Неверно указан срок действия карты"
        else:
            expected = None

    if expected:
        actual = error_message.text.strip()
        assert actual == expected, f"Ожидалось '{expected}', получено: '{actual}'"
        allure.attach(f"Ожидалось: {expected}\nФактически: {actual}", name="Сравнение", attachment_type=allure.attachment_type.TEXT)

    allure.title(f"Год '{test_year_errors}' → '{expected}'")

@pytest.mark.parametrize(
    "test_owner_errors, button_text",
    list(product(Data.test_owner_errors, Data.button_texts)))
@allure.feature("UI")
@allure.story("Валидация поля 'Владелец'")
@allure.severity(allure.severity_level.NORMAL)
def test_fields_owner_error(driver, button_text, test_owner_errors):
    if re.fullmatch(r'[a-zA-Z ]+', test_owner_errors) and 2 <= len(test_owner_errors.strip()) <= 50:
        pytest.skip(f"Валидный владелец: '{test_owner_errors}'")
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    with allure.step(f"Нажимаем кнопку '{button_text}'"):
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{button_text}']"))
        )
        submit_button.click()

    with allure.step("Ожидаем появления полей ввода"):
        fields = wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
        )

    with allure.step("Заполняем все поля, кроме 'Владелец'"):
        for i in range(len(fields)):
            if i < len(Data.valid_data) and i != 3:
                fields[i].clear()
                fields[i].send_keys(Data.valid_data[i])

    owner_field_input = fields[3]
    owner_field_input.clear()
    owner_field_input.send_keys(test_owner_errors)

    with allure.step("Нажимаем 'Продолжить'"):
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
        )
        continue_button.click()

    with allure.step("Проверяем сообщение об ошибке"):
        owner_container = wait.until(
            lambda _: owner_field_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']")
        )
        error_message = wait.until(
            lambda _: owner_container.find_element(By.XPATH, ".//span[@class='input__sub']")
        )
        assert error_message.is_displayed(), "Сообщение об ошибке не отображается"

    if test_owner_errors == "":
        expected = "Поле обязательно для заполнения"
    else:
        expected = "Неверный формат"

    actual = error_message.text.strip()
    assert actual == expected, f"Ожидалось '{expected}', получено: '{actual}'"
    allure.attach(f"Ожидалось: {expected}\nФактически: {actual}", name="Сравнение", attachment_type=allure.attachment_type.TEXT)

    allure.title(f"Владелец '{test_owner_errors}' → '{expected}'")


@pytest.mark.parametrize(
    "test_cvv_errors, button_text",
    list(product(Data.test_cvv_errors, Data.button_texts)))
@allure.feature("UI")
@allure.story("Валидация полей")
@allure.severity(allure.severity_level.NORMAL)
def test_fields_cvv_error(driver, button_text, test_cvv_errors):
    if test_cvv_errors.isdigit() and len(test_cvv_errors) == 3:
        pytest.skip(f"Валидный CVV: {test_cvv_errors}")
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    with allure.step(f"Нажимаем кнопку '{button_text}'"):
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{button_text}']"))
        )
        submit_button.click()

    with allure.step("Ожидаем появления полей ввода"):
        fields = wait.until(
            EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
        )

    with allure.step("Заполняем все поля, кроме 'CVV'"):
        for i in range(len(fields)):
            if i < len(Data.valid_data) and i != 4:
                fields[i].clear()
                fields[i].send_keys(Data.valid_data[i])

    cvv_field_input = fields[4]
    cvv_field_input.clear()

    with allure.step(f"Вводим в поле 'CVV': '{test_cvv_errors}'"):
        if len(test_cvv_errors) > 3:
            driver.execute_script("arguments[0].value = arguments[1];", cvv_field_input, test_cvv_errors)
        else:
            cvv_field_input.send_keys(test_cvv_errors)

    with allure.step("Нажимаем 'Продолжить'"):
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
        )
        continue_button.click()

    with allure.step("Проверяем сообщение об ошибке"):
        cvv_container = wait.until(
            lambda _: cvv_field_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']")
        )
        error_message = wait.until(
            lambda _: cvv_container.find_element(By.XPATH, ".//span[@class='input__sub']")
        )
        assert error_message.is_displayed(), "Сообщение об ошибке не отображается"

    if test_cvv_errors == "":
        expected = "Поле обязательно для заполнения"
    elif not test_cvv_errors.isdigit():
        expected = "Неверный формат"
    elif len(test_cvv_errors) != 3:
        expected = "Неверный формат"
    else:
        expected = None

    if expected:
        actual = error_message.text.strip()
        assert actual == expected, f"Ожидалось '{expected}', получено: '{actual}'"
        allure.attach(f"Ожидалось: {expected}\nФактически: {actual}", name="Сравнение", attachment_type=allure.attachment_type.TEXT)

    allure.title(f"CVV '{test_cvv_errors}' → '{expected}'")