from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest
from datetime import datetime
from selenium.common.exceptions import TimeoutException

import Data
import use_functions

# Тест успешной оплаты
def test_payment_approved(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(Data.url)

    use_functions.fill_form(driver, 'Купить в кредит', Data.valid_data)

    success_message = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//div[normalize-space()='Операция одобрена Банком.']"))
    )
    assert success_message.is_displayed(), 'Сообщение об успешной операции не отображается'

    try:
        error_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[normalize-space()='Ошибка! Банк отказал в проведении операции.']"))
        )
        assert not error_element.is_displayed(), "Сообщение об ошибке отображается, но должно быть скрыто"
    except:
        pass

    print("Тест пройден: оплата одобрена, ошибок нет")

# Тест отказа в оплате
def test_payment_declined(driver):
    wait = WebDriverWait(driver, 10)
    driver.get(Data.url)

    # Заполняем форму с данными, при которых оплата отклоняется
    use_functions.fill_form(driver, 'Купить в кредит', Data.invalid_data)

    # Ожидаем сообщение об ошибке
    error_message = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//div[normalize-space()='Ошибка! Банк отказал в проведении операции.']"))
    )
    assert error_message.is_displayed(), 'Сообщение об ошибке не отображается'

    # Проверяем, что сообщение об успехе НЕ появилось
    try:
        success_message = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.XPATH, "//div[normalize-space()='Операция одобрена Банком.']"))
        )
        assert False, "Сообщение об успешной оплате отобразилось, но должно быть скрыто"
    except TimeoutException:
        pass

    print("Тест пройден: оплата отклонена, подтверждение об успехе отсутствует")

