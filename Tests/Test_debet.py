from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import Data
import use_functions


def test_payment_approved(driver):
    wait = WebDriverWait(driver, 10)
    use_functions.fill_form(driver, 'Купить')
    # Проверяем, что появилось сообщение об успехе
    success_message = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//div[text() =  'Успешно']"))
    )
    approval_message = wait.until(
        EC.visibility_of_element_located((By.XPATH, "//div[normalize-space() = 'Операция одобрена Банком.']"))
    )

    assert success_message.text == 'Успешно'
    assert approval_message.text == 'Операция одобрена Банком.'


    print('Тест пройден: оплата одобрена, ошибок нет')

def test_field_error_invalid_format(driver):
    driver.get('http://localhost:8080/')
    wait = WebDriverWait(driver, 10)

    buy_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space() = 'Купить']")))
    buy_button.click()

    card_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="0000 0000 0000 0000"]')))
    card_input.send_keys(Data.invalid_data[1])

    continue_button = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(normalize-space(), 'Продолжить')]")))
    continue_button.click()

    error_message = wait.until(EC.visibility_of_element_located((By.XPATH, '//span[@class="input__sub"]')))
    errors_message = wait.until(EC.visibility_of_all_elements_located((By.XPATH, '//span[@class="input__sub"]')))
    assert error_message.text == 'Неверный формат', (
        f"Ожидалось 'Неверный формат', получено: '{error_message.text}'")
