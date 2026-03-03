# === Suppress all warnings BEFORE any library imports ===
import os
import warnings
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

warnings.filterwarnings("ignore")

import logging
logging.disable(logging.CRITICAL)

import transformers
transformers.logging.set_verbosity_error()

# === Now import everything else ===
import json
import time
import threading
from datetime import datetime
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from transformers import pipeline
from playwright.sync_api import sync_playwright


# === Progress Tracker ===
class ProgressTracker:
    """Track and emit progress as percentages with ETA."""

    def __init__(self, total_channels):
        self._total_channels = total_channels
        self._start_time = time.time()
        self._lock = threading.Lock()
        # Weighted phases: scraping=50%, translation=25%, sentiment=25%
        self._phase_weights = {
            "scraping": 0.50,
            "translation": 0.25,
            "sentiment": 0.25,
        }

    def _calc_eta(self, completed_channels):
        """Calculate ETA string based on completed channels."""
        elapsed = time.time() - self._start_time
        if completed_channels <= 0:
            return "00:00"
        avg_per_channel = elapsed / completed_channels
        remaining = avg_per_channel * (self._total_channels - completed_channels)
        return time.strftime("%M:%S", time.gmtime(remaining))

    def _elapsed_str(self):
        """Get elapsed time in seconds."""
        return f"{time.time() - self._start_time:.0f}s"

    def _emit_progress(self, percentage, message=""):
        """Emit a PROGRESS line with percentage (0-100)."""
        pct = min(100.0, max(0.0, percentage))
        safe_msg = message.replace("|", "-").replace("\n", " ").replace("\r", "").strip()
        print(f"PROGRESS|{pct:.1f}|{safe_msg}", flush=True)

    def channel_start(self, channel_index, channel_code):
        """Emit progress when starting a new channel."""
        if self._total_channels == 0:
            return
        pct = (channel_index / self._total_channels) * 100
        eta = self._calc_eta(channel_index)
        self._emit_progress(
            pct,
            f"[{channel_index + 1}/{self._total_channels}]: {channel_code} | "
            f"Elapsed: {self._elapsed_str()} | ETA: {eta}"
        )

    def channel_phase(self, channel_index, channel_code, phase, phase_progress=1.0):
        """
        Report progress for a specific channel and phase.
        channel_index: 0-based index of the current channel
        phase: "scraping", "translation", or "sentiment"
        phase_progress: 0.0 to 1.0 within the phase
        """
        if self._total_channels == 0:
            return

        channel_weight = 100.0 / self._total_channels
        channel_base = channel_index * channel_weight

        phase_order = ["scraping", "translation", "sentiment"]
        phase_idx = phase_order.index(phase)
        completed_phases_pct = sum(
            self._phase_weights[phase_order[i]] for i in range(phase_idx)
        )
        current_phase_pct = self._phase_weights[phase] * phase_progress

        overall = channel_base + channel_weight * (completed_phases_pct + current_phase_pct)
        eta = self._calc_eta(channel_index + phase_progress * (1.0 / len(phase_order)))
        self._emit_progress(
            overall,
            f"[{channel_index + 1}/{self._total_channels}]: {channel_code} - {phase} | "
            f"Elapsed: {self._elapsed_str()} | ETA: {eta}"
        )

    def channel_done(self, channel_index, channel_code, message=""):
        """Mark a channel as fully complete."""
        if self._total_channels == 0:
            return
        overall = ((channel_index + 1) / self._total_channels) * 100
        eta = self._calc_eta(channel_index + 1)
        self._emit_progress(
            overall,
            f"[{channel_index + 1}/{self._total_channels}]: {channel_code} | "
            f"{message} | Elapsed: {self._elapsed_str()} | ETA: {eta}"
        )

    def done(self):
        """Emit 100% completion."""
        elapsed = time.time() - self._start_time
        self._emit_progress(100.0, f"Processing complete | Total time: {elapsed:.1f}s")


# === Device detection ===
def get_device():
    """Detect the best available device: CUDA GPU > Apple MPS > CPU."""
    if torch.cuda.is_available():
        device_id = 0
        gpu_name = torch.cuda.get_device_name(device_id)
        print(f"DEVICE|GPU|CUDA - {gpu_name}", flush=True)
        return device_id
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("DEVICE|GPU|Apple MPS", flush=True)
        return "mps"
    else:
        print("DEVICE|CPU|No GPU detected - using CPU", flush=True)
        return -1


