import pytest
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import requests

@pytest.fixture
def driver():
    """
    Фикстура для инициализации Selenium WebDriver.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ru")
    options.add_argument("--accept-lang=ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    yield driver
    driver.quit()

import pytest
import mysql.connector


@pytest.fixture(scope="function")
def db_connection():
    """Фикстура: подключение к БД + очистка перед тестом"""
    conn = None
    try:
        conn = mysql.connector.connect(
            host='localhost',
            port=3306,
            database='app',
            user='app',
            password='pass'
        )
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payment_entity;")
        cursor.execute("DELETE FROM order_entity;")
        cursor.execute("DELETE FROM credit_request_entity;")
        conn.commit()
        cursor.close()
    except Exception as e:
        pytest.fail(f"Ошибка подключения к БД: {e}")
        if conn and conn.is_connected():
            conn.close()
        raise

    yield conn

    if conn and conn.is_connected():
        conn.close()
