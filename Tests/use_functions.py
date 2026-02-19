from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import Data

def fill_form(driver, button_text, t_data):
    wait = WebDriverWait(driver, 10)
    driver.get(Data.url)

    # Нажимаем кнопку открытия формы
    submit_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{button_text}']"))
    )
    submit_button.click()

    # Ждём появления полей ввода
    fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )
    # Заполняем поля данными из Data.py
    for i, field in enumerate(fields):
        if i < len(t_data):
            field.clear()
            field.send_keys(t_data[i])

    # Нажимаем «Продолжить»
    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
    )
    continue_button.click()


