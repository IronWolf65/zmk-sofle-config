[English](README.md) | **Русский**

# Конфиг ZMK для Sofle Choc (AliExpress/PandaKB)

Конфигурация [ZMK Firmware](https://zmk.dev/) для сплит-клавиатуры **Sofle Choc**.

**Kit:** Sofle Choc  
**Контроллер:** SuperMini nRF52840

## Оборудование

- Энкодер EC11 (low profile)
- Дисплей OLED 128x32
- Светодиоды (LED)
- Аккумулятор
- Тачпад TPS43

## Сборка прошивки

Прошивку можно собрать автоматически через **GitHub Actions** в этом репозитории. Готовые файлы `.uf2` будут доступны в запусках [Actions](https://github.com/IronWolf65/zmk-sofle-config/actions) или в директории `output/` после успешной сборки.

## Локальная сборка

Для локальной сборки используется [zmk-docker-build](https://github.com/IronWolf65/zmk-docker-build).  
Выполните `make build`

## Полезные ссылки

- [Документация ZMK](https://zmk.dev/docs)
- [Руководство по раскладкам ZMK](https://zmk.dev/docs/keymaps)
