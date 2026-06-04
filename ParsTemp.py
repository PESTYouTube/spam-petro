# weather_parser.py
from typing import Any
import requests
from bs4 import BeautifulSoup as BS
import re


def get_weather_forecast() -> str:
	"""Получает свежий прогноз погоды и возвращает отформатированную строку"""
	try:
		url = 'https://rp5.ru/Погода_в_Санкт-Петербурге_(север)'

		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
		}

		r = requests.get(url, headers=headers, timeout=10)
		r.raise_for_status()

		html = BS(r.text, 'html.parser')

		# Парсим даты
		forecast_rows = html.find_all('tr', class_='forecastDate')
		all_dates = []
		for row in forecast_rows:
			weekdays = row.find_all('span', class_='weekDay')
			for weekday in weekdays:
				all_dates.append(weekday.get_text(strip=True))

		# Парсим время
		time_rows = html.find_all('tr', class_='forecastTime')
		if not time_rows:
			return "❌ Не удалось получить данные о времени"

		first_row = time_rows[0]
		all_cells = first_row.find_all('td')
		times = []
		for cell in all_cells[1:]:
			time_value = cell.get_text(strip=True)
			if time_value:
				times.append(time_value)

		# Парсим температуру
		temperatura_cells = html.select('td:has(div.t_0)')
		tempes = []
		for cell in temperatura_cells:
			div_c = cell.find('div', class_='t_0')
			if div_c:
				raw_text = div_c.get_text(strip=True)
				tempes.append(raw_text)

		# Парсим облачность
		clouds = []
		for div_cc in html.find_all('div', class_='cc_0'):
			cloud_div = div_cc.find(lambda tag: tag.name == 'div' and
												tag.get('class') and
												(tag['class'][0].startswith('cd') or
												 tag['class'][0].startswith('cn')))

			if cloud_div and cloud_div.get('onmouseover'):
				match = re.search(r'<b>(.*?)</b>', cloud_div['onmouseover'])
				if match:
					clouds.append(match.group(1))

		# Форматируем прогноз
		return parsing_temp(times, tempes, all_dates, clouds)

	except requests.RequestException as e:
		print(f"Ошибка подключения: {e}")
		return "❌ Не удалось подключиться к сайту погоды"
	except Exception as e:
		print(f"Ошибка парсинга: {e}")
		return "❌ Ошибка при обработке данных погоды"


def parsing_temp(times: list, temps: list, all_dates: list, clouds: list) -> str:
	"""Форматирует прогноз погоды"""
	if not all_dates or not times:
		return "Нет данных для отображения"

	count = 0
	message_lines = []

	# Обрабатываем максимум 8 дней (сколько обычно бывает)
	days_count = min(len(all_dates), 8)

	for i in range(days_count):
		date = all_dates[i]
		message_lines.append(f"*{date}*")

		# Определяем количество замеров для первого дня
		if i == 0 and times:
			if times[0] == "03":
				measurements = 4
			elif times[0] == "09":
				measurements = 3
			elif times[0] == "15":
				measurements = 2
			elif times[0] == "21":
				measurements = 1
			else:
				measurements = 4
		else:
			measurements = 4

		# Добавляем замеры для текущего дня
		for _ in range(measurements):
			if count >= len(times) or count >= len(temps) or count >= len(clouds):
				break

			temp_clean = temps[count].replace('+', '')
			message_lines.append(f"Время {times[count]}: {temp_clean}° будет {clouds[count]}")
			count += 1

		message_lines.append("")  # Пустая строка между днями

		if count >= len(times):
			break

	return "\n".join(message_lines)


def parsing_temp_day(times: list, temps: list, all_dates: list, clouds: list) -> str:
	"""Форматирует прогноз на один день"""
	if len(times) < 3 or len(temps) < 3 or len(clouds) < 3:
		return "Недостаточно данных"

	count = 0
	message_lines = []

	# Берем первые две даты или одну
	if len(all_dates) >= 2:
		date = all_dates[0]
	else:
		date = all_dates[0] if all_dates else "Сегодня"

	message_lines.append(f"*{date}*")
	message_lines.append("")

	for _ in range(3):
		temp_clean = temps[count].replace('+', '')
		message_lines.append(f"Время {times[count]}: {temp_clean}° будет {clouds[count]}")
		count += 1

	return "\n".join(message_lines)