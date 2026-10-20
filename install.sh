#!/bin/bash
# Установка автовыключения подсветки клавиатуры (при включении и после сна) через systemd.
# Повторный запуск = обновить установленную копию скрипта после правок скрипта.
set -e
H="$(cd "$(dirname "$0")" && pwd)"
[ "$(id -u)" = 0 ] || { echo "Запускать через sudo"; exit 1; }
# Копия в /usr/local, принадлежащая root: сервис от root не должен запускать файл, который можно править без sudo
install -d -m 755 /usr/local/lib/kbd-backlight
install -m 755 "$H/kbd-backlight.py" /usr/local/lib/kbd-backlight/
install -m 644 "$H/1462_1563_ReportDescriptor.txt" /usr/local/lib/kbd-backlight/
install -m 644 "$H/kbd-backlight-off.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable kbd-backlight-off.service
systemctl start kbd-backlight-off.service
systemctl --no-pager status kbd-backlight-off.service | grep -E 'Loaded|Active|ok:'
