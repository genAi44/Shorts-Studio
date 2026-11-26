"""
pipeline/geo_overlay.py
نظام ذكي لاكتشاف المواقع الجغرافية (الدول، المدن، العواصم) تلقائياً من النص والتعليق الصوتي،
وربطها بالتوقيت الزمني للكلمات المنطوقة، وتوليد طبقة خريطة تفاعلية سينمائية (MapOverlay) لـ Remotion.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

import json

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
# Arabic common words that are also country names: accepted as a country only right after one of these tokens.
_AMBIGUOUS_COUNTRY_WORDS = {"مالي"}
_COUNTRY_CONTEXT_PREV = ("دولة", "جمهورية", "في", "إلى", "الى", "من", "نحو", "عاصمة", "شمال", "جنوب", "وسط")

_CURATED_CITIES_AR: Dict[str, Dict[str, Any]] = {
    "مدينة الكويت": {"name_ar": "مدينة الكويت", "name_en": "Kuwait City", "country_ar": "الكويت", "iso3": "KWT", "iso2": "kw", "lat": 29.3759, "lon": 47.9774, "is_capital": True},
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
    "العواصم العربية": {"name_ar": "العالم العربي", "name_en": "Arab World", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN","EGY","JOR","IRQ","SYR","LBN","MAR","DZA","TUN","LBY","SDN","YEM"], "lat": 27.0, "lon": 35.0},
    "الدول العربية": {"name_ar": "العالم العربي", "name_en": "Arab World", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN","EGY","JOR","IRQ","SYR","LBN","MAR","DZA","TUN","LBY","SDN","YEM"], "lat": 27.0, "lon": 35.0},
    "العالم العربي": {"name_ar": "العالم العربي", "name_en": "Arab World", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN","EGY","JOR","IRQ","SYR","LBN","MAR","DZA","TUN","LBY","SDN","YEM"], "lat": 27.0, "lon": 35.0},
    "الوطن العربي": {"name_ar": "العالم العربي", "name_en": "Arab World", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN","EGY","JOR","IRQ","SYR","LBN","MAR","DZA","TUN","LBY","SDN","YEM"], "lat": 27.0, "lon": 35.0},
    "العواصم الخليجية": {"name_ar": "دول الخليج", "name_en": "Gulf States", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN"], "lat": 25.5, "lon": 50.0},
    "الدول الخليجية": {"name_ar": "دول الخليج", "name_en": "Gulf States", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN"], "lat": 25.5, "lon": 50.0},
    "دول الخليج": {"name_ar": "دول الخليج", "name_en": "Gulf States", "iso3": "SAU", "is_region": True, "continent_isos": ["SAU","ARE","QAT","KWT","BHR","OMN"], "lat": 25.5, "lon": 50.0},
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

# Re-exported so `pipeline.geo_overlay.<name>` keeps working.
from .geo_overlay_mentions import (  # noqa: E402,F401
    _COMMON_NOUN_CITY_STOPWORDS,
    _d_svg,
    _find_word_timestamp,
    _format_gps,
    _norm_token,
    extract_timed_geo_mentions,
)

# Re-exported so `pipeline.geo_overlay.<name>` keeps working.
from .geo_overlay_build import (  # noqa: E402,F401
    MAP_FILL,
    _SCALE_LABEL,
    _TERRAIN_LABEL,
    _fills_width,
    _fit_zoom,
    _geojson_extent,
    build_scene_map_overlay,
    mention_from_entity,
)
