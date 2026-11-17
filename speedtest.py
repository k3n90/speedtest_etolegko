"""Десять последовательных GET-запросов и скорость скачивания."""

from __future__ import annotations

import argparse
import http.client
import sys
import time
import urllib.error
import urllib.request

REQUESTS = 10
TIMEOUT_SECONDS = 30
USER_AGENT = "speedtest/1.0"
MB = 1000 ** 2


def fetch(url: str) -> tuple[float, int]:
    """Один GET: полное тело ответа и длительность в секундах.

    Таймер включает DNS, соединение, TLS, заголовки и чтение тела.
    В объём входит число реально прочитанных байт.
    """
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
        method="GET",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = response.read()
    return time.perf_counter() - started, len(body)


def measure(url: str) -> tuple[list[float], int]:
    """Десять запросов строго по очереди. Следующий стартует после полного чтения предыдущего."""
    durations: list[float] = []
    total_bytes = 0
    for _ in range(REQUESTS):
        elapsed, size = fetch(url)
        durations.append(elapsed)
        total_bytes += size
    return durations, total_bytes


def format_report(durations: list[float], total_bytes: int) -> str:
    total_seconds = sum(durations)
    average_ms = (total_seconds / REQUESTS) * 1000
    volume_mb = total_bytes / MB
    if total_seconds == 0:
        speed_mb_s = 0.0
    else:
        speed_mb_s = (total_bytes / MB) / total_seconds

    rows = (
        ("Запросов:", str(REQUESTS)),
        ("Среднее время:", f"{average_ms:.1f} мс"),
        ("Объём данных:", f"{volume_mb:.2f} МБ ({total_bytes} байт)"),
        ("Скорость:", f"{speed_mb_s:.2f} МБ/с"),
    )
    width = max(len(label) for label, _ in rows)
    return "\n".join(f"{label:<{width}}  {value}" for label, value in rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Делает 10 последовательных GET-запросов к адресу, "
            "дожидается полного ответа на каждый и печатает скорость скачивания."
        )
    )
    parser.add_argument("url", help="Адрес, к которому выполнять запросы")
    args = parser.parse_args(argv)

    try:
        durations, total_bytes = measure(args.url)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
        http.client.HTTPException,
    ) as exc:
        print(f"Ошибка запроса: {exc}", file=sys.stderr)
        return 1

    print(format_report(durations, total_bytes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