# === Structured output helper ===
def emit(issuer_code, status, message=""):
    """Print a machine-parseable progress line to stdout."""
    safe_msg = message.replace("|", "-").replace("\n", " ").replace("\r", "").strip()
    print(f"{issuer_code}|{status}|{safe_msg}", flush=True)


# === Browser Manager — single browser, reused across all scraping ===
class BrowserManager:
    """Reuse a single browser instance across all scraping calls."""

    def __init__(self, max_concurrent_pages=8):
        self._playwright = None
        self._browser = None
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_concurrent_pages)

    def start(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=True)

    def stop(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def fetch_page(self, url, timeout=15000):
        """Fetch a page using a temporary context with resource blocking."""
        self._semaphore.acquire()
        context = None
        try:
            context = self._browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            page.route("**/*.{png,jpg,jpeg,gif,svg,ico,webp}", lambda route: route.abort())
            page.route("**/*.{css,woff,woff2,ttf,eot}", lambda route: route.abort())
            page.route("**/*.{mp4,webm,ogg,mp3,wav}", lambda route: route.abort())
            page.route("**/analytics**", lambda route: route.abort())
            page.route("**/tracking**", lambda route: route.abort())
            page.route("**/ads**", lambda route: route.abort())

            page.goto(url, timeout=timeout, wait_until="domcontentloaded")

            try:
                page.wait_for_selector(".container", timeout=5000)
            except Exception:
                pass

            content = page.content()
            return content
        except Exception as e:
            emit("BROWSER", "ERROR", f"fetch_page failed for {url}: {e}")
            return None
        finally:
            if context:
                context.close()
            self._semaphore.release()


class ChannelItem:
    def __init__(self, item_title, item_link, item_pub_date):
        self.title = item_title
        self.link = item_link
        self.pub_date = item_pub_date

    def __str__(self):
        to_string = (' Item : ' + self.title + '\nLink : ' + self.link
                     + '\n Publication Date : ' + self.pub_date)
        return to_string

    def to_dict(self):
        return {
            'title': self.title,
            'link': self.link,
            'pub_date': self.pub_date
        }


class Channel:
    def __init__(self, title, link, code, items: list[ChannelItem]):
        self.title = title
        self.link = link
        self.code = code
        self.rss_items = items
        self.model_processed_texts = list()
        self.result = "NEUTRAL"
        self.score = 0.00
        self.last_date = datetime.today()

    def setProcessed(self, processed_list: list):
        self.model_processed_texts = processed_list

        labels = [entry['label'] for entry in processed_list]

        if labels:
            most_common_label, _ = Counter(labels).most_common(1)[0]
            self.result = most_common_label

            scores = [entry["score"] for entry in processed_list if entry['label'] == most_common_label]
            most_common_score = sum(scores) / len(scores) if scores else 0.00
            self.score = most_common_score

            self.last_date = datetime.today()

    def to_dict(self):
        return {
            'title': self.title,
            'link': self.link,
            'code': self.code,
            'rss_items': [item.to_dict() for item in self.rss_items],
            'model_processed_texts': self.model_processed_texts,
            'result': self.result,
            'score': self.score,
            'last_date': self.last_date.isoformat()
        }


def getIssuerSiteLinksFromLocal(json_path, processed_json_path):
    with open(json_path, 'r', encoding='utf-8') as file_og:
        data = json.load(file_og)

    processed_data = []

    if os.path.exists(processed_json_path):
        with open(processed_json_path, 'r', encoding='utf-8') as file_processed:
            processed_data = json.load(file_processed)

    today_date = datetime.today().date().isoformat()

    unprocessed_issuers = []

    for issuer in data:
        issuer_code = issuer['Issuer code']
        processed_issuer = next((item for item in processed_data if item['code'] == issuer_code), None)

        if processed_issuer:
            last_date_str = processed_issuer['last_date']
            last_date = datetime.fromisoformat(last_date_str).date().isoformat()

            if last_date == today_date:
                continue
            unprocessed_issuers.append(issuer)

    return unprocessed_issuers


def getRSS_url(url_input: str):
    response_local = requests.get(url_input)

    if response_local.status_code != 200:
        return None

    rss_url_local = response_local.url.replace("/issuer/", "/rss/seinet/")
    return rss_url_local


def processIssuerDictToChannel(issuer):
    code = issuer['Issuer code']
    try:
        rss_url = getRSS_url(issuer['Issuer link'])

        if not rss_url:
            emit(code, "ERROR", f"Failed to resolve RSS URL (HTTP error)")
            return None

        response = requests.get(rss_url)
        response.raise_for_status()
        rss_content = response.text

        root = ET.fromstring(rss_content)
        channel = root.find("channel")

        rss_objects_list = []

        for item in channel.findall("item"):
            title = item.find("title").text
            link = item.find("link").text
            pub_date = item.find("pubDate").text

            rss_item_object = ChannelItem(title, link, pub_date)
            rss_objects_list.append(rss_item_object)

        new_channel = Channel(issuer['Issuer name'], issuer['Issuer link'], issuer['Issuer code'], rss_objects_list)
        return new_channel

    except requests.exceptions.RequestException as e:
        emit(code, "ERROR", f"RSS fetch failed: {e}")
        return None
    except ET.ParseError as e:
        emit(code, "ERROR", f"RSS parse failed: {e}")
        return None


def getRSSlinksForEachIssuer(dictionary_list: list):
    channel_list = list()

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_issuer = {
            executor.submit(processIssuerDictToChannel, issuer): issuer
            for issuer in dictionary_list
        }

        for future in as_completed(future_to_issuer):
            issuer = future_to_issuer[future]
            try:
                channel = future.result()
                if channel:
                    channel_list.append(channel)
            except Exception as e:
                emit(issuer.get('Issuer code', 'UNKNOWN'), "ERROR", f"Thread error: {e}")

    return channel_list


def fetch_rss_page_with_playwright(url, browser_manager):
    """Fetch a page using the shared BrowserManager."""
    page_source = browser_manager.fetch_page(url)
    if not page_source:
        return None
    soup = BeautifulSoup(page_source, "html.parser")
    return soup


def process_rss_item(rss_item, channel_title, browser_manager):
    """Process a single RSS item using the shared browser."""
    try:
        rss_link = rss_item.link
        soup = fetch_rss_page_with_playwright(rss_link, browser_manager)

        if not soup:
            return None

        container = soup.select('.container')

        if not container or len(container) < 3:
            return None

        container = container[2]
        concatenated_t = str(container.get_text(strip=True)).replace("Листај по издавачЛистај по урнек", "")
        concatenated_t = concatenated_t.replace(
            "VW_DOCUMENT_PREVIEW_BYISSUERVW_DOCUMENT_PREVIEW_BYLAYOUTVW_DOCUMENT_PREVIEW_PUBLISHEDON:VW_DOCUMENT_PREVIEW_PUBLICID:VW_DOCUMENT_PREVIEW_LAYOUT:",
            "")
        concatenated_t = concatenated_t.replace("\xa0", "").strip()

        if not concatenated_t:
            return None

        return {"channel_title": channel_title, "rss_link": rss_link, "text": concatenated_t}
    except Exception:
        return None


def process_channel(channel, model, translator, browser_manager, channel_index, progress_tracker):
    """Process a single channel using shared model, translator, and browser."""
    try:
        texts_to_translate = []
        rss_links = []
        total_items = len(channel.rss_items)

        # Emit start of channel
        progress_tracker.channel_start(channel_index, channel.code)

        # Phase 1: Scraping (50% of channel work)
        for idx, rss_item in enumerate(channel.rss_items):
            result = process_rss_item(rss_item, channel.title, browser_manager)
            if result:
                texts_to_translate.append(result["text"])
                rss_links.append(result["rss_link"])

            scrape_progress = (idx + 1) / max(total_items, 1)
            progress_tracker.channel_phase(channel_index, channel.code, "scraping", scrape_progress)

        if not texts_to_translate:
            emit(channel.code, "OK", "No texts found - marked NEUTRAL")
            progress_tracker.channel_done(channel_index, channel.code, "No texts - NEUTRAL")
            return

        # Phase 2: Translation (25% of channel work)
        translated_texts = []
        total_translation_batches = max(1, (len(texts_to_translate) + 3) // 4)
        for i in range(0, len(texts_to_translate), 4):
            batch = texts_to_translate[i:i + 4]
            try:
                translated_batch = translator(batch, max_length=512, truncation=True)
                translated_texts.extend([res['translation_text'].strip() for res in translated_batch])
            except Exception as e:
                emit(channel.code, "WARN", f"Translation batch error: {e}")

            batch_index = i // 4 + 1
            progress_tracker.channel_phase(channel_index, channel.code, "translation",
                                           batch_index / total_translation_batches)

        if not translated_texts:
            emit(channel.code, "OK", "Translation yielded no results - marked NEUTRAL")
            progress_tracker.channel_done(channel_index, channel.code, "No translations - NEUTRAL")
            return

        # Phase 3: Sentiment analysis (25% of channel work)
        sentiments = []
        total_sentiment_batches = max(1, (len(translated_texts) + 3) // 4)
        for i in range(0, len(translated_texts), 4):
            batch = translated_texts[i:i + 4]
            try:
                sentiments.extend(model(batch))
            except Exception as e:
                emit(channel.code, "WARN", f"Sentiment batch error: {e}")

            batch_index = i // 4 + 1
            progress_tracker.channel_phase(channel_index, channel.code, "sentiment",
                                           batch_index / total_sentiment_batches)

        # Prepare processed data
        rss_model_processed = []
        label_mapping = {
            "positive": "POSITIVE",
            "negative": "NEGATIVE",
            "neutral": "NEUTRAL"
        }
        for i in range(len(sentiments)):
            sentiment_label = label_mapping.get(sentiments[i]['label'], "NEUTRAL")
            rss_model_processed.append({
                "rss_link": rss_links[i],
                "original_text": texts_to_translate[i],
                "text": translated_texts[i],
                "label": sentiment_label,
                "score": sentiments[i]['score']
            })

        channel.setProcessed(rss_model_processed)
        result_msg = f"Sentiment: {channel.result} Score: {channel.score:.4f}"
        emit(channel.code, "OK", result_msg)
        progress_tracker.channel_done(channel_index, channel.code, result_msg)

    except Exception as e:
        emit(channel.code, "ERROR", f"Processing failed: {e}")
        progress_tracker.channel_done(channel_index, channel.code, f"Failed: {e}")


def save_channels_to_file(channel_list: list[Channel], filename='channels.json'):
    channels_dict = [channel.to_dict() for channel in channel_list]

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            processed_data = json.load(file)
    else:
        processed_data = []

    processed_issuers_codes = {item['code']: item for item in processed_data}

    for channel in channels_dict:
        processed_issuers_codes[channel['code']] = channel

    updated_processed_data = list(processed_issuers_codes.values())

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(updated_processed_data, f, ensure_ascii=False, indent=4)


def main():
    start_time = time.time()

    # Detect device before loading models
    device = get_device()

    json_file_path = './Smestuvanje/names.json'
    json_channels_path = './Smestuvanje/channels.json'

    dictio_list = getIssuerSiteLinksFromLocal(json_file_path, json_channels_path)

    # Emit total so Spring knows how many to expect
    print(f"TOTAL|{len(dictio_list)}", flush=True)

    if len(dictio_list) == 0:
        print("PROGRESS|100.0|Nothing to process", flush=True)
        print("DONE|0", flush=True)
        sys.exit(0)

    channels = getRSSlinksForEachIssuer(dictio_list)

    # Load models ONCE with detected device
    model = pipeline('sentiment-analysis', model='ProsusAI/finbert', device=device)
    translator = pipeline("translation", model="Helsinki-NLP/opus-mt-mk-en", device=device)

    # Create progress tracker
    progress_tracker = ProgressTracker(total_channels=len(channels))

    # Start browser ONCE — reused across all scraping
    browser_manager = BrowserManager(max_concurrent_pages=8)
    browser_manager.start()

    try:
        for idx, channel in enumerate(channels):
            process_channel(channel, model, translator, browser_manager, idx, progress_tracker)
    finally:
        browser_manager.stop()

    progress_tracker.done()

    save_channels_to_file(channels, json_channels_path)

    duration = time.time() - start_time
    print(f"DONE|{len(channels)}|Completed in {duration:.2f}s", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
