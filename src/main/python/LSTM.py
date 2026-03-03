import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)

import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

import pandas as pd
import numpy as np
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from keras.api.models import Sequential
from keras.api.layers import Dense, LSTM, Input
from keras.api.callbacks import EarlyStopping
from keras.api import backend as K
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score

BASE_DIR = Path(__file__).resolve().parent
SMESTUVANJE_DIR = BASE_DIR / 'Smestuvanje'

mega_data_path = str(SMESTUVANJE_DIR / 'mega-data.csv')
processed_dataset_path = str(SMESTUVANJE_DIR / 'processed_lstm.csv')
names_json_filepath = str(SMESTUVANJE_DIR / 'names.json')
codes_json_filepath = str(SMESTUVANJE_DIR / 'processed_codes.json')

FORECAST_DAYS = 7


def generate_future_dates(last_date, num_days):
    """Generate next `num_days` business days after `last_date`."""
    dates = []
    current = last_date
    while len(dates) < num_days:
        current += timedelta(days=1)
        # Skip weekends (Saturday=5, Sunday=6)
        if current.weekday() < 5:
            dates.append(current)
    return dates


def predict_values_for_issuer(all_data: pd.DataFrame, issuer_code: str):
    issuer_table_data = all_data[all_data['code'] == issuer_code].copy()

    if len(issuer_table_data) < 100:
        return None

    issuer_table_data = issuer_table_data.drop_duplicates(subset=['date'])
    issuer_table_data.sort_values('date', inplace=True)
    issuer_table_data['Moving average'] = issuer_table_data['close'].rolling(window=3, min_periods=1).mean()
    issuer_table_data['EMA'] = issuer_table_data['close'].ewm(span=5, adjust=False).mean()
    issuer_table_data.dropna(axis=0, inplace=True)
    issuer_table_data.set_index('date', inplace=True)
    issuer_table_data = issuer_table_data.drop(
        columns=['code', 'max', 'low', 'avg', 'volume', 'turnover in BEST', 'total turnover'])

    # Remember the last date for generating future dates
    last_available_date = issuer_table_data.index[-1]

    calc_lag = round(len(issuer_table_data) / 500.0)
    lag = max(calc_lag, 2)

    # Build lagged features
    lagged_frames = [issuer_table_data]
    for i in range(lag, 0, -1):
        shifted = issuer_table_data.shift(i).add_suffix(f'_lag{i}')
        lagged_frames.append(shifted)
    merged = pd.concat(lagged_frames, axis=1)
    merged = merged.dropna(axis=0)

    og_cols = ['close', 'Moving average', 'EMA']
    features = [f for f in merged.columns if f not in og_cols]
    num_features_per_lag = len(features) // lag

    if num_features_per_lag * lag != len(features):
        return None

    X = merged[features]
    Y = merged['close']

    if Y.nunique() <= 1:
        return None

    # --- Validation split to compute R² score ---
    split_idx = int(len(X) * 0.8)
    x_val_raw = X.iloc[split_idx:]
    y_val = Y.iloc[split_idx:]

    scaler_x = MinMaxScaler()
    scaler_y = MinMaxScaler()

    # Fit scalers on ALL data (we need the full range for forecasting)
    x_all_scaled = scaler_x.fit_transform(X)
    y_all_scaled = scaler_y.fit_transform(Y.values.reshape(-1, 1)).flatten()

    x_train_lstm = x_all_scaled.reshape((x_all_scaled.shape[0], lag, num_features_per_lag))

    model = Sequential([
        Input((lag, num_features_per_lag)),
        LSTM(64, activation="tanh", return_sequences=True),
        LSTM(32, activation="tanh"),
        Dense(1, activation="linear")
    ])
    model.compile(loss="mean_squared_error", optimizer="adam")

    early_stop = EarlyStopping(patience=6, monitor='val_loss', restore_best_weights=True)

    model.fit(x_train_lstm, y_all_scaled, batch_size=16, epochs=32,
              shuffle=False, validation_split=0.1, callbacks=[early_stop], verbose=0)

    # Compute R² on the held-out validation portion
    x_val_scaled = scaler_x.transform(x_val_raw)
    x_val_lstm = x_val_scaled.reshape((x_val_scaled.shape[0], lag, num_features_per_lag))
    y_val_pred_scaled = model.predict(x_val_lstm, verbose=0)
    y_val_pred = scaler_y.inverse_transform(y_val_pred_scaled).flatten()
    score = r2_score(y_val, y_val_pred)

    # --- Iterative 7-day forecast ---
    # We need the last `lag` rows of the original (unlagged) data to build future inputs
    # Each "row" in the LSTM input is [lag timesteps x features_per_lag]
    # features_per_lag columns are: close, Moving average, EMA (the lagged versions)
    # To forecast forward, we predict close, recompute MA/EMA, and slide the window

    # Get the raw feature columns (close, Moving average, EMA) for the last `lag` rows
    recent_window = issuer_table_data[['close', 'Moving average', 'EMA']].iloc[-lag:].copy()

    future_dates = generate_future_dates(last_available_date, FORECAST_DAYS)
    forecast_results = []

    for future_date in future_dates:
        # Build the input: the window IS the lag features
        # Each lag step has [close, Moving average, EMA] from that time step
        # The model expects: lag_N features first, then lag_N-1, ..., lag_1
        # So we flatten the window rows from oldest to newest as lag features

        input_row = []
        for i in range(lag):
            row_vals = recent_window.iloc[i].values
            input_row.extend(row_vals)

        # Wrap in DataFrame with the same feature names the scaler was fitted on
        input_df = pd.DataFrame([input_row], columns=features)

        # Validate feature count
        if input_df.shape[1] != len(features):
            break

        input_scaled = scaler_x.transform(input_df)

        input_lstm = input_scaled.reshape((1, lag, num_features_per_lag))

        pred_scaled = model.predict(input_lstm, verbose=0)
        pred_close = scaler_y.inverse_transform(pred_scaled).flatten()[0]

        # Compute new MA and EMA using the predicted close
        # Append predicted close to compute rolling stats
        all_closes = list(recent_window['close'].values) + [pred_close]

        new_ma = np.mean(all_closes[-3:])  # window=3 moving average
        # EMA: span=5, use the last EMA value
        last_ema = recent_window['EMA'].iloc[-1]
        multiplier = 2.0 / (5 + 1)
        new_ema = (pred_close - last_ema) * multiplier + last_ema

        forecast_results.append({
            'date': future_date.strftime('%d.%m.%Y'),
            'close': round(pred_close, 2),
            'close_pred': round(pred_close, 2),
            'code': issuer_code,
            'score': score,
            'date_processed': datetime.today().date().isoformat()
        })

        # Slide the window: drop the oldest row, add the new predicted row
        new_row = pd.DataFrame({
            'close': [pred_close],
            'Moving average': [new_ma],
            'EMA': [new_ema]
        }, index=[future_date])
        recent_window = pd.concat([recent_window.iloc[1:], new_row])

    K.clear_session()

    if not forecast_results:
        return None

    result_df = pd.DataFrame(forecast_results)
    return result_df


