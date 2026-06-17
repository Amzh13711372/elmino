#!/bin/bash
export APP_SECRET="my-secret-key"
export ZARINPAL_MERCHANT_ID="YOUR-ID"
export ZARINPAL_CALLBACK_URL="http://127.0.0.1:5000/payment/verify"
python3 ~/elmino/app/main.py
