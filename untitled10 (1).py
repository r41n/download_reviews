import streamlit as st
import pandas as pd
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

st.set_page_config(page_title="Загрузка отзывов App Store", layout="wide")

st.title("📱 Загрузка отзывов из App Store")

app_id = st.text_input("Введите ID приложения App Store")

if st.button("Получить отзывы"):

    if not re.fullmatch(r"\d+", app_id):
        st.error("ID приложения должен содержать только цифры.")
        st.stop()

    rss_url = (
        f"https://itunes.apple.com/ru/rss/customerreviews/"
        f"id={app_id}/sortBy=mostRecent/json"
    )

    with st.spinner("Получение отзывов..."):

        try:
            with urllib.request.urlopen(rss_url, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            st.error(f"Ошибка сервиса Apple: HTTP {e.code}")
            st.stop()

        except urllib.error.URLError as e:
            st.error(f"Ошибка подключения: {e.reason}")
            st.stop()

        except Exception as e:
            st.error(f"Неожиданная ошибка: {e}")
            st.stop()

    feed = data.get("feed")

    if not feed:
        st.warning("Отзывы не найдены.")
        st.stop()

    entries = feed.get("entry", [])

    if len(entries) <= 1:
        st.warning("Отзывы отсутствуют.")
        st.stop()

    # Первый элемент содержит информацию о приложении
    entries = entries[1:]

    russian_pattern = re.compile(r"[А-Яа-яЁё]")

    reviews = []

    progress = st.progress(0)

    for i, item in enumerate(entries):

        title = item.get("title", {}).get("label", "").strip()
        text = item.get("content", {}).get("label", "").strip()

        # Только русскоязычные отзывы
        if not russian_pattern.search(text):
            continue

        author = item.get("author", {}).get("name", {}).get("label", "").strip()
        rating = item.get("im:rating", {}).get("label", "")
        date = item.get("updated", {}).get("label", "")

        try:
            dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
            date = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass

        reviews.append({
            "дата": date,
            "имя автора": author,
            "рейтинг": rating,
            "текст отзыва": text,
            "заголовок": title,
            "страна": "Россия"
        })

        progress.progress((i + 1) / len(entries))

    if not reviews:
        st.warning("Русскоязычные отзывы не найдены.")
        st.stop()

    df = pd.DataFrame(reviews)

    st.success(f"Получено отзывов: {len(df)}")

    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 Скачать CSV",
        data=csv,
        file_name=f"reviews_{app_id}.csv",
        mime="text/csv"
    )
