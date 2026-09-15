# Контекст 1CRoutingAPI

Документация фиксирует фактическое состояние репозитория на 2026-06-20, commit `8d0661b4eed96f6b52eb841aa60f0f34ca518926`. Источники: Python-код, `migrations/return_to_supplier.sql`, Docker-конфигурация, зависимости и тест. Полной схемы рабочей БД и кода frontend/WMS в репозитории нет; пробелы отмечены явно.

## Рекомендуемый порядок чтения

1. `current_state.md`
2. `architecture_notes.md`
3. `domain_model.md`
4. `business_rules.md`
5. `api_map.md`
6. `integration_map.md`
7. `database_map.md`
8. `invariants.md`
9. `known_issues.md`
10. `risk_map.md`
11. `saga_candidates.md`
12. `decommission_map.md`

Остальные файлы детализируют операции записи, пробелы API, ADR, БД, frontend-сценарии, вопросы и audit SQL. Документацию необходимо обновлять при изменении endpoint, SQL, интеграционных контрактов или бизнес-логики.

## Локальная документация для AI

Служебный контекст для Codex и других AI-ассистентов хранится локально
в каталоге `local_docs/`.

Каталог не является частью основной документации проекта и не
версионируется в Git.

Основная техническая документация для разработчиков находится в
`docs/context/`.
