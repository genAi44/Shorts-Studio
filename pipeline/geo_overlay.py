"""
pipeline/geo_overlay.py
نظام ذكي لاكتشاف المواقع الجغرافية (الدول، المدن، العواصم) تلقائياً من النص والتعليق الصوتي،
وربطها بالتوقيت الزمني للكلمات المنطوقة، وتوليد طبقة خريطة تفاعلية سينمائية (MapOverlay) لـ Remotion.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .config import FPS
from .geo import AR_ISO3, _CITY_STOP_WORDS, detect_city_in_text, get_engine, get_geo

_TASHKEEL_RE = re.compile(r"[\u064B-\u065F\u0670\u0640]")
_PUNCT_RE = re.compile(r"[^\w\s\u0600-\u06FF]")

# قاموس معزّز للدول والكيانات الخاصة والمصغّرة بالعربية لضمان الاكتشاف الفوري 100%
_CURATED_COUNTRIES_AR: Dict[str, Dict[str, Any]] = {
    "الفاتيكان": {"iso3": "ITA", "iso2": "va", "name_ar": "الفاتيكان", "name_en": "Vatican City", "lat": 41.9029, "lon": 12.4534, "is_microstate": True},
    "مدينة الفاتيكان": {"iso3": "ITA", "iso2": "va", "name_ar": "الفاتيكان", "name_en": "Vatican City", "lat": 41.9029, "lon": 12.4534, "is_microstate": True},
    "دولة الفاتيكان": {"iso3": "ITA", "iso2": "va", "name_ar": "الفاتيكان", "name_en": "Vatican City", "lat": 41.9029, "lon": 12.4534, "is_microstate": True},
    "إيطاليا": {"iso3": "ITA", "iso2": "it", "name_ar": "إيطاليا", "name_en": "Italy", "lat": 42.8333, "lon": 12.8333},
    "ايطاليا": {"iso3": "ITA", "iso2": "it", "name_ar": "إيطاليا", "name_en": "Italy", "lat": 42.8333, "lon": 12.8333},
    "بوليفيا": {"iso3": "BOL", "iso2": "bo", "name_ar": "بوليفيا", "name_en": "Bolivia", "lat": -17.0, "lon": -65.0},
    "مصر": {"iso3": "EGY", "iso2": "eg", "name_ar": "مصر", "name_en": "Egypt", "lat": 27.0, "lon": 30.0},
    "السعودية": {"iso3": "SAU", "iso2": "sa", "name_ar": "السعودية", "name_en": "Saudi Arabia", "lat": 25.0, "lon": 45.0},
    "المملكة العربية السعودية": {"iso3": "SAU", "iso2": "sa", "name_ar": "السعودية", "name_en": "Saudi Arabia", "lat": 25.0, "lon": 45.0},
    "الإمارات": {"iso3": "ARE", "iso2": "ae", "name_ar": "الإمارات", "name_en": "UAE", "lat": 24.0, "lon": 54.0},
    "الامارات": {"iso3": "ARE", "iso2": "ae", "name_ar": "الإمارات", "name_en": "UAE", "lat": 24.0, "lon": 54.0},
    "قطر": {"iso3": "QAT", "iso2": "qa", "name_ar": "قطر", "name_en": "Qatar", "lat": 25.5, "lon": 51.25},
    "الكويت": {"iso3": "KWT", "iso2": "kw", "name_ar": "الكويت", "name_en": "Kuwait", "lat": 29.5, "lon": 47.75},
    "البحرين": {"iso3": "BHR", "iso2": "bh", "name_ar": "البحرين", "name_en": "Bahrain", "lat": 26.0, "lon": 50.55},
    "عمان": {"iso3": "OMN", "iso2": "om", "name_ar": "عُمان", "name_en": "Oman", "lat": 21.0, "lon": 57.0},
    "سلطنة عمان": {"iso3": "OMN", "iso2": "om", "name_ar": "سلطنة عُمان", "name_en": "Oman", "lat": 21.0, "lon": 57.0},
    "اليمن": {"iso3": "YEM", "iso2": "ye", "name_ar": "اليمن", "name_en": "Yemen", "lat": 15.5, "lon": 47.5},
    "العراق": {"iso3": "IRQ", "iso2": "iq", "name_ar": "العراق", "name_en": "Iraq", "lat": 33.0, "lon": 44.0},
    "سوريا": {"iso3": "SYR", "iso2": "sy", "name_ar": "سوريا", "name_en": "Syria", "lat": 35.0, "lon": 38.0},
    "الأردن": {"iso3": "JOR", "iso2": "jo", "name_ar": "الأردن", "name_en": "Jordan", "lat": 31.0, "lon": 36.0},
    "الاردن": {"iso3": "JOR", "iso2": "jo", "name_ar": "الأردن", "name_en": "Jordan", "lat": 31.0, "lon": 36.0},
    "لبنان": {"iso3": "LBN", "iso2": "lb", "name_ar": "لبنان", "name_en": "Lebanon", "lat": 33.8333, "lon": 35.8333},
    "فلسطين": {"iso3": "PSE", "iso2": "ps", "name_ar": "فلسطين", "name_en": "Palestine", "lat": 31.9, "lon": 35.2},
    "المغرب": {"iso3": "MAR", "iso2": "ma", "name_ar": "المغرب", "name_en": "Morocco", "lat": 32.0, "lon": -5.0},
    "الجزائر": {"iso3": "DZA", "iso2": "dz", "name_ar": "الجزائر", "name_en": "Algeria", "lat": 28.0, "lon": 3.0},
    "تونس": {"iso3": "TUN", "iso2": "tn", "name_ar": "تونس", "name_en": "Tunisia", "lat": 34.0, "lon": 9.0},
    "ليبيا": {"iso3": "LBY", "iso2": "ly", "name_ar": "ليبيا", "name_en": "Libya", "lat": 25.0, "lon": 17.0},
    "السودان": {"iso3": "SDN", "iso2": "sd", "name_ar": "السودان", "name_en": "Sudan", "lat": 15.0, "lon": 30.0},
    "تركيا": {"iso3": "TUR", "iso2": "tr", "name_ar": "تركيا", "name_en": "Turkey", "lat": 39.0, "lon": 35.0},
    "إيران": {"iso3": "IRN", "iso2": "ir", "name_ar": "إيران", "name_en": "Iran", "lat": 32.0, "lon": 53.0},
    "ايران": {"iso3": "IRN", "iso2": "ir", "name_ar": "إيران", "name_en": "Iran", "lat": 32.0, "lon": 53.0},
    "اليابان": {"iso3": "JPN", "iso2": "jp", "name_ar": "اليابان", "name_en": "Japan", "lat": 36.0, "lon": 138.0},
    "الصين": {"iso3": "CHN", "iso2": "cn", "name_ar": "الصين", "name_en": "China", "lat": 35.0, "lon": 105.0},
    "الهند": {"iso3": "IND", "iso2": "in", "name_ar": "الهند", "name_en": "India", "lat": 20.0, "lon": 77.0},
    "روسيا": {"iso3": "RUS", "iso2": "ru", "name_ar": "روسيا", "name_en": "Russia", "lat": 60.0, "lon": 100.0},
    "فرنسا": {"iso3": "FRA", "iso2": "fr", "name_ar": "فرنسا", "name_en": "France", "lat": 46.0, "lon": 2.0},
    "ألمانيا": {"iso3": "DEU", "iso2": "de", "name_ar": "ألمانيا", "name_en": "Germany", "lat": 51.0, "lon": 9.0},
    "المانيا": {"iso3": "DEU", "iso2": "de", "name_ar": "ألمانيا", "name_en": "Germany", "lat": 51.0, "lon": 9.0},
    "إسبانيا": {"iso3": "ESP", "iso2": "es", "name_ar": "إسبانيا", "name_en": "Spain", "lat": 40.0, "lon": -4.0},
    "اسبانيا": {"iso3": "ESP", "iso2": "es", "name_ar": "إسبانيا", "name_en": "Spain", "lat": 40.0, "lon": -4.0},
    "بريطانيا": {"iso3": "GBR", "iso2": "gb", "name_ar": "بريطانيا", "name_en": "United Kingdom", "lat": 54.0, "lon": -2.0},
    "المملكة المتحدة": {"iso3": "GBR", "iso2": "gb", "name_ar": "المملكة المتحدة", "name_en": "United Kingdom", "lat": 54.0, "lon": -2.0},
    "الولايات المتحدة": {"iso3": "USA", "iso2": "us", "name_ar": "الولايات المتحدة", "name_en": "United States", "lat": 38.0, "lon": -97.0},
    "أمريكا": {"iso3": "USA", "iso2": "us", "name_ar": "الولايات المتحدة", "name_en": "United States", "lat": 38.0, "lon": -97.0},
    "امريكا": {"iso3": "USA", "iso2": "us", "name_ar": "الولايات المتحدة", "name_en": "United States", "lat": 38.0, "lon": -97.0},
    "كندا": {"iso3": "CAN", "iso2": "ca", "name_ar": "كندا", "name_en": "Canada", "lat": 60.0, "lon": -95.0},
    "البرازيل": {"iso3": "BRA", "iso2": "br", "name_ar": "البرازيل", "name_en": "Brazil", "lat": -10.0, "lon": -55.0},
    "الأرجنتين": {"iso3": "ARG", "iso2": "ar", "name_ar": "الأرجنتين", "name_en": "Argentina", "lat": -34.0, "lon": -64.0},
    "تشيلي": {"iso3": "CHL", "iso2": "cl", "name_ar": "تشيلي", "name_en": "Chile", "lat": -30.0, "lon": -71.0},
    "بيرو": {"iso3": "PER", "iso2": "pe", "name_ar": "بيرو", "name_en": "Peru", "lat": -10.0, "lon": -76.0},
    "جنوب أفريقيا": {"iso3": "ZAF", "iso2": "za", "name_ar": "جنوب أفريقيا", "name_en": "South Africa", "lat": -29.0, "lon": 24.0},
    "إثيوبيا": {"iso3": "ETH", "iso2": "et", "name_ar": "إثيوبيا", "name_en": "Ethiopia", "lat": 8.0, "lon": 38.0},
    "أستراليا": {"iso3": "AUS", "iso2": "au", "name_ar": "أستراليا", "name_en": "Australia", "lat": -27.0, "lon": 133.0},
}

# قاموس معزّز لأشهر العواصم والمدن العالمية لضمان الدقة الفورية حتى مع اختلاف الهمزات أو التصريف
_CURATED_CITIES_AR: Dict[str, Dict[str, Any]] = {
    "سوكري": {"name_ar": "سوكري", "name_en": "Sucre", "country_ar": "بوليفيا", "iso3": "BOL", "iso2": "bo", "lat": -19.0196, "lon": -65.2619, "is_capital": True},
    "لاباز": {"name_ar": "لاباز", "name_en": "La Paz", "country_ar": "بوليفيا", "iso3": "BOL", "iso2": "bo", "lat": -16.4897, "lon": -68.1193, "is_capital": True},
    "لا باز": {"name_ar": "لاباز", "name_en": "La Paz", "country_ar": "بوليفيا", "iso3": "BOL", "iso2": "bo", "lat": -16.4897, "lon": -68.1193, "is_capital": True},
    "روما": {"name_ar": "روما", "name_en": "Rome", "country_ar": "إيطاليا", "iso3": "ITA", "iso2": "it", "lat": 41.9028, "lon": 12.4964, "is_capital": True},
    "البندقية": {"name_ar": "البندقية", "name_en": "Venice", "country_ar": "إيطاليا", "iso3": "ITA", "iso2": "it", "lat": 45.4408, "lon": 12.3155, "is_capital": False},
    "طوكيو": {"name_ar": "طوكيو", "name_en": "Tokyo", "country_ar": "اليابان", "iso3": "JPN", "iso2": "jp", "lat": 35.6762, "lon": 139.6503, "is_capital": True},
    "القاهرة": {"name_ar": "القاهرة", "name_en": "Cairo", "country_ar": "مصر", "iso3": "EGY", "iso2": "eg", "lat": 30.0444, "lon": 31.2357, "is_capital": True},
    "الإسكندرية": {"name_ar": "الإسكندرية", "name_en": "Alexandria", "country_ar": "مصر", "iso3": "EGY", "iso2": "eg", "lat": 31.2001, "lon": 29.9187, "is_capital": False},
    "الرياض": {"name_ar": "الرياض", "name_en": "Riyadh", "country_ar": "السعودية", "iso3": "SAU", "iso2": "sa", "lat": 24.7136, "lon": 46.6753, "is_capital": True},
    "جدة": {"name_ar": "جدة", "name_en": "Jeddah", "country_ar": "السعودية", "iso3": "SAU", "iso2": "sa", "lat": 21.4858, "lon": 39.1925, "is_capital": False},
    "مكة": {"name_ar": "مكة المكرمة", "name_en": "Mecca", "country_ar": "السعودية", "iso3": "SAU", "iso2": "sa", "lat": 21.3891, "lon": 39.8579, "is_capital": False},
    "المدينة المنورة": {"name_ar": "المدينة المنورة", "name_en": "Medina", "country_ar": "السعودية", "iso3": "SAU", "iso2": "sa", "lat": 24.5247, "lon": 39.5692, "is_capital": False},
    "أبوظبي": {"name_ar": "أبوظبي", "name_en": "Abu Dhabi", "country_ar": "الإمارات", "iso3": "ARE", "iso2": "ae", "lat": 24.4539, "lon": 54.3773, "is_capital": True},
    "ابوظبي": {"name_ar": "أبوظبي", "name_en": "Abu Dhabi", "country_ar": "الإمارات", "iso3": "ARE", "iso2": "ae", "lat": 24.4539, "lon": 54.3773, "is_capital": True},
    "دبي": {"name_ar": "دبي", "name_en": "Dubai", "country_ar": "الإمارات", "iso3": "ARE", "iso2": "ae", "lat": 25.2048, "lon": 55.2708, "is_capital": False},
    "الدوحة": {"name_ar": "الدوحة", "name_en": "Doha", "country_ar": "قطر", "iso3": "QAT", "iso2": "qa", "lat": 25.2854, "lon": 51.5310, "is_capital": True},
    "بغداد": {"name_ar": "بغداد", "name_en": "Baghdad", "country_ar": "العراق", "iso3": "IRQ", "iso2": "iq", "lat": 33.3152, "lon": 44.3661, "is_capital": True},
    "دمشق": {"name_ar": "دمشق", "name_en": "Damascus", "country_ar": "سوريا", "iso3": "SYR", "iso2": "sy", "lat": 33.5138, "lon": 36.2765, "is_capital": True},
    "القدس": {"name_ar": "القدس", "name_en": "Jerusalem", "country_ar": "فلسطين", "iso3": "PSE", "iso2": "ps", "lat": 31.7683, "lon": 35.2137, "is_capital": True},
    "بيروت": {"name_ar": "بيروت", "name_en": "Beirut", "country_ar": "لبنان", "iso3": "LBN", "iso2": "lb", "lat": 33.8938, "lon": 35.5018, "is_capital": True},
    "عمان": {"name_ar": "عمّان", "name_en": "Amman", "country_ar": "الأردن", "iso3": "JOR", "iso2": "jo", "lat": 31.9454, "lon": 35.9284, "is_capital": True},
    "الرباط": {"name_ar": "الرباط", "name_en": "Rabat", "country_ar": "المغرب", "iso3": "MAR", "iso2": "ma", "lat": 34.0209, "lon": -6.8416, "is_capital": True},
    "الدار البيضاء": {"name_ar": "الدار البيضاء", "name_en": "Casablanca", "country_ar": "المغرب", "iso3": "MAR", "iso2": "ma", "lat": 33.5731, "lon": -7.5898, "is_capital": False},
    "إسطنبول": {"name_ar": "إسطنبول", "name_en": "Istanbul", "country_ar": "تركيا", "iso3": "TUR", "iso2": "tr", "lat": 41.0082, "lon": 28.9784, "is_capital": False},
    "اسطنبول": {"name_ar": "إسطنبول", "name_en": "Istanbul", "country_ar": "تركيا", "iso3": "TUR", "iso2": "tr", "lat": 41.0082, "lon": 28.9784, "is_capital": False},
    "أنقرة": {"name_ar": "أنقرة", "name_en": "Ankara", "country_ar": "تركيا", "iso3": "TUR", "iso2": "tr", "lat": 39.9334, "lon": 32.8597, "is_capital": True},
    "باريس": {"name_ar": "باريس", "name_en": "Paris", "country_ar": "فرنسا", "iso3": "FRA", "iso2": "fr", "lat": 48.8566, "lon": 2.3522, "is_capital": True},
    "لندن": {"name_ar": "لندن", "name_en": "London", "country_ar": "بريطانيا", "iso3": "GBR", "iso2": "gb", "lat": 51.5072, "lon": -0.1276, "is_capital": True},
    "برلين": {"name_ar": "برلين", "name_en": "Berlin", "country_ar": "ألمانيا", "iso3": "DEU", "iso2": "de", "lat": 52.5200, "lon": 13.4050, "is_capital": True},
    "مدريد": {"name_ar": "مدريد", "name_en": "Madrid", "country_ar": "إسبانيا", "iso3": "ESP", "iso2": "es", "lat": 40.4168, "lon": -3.7038, "is_capital": True},
    "موسكو": {"name_ar": "موسكو", "name_en": "Moscow", "country_ar": "روسيا", "iso3": "RUS", "iso2": "ru", "lat": 55.7558, "lon": 37.6173, "is_capital": True},
    "بكين": {"name_ar": "بكين", "name_en": "Beijing", "country_ar": "الصين", "iso3": "CHN", "iso2": "cn", "lat": 39.9042, "lon": 116.4074, "is_capital": True},
    "شنغهاي": {"name_ar": "شنغهاي", "name_en": "Shanghai", "country_ar": "الصين", "iso3": "CHN", "iso2": "cn", "lat": 31.2304, "lon": 121.4737, "is_capital": False},
    "دلهي": {"name_ar": "نيودلهي", "name_en": "New Delhi", "country_ar": "الهند", "iso3": "IND", "iso2": "in", "lat": 28.6139, "lon": 77.2090, "is_capital": True},
    "نيودلهي": {"name_ar": "نيودلهي", "name_en": "New Delhi", "country_ar": "الهند", "iso3": "IND", "iso2": "in", "lat": 28.6139, "lon": 77.2090, "is_capital": True},
    "واشنطن العاصمة": {"name_ar": "واشنطن العاصمة", "name_en": "Washington, D.C.", "country_ar": "الولايات المتحدة", "iso3": "USA", "iso2": "us", "lat": 38.9072, "lon": -77.0369, "is_capital": True},
    "واشنطن": {"name_ar": "واشنطن العاصمة", "name_en": "Washington, D.C.", "country_ar": "الولايات المتحدة", "iso3": "USA", "iso2": "us", "lat": 38.9072, "lon": -77.0369, "is_capital": True},
    "نيويورك": {"name_ar": "نيويورك", "name_en": "New York", "country_ar": "الولايات المتحدة", "iso3": "USA", "iso2": "us", "lat": 40.7128, "lon": -74.0060, "is_capital": False},
    "برازيليا": {"name_ar": "برازيليا", "name_en": "Brasília", "country_ar": "البرازيل", "iso3": "BRA", "iso2": "br", "lat": -15.7975, "lon": -47.8919, "is_capital": True},
    "ريو دي جانيرو": {"name_ar": "ريو دي جانيرو", "name_en": "Rio de Janeiro", "country_ar": "البرازيل", "iso3": "BRA", "iso2": "br", "lat": -22.9068, "lon": -43.1729, "is_capital": False},
    "ساو باولو": {"name_ar": "ساو باولو", "name_en": "São Paulo", "country_ar": "البرازيل", "iso3": "BRA", "iso2": "br", "lat": -23.5505, "lon": -46.6333, "is_capital": False},
    "بريتوريا": {"name_ar": "بريتوريا", "name_en": "Pretoria", "country_ar": "جنوب أفريقيا", "iso3": "ZAF", "iso2": "za", "lat": -25.7479, "lon": 28.2293, "is_capital": True},
    "كيب تاون": {"name_ar": "كيب تاون", "name_en": "Cape Town", "country_ar": "جنوب أفريقيا", "iso3": "ZAF", "iso2": "za", "lat": -33.9249, "lon": 18.4241, "is_capital": True},
}

# القارات السبع مع دول ممثلة لتحديد إطار القارة وإبراز حدودها عند ذكر أي قارة
_CURATED_CONTINENTS_AR: Dict[str, Dict[str, Any]] = {
    "أمريكا الجنوبية": {"name_ar": "أمريكا الجنوبية", "name_en": "South America", "iso3": "BRA", "continent_isos": ["BRA", "ARG", "BOL", "PER", "COL", "CHL"], "lat": -14.0, "lon": -60.0},
    "أمريكا الشمالية": {"name_ar": "أمريكا الشمالية", "name_en": "North America", "iso3": "USA", "continent_isos": ["USA", "CAN", "MEX"], "lat": 42.0, "lon": -98.0},
    "أوروبا": {"name_ar": "أوروبا", "name_en": "Europe", "iso3": "DEU", "continent_isos": ["FRA", "DEU", "ITA", "ESP", "POL", "GBR"], "lat": 49.0, "lon": 12.0},
    "آسيا": {"name_ar": "آسيا", "name_en": "Asia", "iso3": "CHN", "continent_isos": ["CHN", "IND", "SAU", "TUR", "JPN", "IRN"], "lat": 34.0, "lon": 90.0},
    "أفريقيا": {"name_ar": "أفريقيا", "name_en": "Africa", "iso3": "EGY", "continent_isos": ["EGY", "DZA", "NGA", "ETH", "ZAF", "COD"], "lat": 4.0, "lon": 20.0},
    "إفريقيا": {"name_ar": "إفريقيا", "name_en": "Africa", "iso3": "EGY", "continent_isos": ["EGY", "DZA", "NGA", "ETH", "ZAF", "COD"], "lat": 4.0, "lon": 20.0},
    "أوقيانوسيا": {"name_ar": "أوقيانوسيا", "name_en": "Oceania", "iso3": "AUS", "continent_isos": ["AUS", "NZL", "PNG"], "lat": -25.0, "lon": 135.0},
}

# المعالم والممرات المائية والأحداث المرتبطة بمواقع جغرافية محددة
_CURATED_LANDMARKS_AR: Dict[str, Dict[str, Any]] = {
    "قناة السويس": {"name_ar": "قناة السويس", "name_en": "Suez Canal", "country_ar": "مصر", "iso3": "EGY", "iso2": "eg", "lat": 30.5852, "lon": 32.2654},
    "مضيق البوسفور": {"name_ar": "مضيق البوسفور", "name_en": "Bosphorus Strait", "country_ar": "تركيا", "iso3": "TUR", "iso2": "tr", "lat": 41.1194, "lon": 29.0750},
    "البوسفور": {"name_ar": "مضيق البوسفور", "name_en": "Bosphorus Strait", "country_ar": "تركيا", "iso3": "TUR", "iso2": "tr", "lat": 41.1194, "lon": 29.0750},
    "جدار برلين": {"name_ar": "جدار برلين", "name_en": "Berlin Wall", "country_ar": "ألمانيا", "iso3": "DEU", "iso2": "de", "lat": 52.5163, "lon": 13.3777},
    "الأهرامات": {"name_ar": "أهرامات الجيزة", "name_en": "Giza Pyramids", "country_ar": "مصر", "iso3": "EGY", "iso2": "eg", "lat": 29.9792, "lon": 31.1342},
    "برج إيفل": {"name_ar": "برج إيفل", "name_en": "Eiffel Tower", "country_ar": "فرنسا", "iso3": "FRA", "iso2": "fr", "lat": 48.8584, "lon": 2.2945},
    "نهر النيل": {"name_ar": "نهر النيل", "name_en": "Nile River", "country_ar": "مصر", "iso3": "EGY", "iso2": "eg", "lat": 26.8206, "lon": 30.8025},
    "مضيق جبل طارق": {"name_ar": "مضيق جبل طارق", "name_en": "Strait of Gibraltar", "country_ar": "المغرب / إسبانيا", "iso3": "MAR", "iso2": "ma", "lat": 35.9667, "lon": -5.6167},
    "البحر الأحمر": {"name_ar": "البحر الأحمر", "name_en": "Red Sea", "country_ar": "مصر / السعودية", "iso3": "EGY", "iso2": "eg", "lat": 22.0, "lon": 38.0},
    "البحر المتوسط": {"name_ar": "البحر المتوسط", "name_en": "Mediterranean Sea", "country_ar": "حوض المتوسط", "iso3": "ITA", "iso2": "it", "lat": 35.5, "lon": 18.0},
    "الأندلس": {"name_ar": "الأندلس", "name_en": "Al-Andalus (Iberia)", "country_ar": "إسبانيا", "iso3": "ESP", "iso2": "es", "lat": 37.3891, "lon": -5.9845},
    "وادي لكة": {"name_ar": "معركة وادي لكة", "name_en": "Battle of Guadalete", "country_ar": "إسبانيا", "iso3": "ESP", "iso2": "es", "lat": 36.25, "lon": -5.95},
    "البتراء": {"name_ar": "البتراء", "name_en": "Petra", "country_ar": "الأردن", "iso3": "JOR", "iso2": "jo", "lat": 30.3285, "lon": 35.4444},
    "سور الصين العظيم": {"name_ar": "سور الصين العظيم", "name_en": "Great Wall of China", "country_ar": "الصين", "iso3": "CHN", "iso2": "cn", "lat": 40.4319, "lon": 116.5704},
    "سور الصين": {"name_ar": "سور الصين العظيم", "name_en": "Great Wall of China", "country_ar": "الصين", "iso3": "CHN", "iso2": "cn", "lat": 40.4319, "lon": 116.5704},
    "القسطنطينية": {"name_ar": "القسطنطينية (إسطنبول)", "name_en": "Constantinople", "country_ar": "تركيا", "iso3": "TUR", "iso2": "tr", "lat": 41.0082, "lon": 28.9784},
    "ستالينغراد": {"name_ar": "ستالينغراد", "name_en": "Stalingrad", "country_ar": "روسيا", "iso3": "RUS", "iso2": "ru", "lat": 48.7080, "lon": 44.5133},
    "نورماندي": {"name_ar": "سواحل نورماندي", "name_en": "Normandy", "country_ar": "فرنسا", "iso3": "FRA", "iso2": "fr", "lat": 49.3697, "lon": -0.8711},
    "حطين": {"name_ar": "معركة حطين", "name_en": "Hattin", "country_ar": "فلسطين", "iso3": "PSE", "iso2": "ps", "lat": 32.8011, "lon": 35.4608},
    "عين جالوت": {"name_ar": "معركة عين جالوت", "name_en": "Ain Jalut", "country_ar": "فلسطين", "iso3": "PSE", "iso2": "ps", "lat": 32.5594, "lon": 35.3514},
    "اليرموك": {"name_ar": "معركة اليرموك", "name_en": "Battle of Yarmouk", "country_ar": "الأردن", "iso3": "JOR", "iso2": "jo", "lat": 32.7536, "lon": 35.8719},
    "القادسية": {"name_ar": "معركة القادسية", "name_en": "al-Qadisiyyah", "country_ar": "العراق", "iso3": "IRQ", "iso2": "iq", "lat": 31.6531, "lon": 44.3314},
    "واترلو": {"name_ar": "معركة واترلو", "name_en": "Waterloo", "country_ar": "بلجيكا", "iso3": "BEL", "iso2": "be", "lat": 50.6800, "lon": 4.4117},
    "غرناطة": {"name_ar": "غرناطة", "name_en": "Granada", "country_ar": "إسبانيا", "iso3": "ESP", "iso2": "es", "lat": 37.1773, "lon": -3.5986},
    "تاج محل": {"name_ar": "تاج محل", "name_en": "Taj Mahal", "country_ar": "الهند", "iso3": "IND", "iso2": "in", "lat": 27.1751, "lon": 78.0421},
    "الكولوسيوم": {"name_ar": "الكولوسيوم", "name_en": "Colosseum", "country_ar": "إيطاليا", "iso3": "ITA", "iso2": "it", "lat": 41.8902, "lon": 12.4922},
    "الحرب العالمية الثانية": {"name_ar": "أوروبا — الحرب العالمية الثانية", "name_en": "WWII Europe", "country_ar": "أوروبا", "iso3": "DEU", "iso2": "de", "lat": 51.1657, "lon": 10.4515},
    "الحرب العالمية الأولى": {"name_ar": "أوروبا — الحرب العالمية الأولى", "name_en": "WWI Europe", "country_ar": "فرنسا", "iso3": "FRA", "iso2": "fr", "lat": 49.15, "lon": 4.0},
    "الحرب الباردة": {"name_ar": "برلين — الحرب الباردة", "name_en": "Berlin Cold War", "country_ar": "ألمانيا", "iso3": "DEU", "iso2": "de", "lat": 52.5200, "lon": 13.4050},
}

# الكرة الأرضية / العالم: خريطة عالمية بدول ممثِّلة من كل القارات
_CURATED_WORLD_AR: Dict[str, Dict[str, Any]] = {
    k: {"name_ar": k, "name_en": "World", "iso3": "EGY", "continent_isos": ["USA", "BRA", "EGY", "ZAF", "RUS", "CHN", "IND", "AUS", "FRA"], "lat": 20.0, "lon": 10.0}
    for k in ("الكرة الأرضية", "كوكب الأرض", "خريطة العالم", "العالم بأسره", "أنحاء العالم")
}

_COMMON_NOUN_CITY_STOPWORDS = {
    "العبور", "عبور", "السلام", "سلام", "النصر", "نصر", "الفتح", "فتح",
    "التحرير", "تحرير", "الثورة", "ثورة", "الشروق", "شروق", "الأمل", "أمل",
    "الرحاب", "البدر", "الفيصل", "المدينة", "مدينة", "العاصمة", "عاصمة",
    "المحيط", "البحر", "النهر", "الشمال", "الجنوب", "الشرق", "الغرب", "الوسط",
    "الخليج", "الجمهورية", "المملكة", "الدولة", "الإسلامية", "المسلمين",
    "دولا", "دولاً", "دول", "أخرى", "عالمي", "مركز", "ميناء", "جزيرة",
    "خفي", "خفية", "حديثة", "حديثا", "حديثاً", "قديم", "قديمة", "عظيم", "عظيمة",
    "كبير", "كبيرة", "صغير", "صغيرة", "جديد", "جديدة", "أبيض", "أسود", "أحمر",
}


def _norm_token(s: str) -> str:
    if not s:
        return ""
    s = _TASHKEEL_RE.sub("", str(s))
    s = _PUNCT_RE.sub("", s)
    return s.strip()


def _format_gps(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.1f}°{ns} {abs(lon):.1f}°{ew}"


def _d_svg(xy: np.ndarray, min_d: float = 1.6) -> str:
    out, last = [], None
    for x, y in xy:
        if last is None or (x - last[0]) ** 2 + (y - last[1]) ** 2 >= min_d ** 2:
            out.append((float(x), float(y)))
            last = (float(x), float(y))
    if len(out) < 3:
        return ""
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in out) + "Z"


def _find_word_timestamp(
    mention_token: str,
    words: List[Dict[str, Any]],
    scene_dur_sec: float,
    fallback_ratio: float = 0.15,
) -> Tuple[float, float, int]:
    """Finds the exact (start_sec, end_sec, word_index) where `mention_token` is spoken in `words`."""
    norm_target = _norm_token(mention_token)
    if not norm_target or not words:
        t_start = round(scene_dur_sec * fallback_ratio, 3)
        return t_start, min(scene_dur_sec, t_start + 1.8), 0

    target_parts = [p for p in norm_target.split() if p]
    first_part = target_parts[0] if target_parts else norm_target

    for idx, w in enumerate(words):
        wt = _norm_token(w.get("t", ""))
        if not wt:
            continue
        # Match exact or with single-letter Arabic prefix (و، ب، ل، ف، ك)
        if (
            wt == first_part
            or (len(wt) >= 4 and wt[0] in ("و", "ب", "ل", "ف", "ك") and wt[1:] == first_part)
            or (len(first_part) >= 4 and first_part in wt)
        ):
            s_sec = float(w.get("s", 0.0))
            e_sec = float(w.get("e", s_sec + 0.6))
            if len(target_parts) > 1 and idx + 1 < len(words):
                e_sec = float(words[idx + 1].get("e", e_sec))
            return s_sec, e_sec, idx

    t_start = round(scene_dur_sec * fallback_ratio, 3)
    return t_start, min(scene_dur_sec, t_start + 1.8), 0


def extract_timed_geo_mentions(
    narration: str,
    on_screen: str,
    words: List[Dict[str, Any]],
    dur_frames: int,
) -> List[Dict[str, Any]]:
    """
    Automatically extracts all countries, capitals, and cities mentioned in `narration` (and `on_screen`),
    determines their accurate geographic coordinates and classification (`capital`, `city`, `country`),
    and aligns each mention with the exact spoken word timestamp in `words`.
    """
    combined = f"{narration or ''} {on_screen or ''}".strip()
    if not combined:
        return []

    clean_text = _TASHKEEL_RE.sub("", combined)
    scene_dur_sec = max(1.0, dur_frames / float(FPS))
    engine = get_engine()
    geo = get_geo()

    mentions: List[Dict[str, Any]] = []
    seen_keys = set()

    def _register_mention(
        matched_str: str,
        kind: str,
        name_ar: str,
        name_en: str,
        country_ar: str,
        iso3: str,
        iso2: str,
        lat: float,
        lon: float,
        is_microstate: bool = False,
    ):
        dedup_key = (kind, name_ar, round(lat, 1), round(lon, 1))
        if dedup_key in seen_keys:
            return
        # Avoid registering both a city and a country with the exact same name (e.g. الفاتيكان / تونس / الجزائر)
        for existing in mentions:
            if existing["name_ar"] == name_ar:
                return
        seen_keys.add(dedup_key)

        fallback_r = min(0.75, 0.10 + len(mentions) * 0.28)
        s_sec, e_sec, w_idx = _find_word_timestamp(matched_str, words, scene_dur_sec, fallback_ratio=fallback_r)
        char_pos = clean_text.find(matched_str)
        if char_pos < 0:
            char_pos = 9999

        kind_label = (
            "عاصمة" if kind == "capital"
            else ("مدينة" if kind == "city"
            else ("قارة" if kind == "continent"
            else ("العالم" if kind == "world"
            else ("معلم" if kind == "landmark" else "دولة"))))
        )
        mentions.append({
            "matched_token": matched_str,
            "kind": kind,
            "kind_label": kind_label,
            "name_ar": name_ar,
            "name_en": name_en,
            "country_ar": country_ar,
            "iso3": (iso3 or "").upper(),
            "iso2": (iso2 or "").lower(),
            "lat": float(lat),
            "lon": float(lon),
            "coords": _format_gps(float(lat), float(lon)),
            "is_microstate": bool(is_microstate),
            "start_sec": round(s_sec, 3),
            "end_sec": round(e_sec, 3),
            "word_index": w_idx,
            "char_pos": char_pos,
        })

    # 1. Check curated cities & capitals first (longest match first)
    for city_key in sorted(_CURATED_CITIES_AR.keys(), key=len, reverse=True):
        pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(city_key)}(?:$|[\s،؟!.,:؛\-])")
        if pat.search(clean_text):
            cinfo = _CURATED_CITIES_AR[city_key]
            # Disambiguate "عمان" (Amman vs Oman) by context
            if city_key == "عمان" and ("سلطنة" in clean_text or "خليج" in clean_text or "مسقط" in clean_text):
                continue
            _register_mention(
                matched_str=city_key,
                kind="capital" if cinfo.get("is_capital") else "city",
                name_ar=cinfo["name_ar"],
                name_en=cinfo["name_en"],
                country_ar=cinfo["country_ar"],
                iso3=cinfo["iso3"],
                iso2=cinfo["iso2"],
                lat=cinfo["lat"],
                lon=cinfo["lon"],
            )

    # 1b. Check curated landmarks, waterways & geo-historical sites
    for lm_key in sorted(_CURATED_LANDMARKS_AR.keys(), key=len, reverse=True):
        pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(lm_key)}(?:$|[\s،؟!.,:؛\-])")
        if pat.search(clean_text):
            linfo = _CURATED_LANDMARKS_AR[lm_key]
            _register_mention(
                matched_str=lm_key,
                kind="landmark",
                name_ar=linfo["name_ar"],
                name_en=linfo["name_en"],
                country_ar=linfo["country_ar"],
                iso3=linfo["iso3"],
                iso2=linfo["iso2"],
                lat=linfo["lat"],
                lon=linfo["lon"],
            )

    # 2. Check curated countries & microstates
    for country_key in sorted(_CURATED_COUNTRIES_AR.keys(), key=len, reverse=True):
        pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(country_key)}(?:$|[\s،؟!.,:؛\-])")
        if pat.search(clean_text):
            # Disambiguate "أمريكا" (USA) vs continent names ("أمريكا الجنوبية / الشمالية / اللاتينية / الوسطى")
            if country_key in ("أمريكا", "امريكا") and re.search(
                r"(?:أمريكا|امريكا)\s+(?:الجنوبية|الشمالية|اللاتينية|الوسطى)",
                clean_text,
            ):
                continue
            cinfo = _CURATED_COUNTRIES_AR[country_key]
            _register_mention(
                matched_str=country_key,
                kind="country",
                name_ar=cinfo["name_ar"],
                name_en=cinfo["name_en"],
                country_ar=cinfo["name_ar"],
                iso3=cinfo["iso3"],
                iso2=cinfo["iso2"],
                lat=cinfo["lat"],
                lon=cinfo["lon"],
                is_microstate=bool(cinfo.get("is_microstate")),
            )

    # 2a. الكرة الأرضية / العالم
    for wk in _CURATED_WORLD_AR:
        if wk in clean_text and not mentions:
            w = _CURATED_WORLD_AR[wk]
            _register_mention(wk, "world", w["name_ar"], w["name_en"], w["name_ar"], w["iso3"], "", w["lat"], w["lon"])
            mentions[-1]["continent_isos"] = list(w["continent_isos"])
            break

    # 2b. Check continents (if no more specific country/city/landmark already found, or alongside)
    if len(mentions) < 3:
        for cont_key in sorted(_CURATED_CONTINENTS_AR.keys(), key=len, reverse=True):
            pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلفك]){re.escape(cont_key)}(?:$|[\s،؟!.,:؛\-])")
            if pat.search(clean_text):
                cinfo = _CURATED_CONTINENTS_AR[cont_key]
                _register_mention(
                    matched_str=cont_key,
                    kind="continent",
                    name_ar=cinfo["name_ar"],
                    name_en=cinfo["name_en"],
                    country_ar=cinfo["name_ar"],
                    iso3=cinfo["iso3"],
                    iso2="",
                    lat=cinfo["lat"],
                    lon=cinfo["lon"],
                )
                if mentions:
                    mentions[-1]["continent_isos"] = list(cinfo.get("continent_isos") or [])

    # 3. Dynamic database scan for any other country in AR_ISO3
    if len(mentions) < 4:
        for ar_name, iso3 in sorted(AR_ISO3.items(), key=lambda x: len(x[0]), reverse=True):
            if len(ar_name) < 3 or not re.search(r"[\u0600-\u06FF]", ar_name):
                continue
            if ar_name in _CITY_STOP_WORDS:
                continue
            if ar_name in ("أمريكا", "امريكا") and re.search(
                r"(?:أمريكا|امريكا)\s+(?:الجنوبية|الشمالية|اللاتينية|الوسطى)",
                clean_text,
            ):
                continue
            pat = re.compile(rf"(?:^|[\s،؟!.,:؛\-وبلف]){re.escape(ar_name)}(?:$|[\s،؟!.,:؛\-])")
            if pat.search(clean_text) and geo.has(iso3):
                bb = geo.main_bbox(iso3)
                lon_c = (bb[0] + bb[2]) / 2.0
                lat_c = (bb[1] + bb[3]) / 2.0
                c_row = engine.get_country(iso3) if engine else None
                iso2 = (c_row.iso2 if c_row else iso3[:2]).lower()
                en_name = (c_row.name_en if c_row else geo.c[iso3].get("name", iso3))
                _register_mention(
                    matched_str=ar_name,
                    kind="country",
                    name_ar=ar_name,
                    name_en=en_name,
                    country_ar=ar_name,
                    iso3=iso3,
                    iso2=iso2,
                    lat=lat_c,
                    lon=lon_c,
                )
                if len(mentions) >= 4:
                    break

    # 4. Token-level city/capital lookup in geodata.db for any remaining cities
    if len(mentions) < 4:
        raw_tokens = [_norm_token(tok) for tok in clean_text.split()]
        raw_tokens = [t for t in raw_tokens if len(t) >= 3 and t not in _CITY_STOP_WORDS]
        candidates: List[str] = []
        for i in range(len(raw_tokens)):
            if i + 1 < len(raw_tokens):
                candidates.append(f"{raw_tokens[i]} {raw_tokens[i + 1]}")
            candidates.append(raw_tokens[i])
            if len(raw_tokens[i]) >= 5 and raw_tokens[i][0] in ("و", "ب", "ل", "ف"):
                stripped = raw_tokens[i][1:]
                if stripped not in _CITY_STOP_WORDS:
                    candidates.append(stripped)

        for cand in candidates:
            if len(mentions) >= 4:
                break
            norm_cand = _norm_token(cand)
            if norm_cand in _CITY_STOP_WORDS or norm_cand in _COMMON_NOUN_CITY_STOPWORDS:
                continue
            cn, ci = detect_city_in_text(cand)
            if cn and (_norm_token(cn) in _COMMON_NOUN_CITY_STOPWORDS):
                continue
            if cn and ci and "lat" in ci and "lon" in ci:
                pop = int(ci.get("pop") or ci.get("population") or 0)
                is_cap = bool(ci.get("is_capital"))
                has_city_prefix = bool(re.search(rf"مدينة\s+{re.escape(cand)}", clean_text))
                if not is_cap and pop < 500_000 and not has_city_prefix:
                    continue
                iso3 = str(ci.get("iso") or "").upper()
                iso2 = str(ci.get("iso2") or iso3[:2]).lower()
                c_row = engine.get_country(iso3) if (engine and iso3) else None
                country_ar = (c_row.name_ar if (c_row and c_row.name_ar) else str(ci.get("country") or ""))
                _register_mention(
                    matched_str=cand,
                    kind="capital" if ci.get("is_capital") else "city",
                    name_ar=str(ci.get("name") or cn),
                    name_en=str(ci.get("en") or cn),
                    country_ar=country_ar,
                    iso3=iso3,
                    iso2=iso2,
                    lat=float(ci["lat"]),
                    lon=float(ci["lon"]),
                )

    # 5. قرية/بلدة + اسم: بحث مباشر بلا فلتر حجم السكان
    if len(mentions) < 4 and engine is not None:
        for m_ in re.finditer(r"(?:قرية|بلدة|قرى)\s+((?:ال)?[؀-ۿ]+(?:\s[؀-ۿ]+)?)", clean_text):
            if len(mentions) >= 4:
                break
            parts = m_.group(1).split()
            for cand in dict.fromkeys([" ".join(parts), parts[0]]):
                try:
                    pl = engine._match_exact_ar(cand, None) or engine._match_altname(cand, "ar", None)
                except Exception:
                    pl = None
                if pl and pl.lat is not None and pl.lon is not None:
                    _register_mention(cand, "city", pl.name_ar or cand, pl.name_en or cand, pl.country_ar or "", pl.country_iso3 or "", pl.country_iso2 or "", float(pl.lat), float(pl.lon))
                    break

    # Sort mentions in chronological spoken order (by start_sec, then char_pos)
    mentions.sort(key=lambda m: (m["start_sec"], m["char_pos"]))
    return mentions[:4]


def build_scene_map_overlay(
    sc: Dict[str, Any],
    words: List[Dict[str, Any]],
    dur_frames: int,
    geo: Any = None,
    scene_idx: int = 0,
    prev_overlay: Optional[Dict[str, Any]] = None,
    inherited_locations: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Builds a complete, self-contained `map_overlay` specification for a Remotion Scene
    whenever countries, capitals, or cities are mentioned in the scene's narration.
    Falls back to `inherited_locations` from Visual Context Memory when the scene
    continues talking about the same place without repeating its name.
    Returns `None` if no geographic locations are mentioned or inherited.
    """
    role = str(sc.get("role") or "")
    narration = str(sc.get("narration") or sc.get("text") or "")
    on_screen = str(sc.get("on_screen") or sc.get("title") or "")

    mentions = extract_timed_geo_mentions(narration, on_screen, words, dur_frames)
    if not mentions and inherited_locations and role not in ("cta", "loop"):
        inh_text = " ".join(str(loc.get("name_ar") or "") for loc in inherited_locations[:2] if isinstance(loc, dict))
        if inh_text.strip():
            mentions = extract_timed_geo_mentions(inh_text, "", words, dur_frames)
    if not mentions:
        return None

    # Render the overlay on every scene where a country, capital, or city is mentioned
    if role == "loop" and not any(m["kind"] in ("capital", "city", "country") for m in mentions):
        return None

    if geo is None:
        geo = get_geo()

    # Collect ISO3 codes and point coordinates for viewport projection (840x520 high-res local SVG box)
    W_BOX, H_BOX = 840.0, 520.0
    CX_BOX, CY_BOX = W_BOX / 2.0, H_BOX / 2.0

    # Map each ISO3 to its primary capital/city mention in this scene (if any)
    city_by_iso3: Dict[str, Dict[str, Any]] = {}
    distinct_cities: List[str] = []
    for m in mentions:
        if m.get("kind") in ("capital", "city"):
            iso_k = m.get("iso3") or ""
            if iso_k and iso_k not in city_by_iso3:
                city_by_iso3[iso_k] = m
            c_name = str(m.get("name_ar") or "")
            if c_name and c_name not in distinct_cities:
                distinct_cities.append(c_name)

    isos: List[str] = []
    pts_for_view: List[Dict[str, float]] = []
    for m in mentions:
        for c_iso in (m.get("continent_isos") or []):
            if c_iso and geo.has(c_iso) and c_iso not in isos:
                isos.append(c_iso)
        iso3 = m.get("iso3") or ""
        if iso3 and geo.has(iso3) and iso3 not in isos:
            isos.append(iso3)
        # If this is a country mention and we already have a city/capital in the same country,
        # use the city coordinates so the country centroid doesn't skew the pin or bbox.
        ref_m = city_by_iso3.get(iso3, m) if m.get("kind") == "country" else m
        pts_for_view.append({"lat": float(ref_m["lat"]), "lon": float(ref_m["lon"])})

    # Include previous overlay's last point ONLY if continuing within the exact same country (iso3)
    prev_wp = None
    if isinstance(prev_overlay, dict) and prev_overlay.get("waypoints"):
        last_prev = prev_overlay["waypoints"][-1]
        prev_iso = str(last_prev.get("iso3") or "")
        first_iso = str(mentions[0].get("iso3") or "")
        dist_deg = math.hypot(
            float(last_prev.get("lat", 0.0)) - float(mentions[0]["lat"]),
            float(last_prev.get("lon", 0.0)) - float(mentions[0]["lon"]),
        )
        if prev_iso and prev_iso == first_iso and 0.05 < dist_deg <= 25.0:
            prev_wp = last_prev
            pts_for_view.insert(0, {"lat": float(last_prev["lat"]), "lon": float(last_prev["lon"])})

    view = geo.view_for(isos, pts_for_view, bw=688, bh=412, smax=440, pad=0.24)
    S, K, lonc, latc = view["S"], view["K"], view["lonc"], view["latc"]

    def proj_xy(lon_val: float, lat_val: float) -> Tuple[float, float]:
        px = CX_BOX + (lon_val - lonc) * S * K
        py = CY_BOX - (lat_val - latc) * S
        return round(float(px), 1), round(float(py), 1)

    def proj_arr(a: Any) -> np.ndarray:
        arr = np.asarray(a, np.float64)
        return np.stack([CX_BOX + (arr[:, 0] - lonc) * S * K, CY_BOX - (arr[:, 1] - latc) * S], 1)

    hw, hh = 520.0 / max(S * K, 1e-3), 360.0 / max(S, 1e-3)
    win = (lonc - hw, latc - hh, lonc + hw, latc + hh)

    def sect(b: Tuple[float, float, float, float]) -> bool:
        return not (b[2] < win[0] or b[0] > win[2] or b[3] < win[1] or b[1] > win[3])

    def country_path(iso_code: str) -> str:
        if not geo.has(iso_code):
            return ""
        c = geo.c[iso_code]
        parts = []
        for poly, bb in zip(c["polys"], c["bbs"]):
            if not sect(bb):
                continue
            if (bb[2] - bb[0]) * S * K < 1.5 and (bb[3] - bb[1]) * S < 1.5:
                continue
            for ring in poly:
                parts.append(_d_svg(proj_arr(ring)))
        return "".join(p for p in parts if p)

    ctx_paths: List[str] = []
    acc_ctx_len = 0
    for iso_code in geo.c:
        if iso_code in isos:
            continue
        if sect(geo.main_bbox(iso_code)):
            d_str = country_path(iso_code)
            if d_str:
                if acc_ctx_len + len(d_str) > 18000 and ctx_paths:
                    break
                ctx_paths.append(d_str)
                acc_ctx_len += len(d_str)

    countries_out: List[Dict[str, Any]] = []
    for iso_code in isos:
        d_str = country_path(iso_code)
        bb = geo.main_bbox(iso_code)
        cx, cy = proj_xy((bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0)
        c_name_ar = next((m["country_ar"] for m in mentions if m["iso3"] == iso_code and m["country_ar"]), iso_code)
        countries_out.append({
            "iso3": iso_code,
            "name_ar": c_name_ar,
            "d": d_str,
            "cx": cx,
            "cy": cy,
        })

    # Compute frame timing for each waypoint synced to the voiceover
    single_country_scene = len(isos) <= 1
    waypoints: List[Dict[str, Any]] = []
    for idx_m, m in enumerate(mentions):
        iso_m = m.get("iso3") or ""
        # When a country is mentioned alongside its capital/city in the same scene,
        # keep the pin locked on the capital/city's exact location rather than jumping to the country centroid.
        pin_m = city_by_iso3.get(iso_m, m) if m.get("kind") == "country" else m
        px, py = proj_xy(float(pin_m["lon"]), float(pin_m["lat"]))

        trig_frame = max(0, int(round(m["start_sec"] * FPS)) - 4)
        if idx_m == 0 and trig_frame <= 14:
            trig_frame = 0

        # Vary zoom when previous scene covered the same country to avoid identical consecutive maps
        prev_same_country = (
            isinstance(prev_overlay, dict)
            and prev_overlay.get("waypoints")
            and str(prev_overlay["waypoints"][-1].get("iso3") or "") == str(iso_m or "")
        )
        zoom_variety = 0.18 if prev_same_country else 0.0

        if m.get("is_microstate"):
            target_zoom = 2.15 + zoom_variety
        elif single_country_scene:
            if len(distinct_cities) >= 2:
                target_zoom = 1.22 + zoom_variety if m["kind"] in ("capital", "city") else 1.08 + zoom_variety
            else:
                target_zoom = 1.12 + zoom_variety if m["kind"] in ("capital", "city") else 1.06 + zoom_variety
        else:
            target_zoom = 1.65 + zoom_variety if m["kind"] in ("capital", "city") else 1.38 + zoom_variety
            if S < 5.0:
                scale_boost = min(1.55, max(1.0, 4.5 / max(S, 1.8)))
                target_zoom = round(min(2.4, target_zoom * scale_boost), 2)

        waypoints.append({
            "id": f"wp_{scene_idx}_{idx_m}",
            "kind": m["kind"],
            "kind_label": m["kind_label"],
            "name_ar": m["name_ar"],
            "name_en": m["name_en"],
            "country_ar": m["country_ar"],
            "iso3": m["iso3"],
            "iso2": m["iso2"],
            "lat": float(pin_m["lat"]),
            "lon": float(pin_m["lon"]),
            "coords": pin_m["coords"],
            "x": px,
            "y": py,
            "trigger_frame": trig_frame,
            "zoom": target_zoom,
        })

    for i in range(len(waypoints)):
        if i + 1 < len(waypoints):
            waypoints[i]["end_frame"] = max(waypoints[i]["trigger_frame"] + 18, waypoints[i + 1]["trigger_frame"])
        else:
            waypoints[i]["end_frame"] = dur_frames

    enter_frame = max(0, waypoints[0]["trigger_frame"] - 6)
    exit_frame = dur_frames

    # Project previous scene's last waypoint if available for cross-scene continuity
    prev_projected = None
    if prev_wp is not None:
        ppx, ppy = proj_xy(float(prev_wp["lon"]), float(prev_wp["lat"]))
        if 10.0 <= ppx <= W_BOX - 10.0 and 10.0 <= ppy <= H_BOX - 10.0:
            prev_projected = {
                "name_ar": prev_wp.get("name_ar", ""),
                "x": ppx,
                "y": ppy,
            }

    # Place only in top-left or top-right HUD corners so lower/center counters and captions are never obstructed
    placements = ["top-left", "top-right"]
    placement = placements[scene_idx % len(placements)]

    sc_vi = sc.get("_vi") if isinstance(sc.get("_vi"), dict) else {}
    is_hist_map = bool(sc_vi.get("is_historical"))
    primary_kind = waypoints[0]["kind"] if waypoints else "country"
    zoom_hierarchy = (
        ["world", "continent", "country", "city"]
        if primary_kind in ("city", "capital", "landmark")
        else (["world", "continent", "country"] if primary_kind == "country" else ["world", "continent"])
    )

    return {
        "enabled": True,
        "placement": placement,
        "enter_frame": enter_frame,
        "exit_frame": exit_frame,
        "viewport": {"w": int(W_BOX), "h": int(H_BOX)},
        "ctx_path": "".join(ctx_paths),
        "countries": countries_out,
        "waypoints": waypoints,
        "prev_waypoint": prev_projected,
        "zoom_hierarchy": zoom_hierarchy,
        "map_style": "historical" if is_hist_map else "modern",
    }