def save_processed_codes_to_json(codes_list: list, json_codes_path: str):
    with open(json_codes_path, 'w', encoding='utf-8') as f:
        json.dump(codes_list, f, ensure_ascii=False, indent=4)
    print(f"Processed issuer codes saved to {json_codes_path}")


def find_last_processing(names_file_path: str, processed_path: str):
    with open(names_file_path, 'r', encoding='utf-8') as file_og:
        json_data = json.load(file_og)

    if os.path.exists(processed_path):
        processed_data = pd.read_csv(processed_path)
        today_date = datetime.today().date().isoformat()
        if processed_data.iloc[0]['date_processed'] == today_date:
            return None

    return json_data


def process_all():
    data = pd.read_csv(mega_data_path)
    data['date'] = pd.to_datetime(data['date'], format='%d.%m.%Y')
    data.sort_values('date', inplace=True)

    json_data = find_last_processing(names_json_filepath, processed_dataset_path)
    if not json_data:
        print("DONE|0|No issuers to process or data already up-to-date.")
        return

    total = len(json_data)
    all_predicts = []
    all_predict_codes = []
    start_time = time.time()

    for idx, issuer in enumerate(json_data, start=1):
        code = issuer['Issuer code']
        progress_pct = (idx / total) * 100

        elapsed = time.time() - start_time
        avg_per_item = elapsed / idx if idx > 0 else 0
        remaining = avg_per_item * (total - idx)
        eta_str = time.strftime("%M:%S", time.gmtime(remaining))

        print(f"PROGRESS|{progress_pct:.1f}|[{idx}/{total}]: {code} | "
              f"Elapsed: {elapsed:.0f}s | ETA: {eta_str}", flush=True)

        try:
            result = predict_values_for_issuer(data, code)
            if result is not None:
                all_predicts.append(result)
                all_predict_codes.append(code)
                print(f"  Done — R² score: {result['score'].iloc[0]:.4f} | "
                      f"Forecasted {len(result)} days ahead", flush=True)
            else:
                print(f"  Skipped (insufficient data or feature mismatch)", flush=True)
        except Exception as e:
            print(f"  Error: {e}", flush=True)

    total_elapsed = time.time() - start_time
    print(f"\nAll issuers processed in {total_elapsed:.1f}s", flush=True)

    if all_predicts:
        try:
            concatenated_data = pd.concat(all_predicts, ignore_index=True)
            concatenated_data.to_csv(processed_dataset_path, index=False)
            save_processed_codes_to_json(all_predict_codes, codes_json_filepath)
            print(f"Processed data saved to {processed_dataset_path}", flush=True)
        except Exception as e:
            print(f"Error saving processed data: {e}", flush=True)
    else:
        print("No data to save.", flush=True)


process_all()
sys.stdout.flush()