# Тест значений в поле номера карты вызывающих ошибку
@pytest.mark.parametrize("test_card_number, expected_error_number_card", [
    ("", "Поле обязательно для заполнения"),
    ("4444 4444 4444 444", "Неверный формат"),
    ("4444 4444 4444 44444","Неверный формат"),
    ("!@#$ %^&* @!#% @!$%", "Неверный формат"),
    ("aaaa aaaa aaaa aaaa", "Неверный формат"),
])
def test_card_number_invalid(driver, test_card_number,expected_error_number_card):
    wait = WebDriverWait(driver, 10)
    driver.get(Data.url)

    # Открываем форму
    buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Купить в кредит']")))
    buy_button.click()

    # Ждём появления всех полей
    fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )

    # Заполняем номер карты
    card_input = fields[0]
    fields[0].clear()
    fields[0].send_keys(test_card_number)

    # Заполняем остальные поля
    for i in range(1, len(fields)):
        if i < len(Data.valid_data):
            fields[i].clear()
            fields[i].send_keys(Data.valid_data[i])

        # Нажимаем "Продолжить"
        continue_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
        )
        continue_button.click()

    # Находим контейнер поля "Месяц"
    card_number_field = wait.until(
        lambda _: card_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']"))

    # Ждём появление сообщения об ошибке
    error_message = wait.until(
        lambda _: card_number_field.find_element(By.XPATH, ".//span[@class='input__sub']"))

    assert error_message.is_displayed(), "Сообщение об ошибке не отображается"
    assert error_message.text.strip() == expected_error_number_card, \
        f"Ожидалось '{expected_error_number_card}', получено: '{error_message.text.strip()}'"

# Тест проверки появления ошибки при вводе неверного поля месяц
@pytest.mark.parametrize("test_month, expected_error_month", [
    ("", "Поле обязательно для заполнения"),
    ("00", "Неверно указан срок действия карты"),
    ("13", "Неверно указан срок действия карты"),
    ("Февраль", "Неверный формат"),
])
def test_fields_month_error(driver, test_month, expected_error_month):
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    # Открываем форму
    buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Купить в кредит']")))
    buy_button.click()


    # Ждём появления всех полей
    fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )

    # Заполняем номер карты
    fields[0].clear()
    fields[0].send_keys('4444 4444 4444 4441')

    # Заполняем месяц
    month_field_input = fields[1]
    month_field_input.clear()
    month_field_input.send_keys(test_month)

    # Заполняем остальные поля
    for i in range(2, len(fields)):
        if i < len(Data.valid_data):
            fields[i].clear()
            fields[i].send_keys(Data.valid_data[i])

    # Нажимаем "Продолжить"
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
    )
    continue_button.click()

    # Находим контейнер поля "Месяц"
    month_field = wait.until(
        lambda _: month_field_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']"))

    # Ждём появление сообщения об ошибке
    error_message = wait.until(
        lambda _: month_field.find_element(By.XPATH, ".//span[@class='input__sub']"))

    assert error_message.is_displayed(), "Сообщение об ошибке не отображается"
    assert error_message.text.strip() == expected_error_month, \
        f"Ожидалось '{expected_error_month}', получено: '{error_message.text.strip()}'"

# Тест проверки появления ошибки при вводе неверного поля год
@pytest.mark.parametrize("test_year_error", ["","31","24","Ab","311","!@","-1"])
def test_fields_year_error(driver, test_year_error):
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    # Открываем форму
    buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Купить в кредит']")))
    buy_button.click()


    # Ждём появления всех полей
    fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )

    # Заполняем год
    field_year_input = fields[2]
    field_year_input.clear()
    field_year_input.send_keys(test_year_error)

    # Заполняем поля месяц и номер карты
    data_field_year = Data.valid_data[0:2]
    for i in range(0, 2):
        if i < 2:
            fields[i].clear()
            fields[i].send_keys(data_field_year[i])


    # Заполняем остальные поля
    for i in range(3, len(fields)):
        if i < len(Data.valid_data):
            fields[i].clear()
            fields[i].send_keys(Data.valid_data[i])

    # Нажимаем "Продолжить"
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
    )
    continue_button.click()

    # Находим контейнер поля "Год"
    year_container = wait.until(
        lambda _: field_year_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']"))

    # Ждём появление сообщения об ошибке
    error_message = wait.until(
        lambda _: year_container.find_element(By.XPATH, ".//span[@class='input__sub']"))

    # Проверяем
    assert error_message.is_displayed(), "Сообщение об ошибке не отображается"

    current_year = int(datetime.now().strftime("%y"))

    if test_year_error == "":
        expected = "Поле обязательно для заполнения"
    elif test_year_error.isdigit():
        test_year_int = int(test_year_error)
        if test_year_int < current_year:
            expected = "Истёк срок действия карты"
        elif test_year_int > current_year + 5:
            expected = "Неверно указан срок действия карты"
        else:
            expected = None
    else:
        expected = "Неверный формат"

    # Для этого теста expected не должен быть None
    assert expected is not None, "Ожидалась ошибка, но год валиден"
    assert error_message.text.strip() == expected, \
        f"Ожидалось '{expected}', получено: '{error_message.text.strip()}'"
# Тест проверки поля владелец
@pytest.mark.parametrize("test_owner, expected_error_owner", [
    ("", "Поле обязательно для заполнения"),
    ("Andrey123", "Неверный формат"),
    ("Andrey!!!!", "Неверный формат"),
    ("12345", "Неверный формат"),
    ("!@#$%^&*()_", "Неверный формат"),
    ("Андрей", "Неверный формат"),
])
def test_fields_owner_error(driver, test_owner, expected_error_owner):
    wait = WebDriverWait(driver, 10)
    driver.get(Data.url)

    # Открываем форму
    buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Купить в кредит']")))
    buy_button.click()

    # Ждём появления всех полей
    fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )

    # Заполняем поле владелец
    owner_field_input = fields[3]
    owner_field_input.clear()
    owner_field_input.send_keys(test_owner)

    # Заполняем поля: номер карты, месяц, год
    for i in range(0, 3):
        fields[i].clear()
        fields[i].send_keys(Data.valid_data[i])

    # Заполняем CVC (если есть)
    if len(fields) > 4:
        fields[4].clear()
        fields[4].send_keys(Data.valid_data[4])

    # Нажимаем "Продолжить"
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
    )
    continue_button.click()

    # Находим контейнер поля "Владелец"
    owner_container = wait.until(
        lambda _: owner_field_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']"))

    # Ждём появление сообщения об ошибке
    error_message = wait.until(
        lambda _: owner_container.find_element(By.XPATH, ".//span[@class='input__sub']"))


    # Проверяем
    assert error_message.is_displayed(), "Сообщение об ошибке не отображается"
    assert error_message.text.strip() == expected_error_owner, \
        f"Ожидалось '{expected_error_owner}', получено: '{error_message.text.strip()}'"


# Тест проверки CVV поля
@pytest.mark.parametrize("test_cvv, expected_error_cvv", [
    ("", "Поле обязательно для заполнения"),
    ("1", "Неверный формат"),
    ("12", "Неверный формат"),
    ("1234", "Неверный формат"),
])
def test_fields_cvv_error(driver, test_cvv, expected_error_cvv):
    wait = WebDriverWait(driver, 15)
    driver.get(Data.url)

    # Открываем форму
    buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Купить в кредит']")))
    buy_button.click()

    # Ждём появления всех полей
    fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )

    # Заполняем номер, месяц, год, владелец
    for i in range(0, 4):
        fields[i].clear()
        fields[i].send_keys(Data.valid_data[i])

    # Заполняем CVV
    cvv_input = fields[4]
    cvv_input.clear()
    cvv_input.send_keys(test_cvv)

    # Нажимаем "Продолжить"
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
    )
    continue_button.click()

    # Находим контейнер поля "CVV"
    cvv_container = wait.until(
        lambda _: cvv_input.find_element(By.XPATH, "./ancestor::span[@class='input__inner']"))


    # Ждём появление сообщения об ошибке
    error_message = wait.until(
        lambda _: cvv_container.find_element(By.XPATH, ".//span[@class='input__sub']"))

    # Проверяем
    assert error_message.is_displayed(), "Сообщение об ошибке не отображается"
    assert error_message.text.strip() == expected_error_cvv, \
        f"Ожидалось '{expected_error_cvv}', получено: '{error_message.text.strip()}'"



