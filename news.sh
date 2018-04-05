#!/bin/bash

echo "Fetching news..."

# Short pauses may get your IP banned
PAUSE_SECONDS=30

while true;
do
    python3 news.py
    sleep $PAUSE_SECONDS
    test $? -gt 128 && break
done

