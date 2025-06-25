FROM python:3.12-slim
LABEL authors="skurbick"

# Устанавливаем системные зависимости и шрифты
RUN apt-get update && \
    apt-get install -y \
    fontconfig \
    fonts-dejavu-core \
    ttf-mscorefonts-installer \
    wget && \
    # Очистка кэша apt для уменьшения размера образа
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем дополнительные шрифты (если нужно)
RUN mkdir -p /usr/share/fonts/truetype/custom && \
    wget -q -O /tmp/dejavu-fonts-ttf-2.37.tar.bz2 \
    https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.tar.bz2 && \
    tar -xjf /tmp/dejavu-fonts-ttf-2.37.tar.bz2 -C /tmp && \
    cp /tmp/dejavu-fonts-ttf-2.37/ttf/* /usr/share/fonts/truetype/custom/ && \
    rm -rf /tmp/dejavu-fonts-ttf-2.37* && \
    fc-cache -fv


WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]