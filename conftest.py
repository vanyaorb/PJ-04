# В этом файле есть возможность управления неудачными тестами и
# делать скриншоты после любого неудачного теста

import os
import pytest
import uuid
import allure
from selenium import webdriver

@pytest.fixture(scope="function")
def chrome_browser_instance(request):
    options = webdriver.ChromeOptions()
    browser = webdriver.Chrome(options=options)
    browser.maximize_window()
    yield browser
    log_file = os.path.join(os.getcwd(), "cookie_log.txt")
    with open(log_file, "w") as f:
        before_cookies = browser.get_cookies()
        f.write("Файлы cookie перед удалением:\n")
        for cookie in before_cookies:
            f.write(str(cookie) + "\n")
        browser.delete_all_cookies()
        after_cookies = browser.get_cookies()
        f.write("Файлы cookie после удаления:\n")
        for cookie in after_cookies:
            f.write(str(cookie) + "\n")
    browser.quit()

@pytest.fixture
def chrome_options(chrome_options):
    # chrome_options.binary_location = '/usr/bin/google-chrome-stable'
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=DEBUG')

    return chrome_options

@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Функция помогает обнаружить, что какой-либо тест не пройден успешно,
    # и передать эту информацию

    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
    return rep

@pytest.fixture
def web_browser(request, selenium):
    browser = selenium
    browser.set_window_size(1400, 1000)

    # Возврат экземпляра
    yield browser

    # Код будет выполняться после каждого теста

    if request.node.rep_call.failed:
        # Делается снимок экрана, если тест не удался
        try:
            browser.execute_script("document.body.bgColor = 'white';")

            # Делается снимок экрана для локальной отладки
            browser.save_screenshot('screenshots/' + str(uuid.uuid4()) + '.png')

            # Приложение скриншота к Allure report
            allure.attach(browser.get_screenshot_as_png(),
                          name=request.function.__name__,
                          attachment_type=allure.attachment_type.PNG)

            # Для успешной отладки
            print('URL: ', browser.current_url)
            print('Browser logs:')
            for log in browser.get_log('browser'):
                print(log)

        except:
            pass  # Игнорирование любых ошибкок

def get_test_case_docstring(item):
    # Функция получения строки doc из тестового примера и форматирования ее,
    # чтобы она отображалась в отчетах вместо имени тестового примера.

    full_name = ''

    if item._obj.__doc__:
        # Удаление лишних пробелов из строки док-та
        name = str(item._obj.__doc__.split('.')[0]).strip()
        full_name = ' '.join(name.split())

        # Генерация списока параметров для параметризованных тестовых случаев
        if hasattr(item, 'callspec'):
            params = item.callspec.params

            res_keys = sorted([k for k in params])
            # Создать список на основе словаря
            res = ['{0}_"{1}"'.format(k, params[k]) for k in res_keys]
            # Добавление словаря со всеми параметрами к названию тестового примера
            full_name += ' Parameters ' + str(', '.join(res))
            full_name = full_name.replace(':', '')

    return full_name

def pytest_itemcollected(item):
    # Функция изменения названия тестовых наборов
    # во время выполнения тестовых наборов

    if item._obj.__doc__:
        item._nodeid = get_test_case_docstring(item)

def pytest_collection_finish(session):
    # Функция изменения названия тестовых примеров,
    # когда используется параметр --collect-only для pytest
    # (чтобы получить полный список всех существующих тестовых примеров)

    if session.config.option.collectonly is True:
        for item in session.items:
            # Если тестовый пример содержит строку doc, то нужно изменить его название на строку doc,
            # чтобы отображать читаемые отчеты и
            # автоматически импортировать тестовые примеры в систему управления тестированием
            if item._obj.__doc__:
                full_name = get_test_case_docstring(item)
                print(full_name)

        pytest.exit('Выполнено!')