# Тестовое задание для Demlabs

## Local deployment

install poetry: \
`curl -sSL https://install.python-poetry.org | python3.10 -`

install requirements: \
`poetry install`

activate venv

run scripts 'cli_config.py'

### Examples

`python cli_config.py get --addr root@195.133.49.83:22:/root/configs a.a1.owner.name`

`python cli_config.py set --addr root@195.133.49.83:22:/root/configs a.a1.new_section.name "New section"`


## Комментарий

Решение протестировано вручную. Автотесты не писал, думаю, это излишне в рамках тестового задания. \
Настройки прописаны для рабочего VPS(арендовал для проверки), можно на нем проверить функционал. \
Надеюсь ничего не забыл -)