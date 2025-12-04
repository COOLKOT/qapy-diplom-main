from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import Data


def fill_form(driver, button_text):
    wait = WebDriverWait(driver, 10)
    driver.get(Data.url)

    submit_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{button_text}']"))
    )
    submit_button.click()

    input_fields = wait.until(
        EC.visibility_of_all_elements_located((By.XPATH, '//input[@class="input__control"]'))
    )

    for field, value in zip(input_fields, Data.valid_data):
        field.clear()
        field.send_keys(value)

    continue_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Продолжить')]"))
    )
    continue_button.click()










