# Подсветка клавиатуры MSI в Linux (MysticLight 1462:1563)

Выключение и включение RGB-подсветки клавиатуры ноутбуков MSI с контроллером
**MSI MysticLight MS-1563** (USB `1462:1563`) без MSI Center и без Windows.

Проверено на **MSI Pulse GL76 11UCK** (Ubuntu, ядро 7.0). Тот же контроллер стоит, например,
в MSI Alpha 17 B5EEK, а скорее всего и в других моделях.

```
lsusb | grep 1462:1563
Bus 003 Device 002: ID 1462:1563 Micro Star International MysticLight MS-1563 v0001
```

## Использование

```
sudo ./kbd-backlight.py off               # выключить
sudo ./kbd-backlight.py on white 5        # включить: white | red | green | blue, яркость 1–5
sudo ./kbd-backlight.py off --dry-run     # только показать пакет, ничего не отправлять
```

### Автовыключение при включении и после сна

```
sudo ./install.sh
```
Скрипт копирует файлы в `/usr/local/lib/kbd-backlight/` (копия принадлежит root, чтобы сервис
от root не запускал файл, который можно поменять без sudo) и включает `kbd-backlight-off.service`.
Повторный запуск обновляет установленную копию.

Удалить:
```
sudo systemctl disable --now kbd-backlight-off.service
sudo rm /etc/systemd/system/kbd-backlight-off.service
sudo rm -r /usr/local/lib/kbd-backlight
sudo systemctl daemon-reload
```

## Как это работает

Подсветкой управляет не EC (встроенный контроллер ноутбука), а отдельный USB HID-контроллер.
В Linux к нему подключается только общий драйвер `hid-generic`, который даёт «сырой» доступ
через `/dev/hidrawN`. Какие пакеты контроллер понимает, MSI не публикует.

Пакеты взяты из записей USB-трафика MSI Center (USBPcap), которые приложили к заявке OpenRGB
[#2289](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/2289). Подсветку меняет один
feature report №2 длиной 64 байта (`SET_REPORT`, `bmRequestType 0x21`, `wValue 0x0302`):

```
байт:  0  1  2      3  4         5  6  7  8
      02 00 [режим] 00 [яркость] 01 [R  G  B] ff 50 00 ff ff 00 00 ff 00 00 00 ff 96 00 ff ff 00 ff 00 …
```

| Действие в MSI Center | режим | яркость | R G B |
|---|---|---|---|
| Whole Device Off | `00` | `0a` | (не важно) |
| Steady, полная яркость … минимум | `01` | `0a` `08` `06` `04` `02` | `ff 00 00`, `00 ff 00`, `00 00 ff`, `ff ff ff` |

Остальные 61 байт во всех записях одинаковые, и скрипт отправляет их без изменений.
В Linux пакет уходит через `ioctl(HIDIOCSFEATURE)` на `/dev/hidrawN`.

## Безопасность

- Отправляются **только** варианты, которые есть в записях MSI Center. Скрипт меняет только режим,
  яркость и цвет, и только на записанные значения. Угадывание неизвестных команд в других проектах
  портило RGB-контроллеры MSI, поэтому OpenRGB отключил у себя поддержку MSI Mystic Light.
- Перед отправкой скрипт сверяет report descriptor устройства с `1462_1563_ReportDescriptor.txt`.
  Если descriptor отличается (другая ревизия контроллера или прошивки), скрипт ничего не отправит.

Используйте на свой риск.

## Почему не msi-ec

Драйвер [msi-ec](https://github.com/BeardOverflow/msi-ec) управляет подсветкой через EC. Так работают
модели с одноцветной клавиатурой. На моделях с этим RGB-контроллером запись в EC подсветку не меняет.
Fn+F9/F10 меняют уровень яркости в EC (адрес `0xd3`), но в контроллер сам EC ничего не отправляет:
это делает MSI Center.

## Файлы

| Файл | Что это |
|---|---|
| `kbd-backlight.py` | управление подсветкой |
| `kbd-backlight-off.service` | systemd-юнит: выключить при загрузке и после сна |
| `install.sh` | установка и обновление юнита |
| `1462_1563_ReportDescriptor.txt` | эталонный report descriptor для проверки устройства |

## Лицензия

GPL-2.0, см. [LICENSE](LICENSE).
