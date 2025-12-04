import pytest
import mysql.connector
from selenium import webdriver

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)
    yield driver
    driver.quit()


@pytest.fixture(scope="function")
def db_connection():
    # Подключаемся к БД
    conn = mysql.connector.connect(
        host='localhost',
        port=3306,
        database='app',
        user='app',
        password='pass'
    )

    cursor = conn.cursor()
    cursor.execute("DELETE FROM payment_entity;")
    conn.commit()
    cursor.close()

    yield conn
    conn.close()


