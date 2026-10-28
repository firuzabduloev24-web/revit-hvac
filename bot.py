#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
🏛 REVIT SANTEXNIKA & HVAC MUHANDISLIK MARKAZI — MEGA TELEGRAM BOT 🏛
=============================================================================
Bosh Administrator & Muallif: @usman_khasan (Telegram ID: 1021089367)
Bot Token: 8874741365:AAH0js92yHTOE3jEWY-Mbzc6VB9523zStLE
Me'yoriy bazalar: KMK 2.04.01-98, KMK 2.04.05-97, QMQ 2.01.04-97, EN 1264, VDI 2089 & Valtec

Asosiy imkoniyatlar:
1. 📱 Telegram ichida 10-bo'limli interaktiv Web App (Mini App) kalkulyatori.
2. 🚰 Suv ta'minoti va nasos stansiyasi (/water).
3. 🚽 Kanalizatsiya K1 va Tom vodostoki K2 (/sewage).
4. 🏠 Xonaning to'liq Teplopoteryasi QMQ 2.01.04-97 (/teplo).
5. ♨️ Radiatorlar haqiqiy quvvati va seksiya podbori (/radiator).
6. 🌀 Tyopliy Pol gidravlikasi va Grundfos/Wilo nasos podbori (/floor).
7. 🔥 Kotelnaya, Senyashin 3D Gidrostrelkasi va BKN (/boiler).
8. 💨 Ventilyatsiya va havo sarfi KMK 2.04.05-97 (/vent).
9. ❄️ Toshkent yozgi (+42°C) Konditsionerlash BTU (/ac).
10. 🏊 Basseyn filtratsiyasi va VDI 2089 Osushitel (/pool).
11. 📊 Bosh Administrator Paneli: To'liq SQLite statistika (/admin, /stat).
12. 📢 Barcha foydalanuvchilarga xabar tarqatish (/broadcast).
=============================================================================
"""

import os
import sys
import time
import math
import html
import sqlite3
import logging
from datetime import datetime

try:
    import telebot
    from telebot import types
except ImportError:
    print("❌ XATOLIK: pyTelegramBotAPI o'rnatilmagan!")
    print("Terminalda quyidagi buyruqni bering:")
    print("pip install pyTelegramBotAPI")
    sys.exit(1)

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("RevitHVACBot")

# ==================== ASOSIY SOZLAMALAR ====================
DEFAULT_BOT_TOKEN = "8874741365:AAH0js92yHTOE3jEWY-Mbzc6VB9523zStLE"
BOT_TOKEN = os.environ.get("BOT_TOKEN", DEFAULT_BOT_TOKEN).strip()

DEFAULT_ADMIN_ID = 1021089367
ADMIN_USERNAME = "@usman_khasan"
try:
    ADMIN_ID = int(os.environ.get("ADMIN_ID", DEFAULT_ADMIN_ID))
except ValueError:
    ADMIN_ID = DEFAULT_ADMIN_ID

# Interaktiv 10-tabli Web App (revit_hvac_calc.html) joylashgan manzil:
DEFAULT_WEBAPP_URL = "https://firuzabduloev24-web.github.io/universal-bot-private/"
WEBAPP_URL = os.environ.get("WEBAPP_URL", DEFAULT_WEBAPP_URL).strip()

DB_FILE = os.environ.get("DB_FILE", "hvac_bot.db")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


# ==================== MA'LUMOTLAR BAZASI (SQLite) ====================
def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    # Foydalanuvchilar jadvali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            calc_count INTEGER DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Hisoblashlar log jurnali
    cur.execute("""
        CREATE TABLE IF NOT EXISTS calc_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            calc_type TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def register_user(user: types.User):
    """Foydalanuvchini ro'yxatga olish yoki faolligini yangilash."""
    try:
        conn = get_db()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        u_name = user.username or ""
        f_name = user.full_name or user.first_name or "Foydalanuvchi"
        cur.execute("""
            INSERT INTO users (user_id, username, full_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                last_seen = excluded.last_seen
        """, (user.id, u_name, f_name, now, now))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"register_user xatosi: {e}")

def log_calculation(user_id: int, calc_type: str, details: str = ""):
    """Qilingan muhandislik hisobini bazaga yozib qo'yish."""
    try:
        conn = get_db()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO calc_history (user_id, calc_type, details, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, calc_type, details, now))
        cur.execute("""
            UPDATE users SET calc_count = calc_count + 1, last_seen = ? WHERE user_id = ?
        """, (now, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"log_calculation xatosi: {e}")

def get_admin_stats() -> dict:
    """Administrator uchun umumiy statistikani chiqarish."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM users")
    total_users = cur.fetchone()[0]

    today_str = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT count(*) FROM users WHERE last_seen LIKE ?", (f"{today_str}%",))
    active_today = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM calc_history")
    total_calcs = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM calc_history WHERE created_at LIKE ?", (f"{today_str}%",))
    calcs_today = cur.fetchone()[0]

    # Eng ko'p ishlatilgan bo'limlar
    cur.execute("""
        SELECT calc_type, count(*) as cnt 
        FROM calc_history 
        GROUP BY calc_type 
        ORDER BY cnt DESC LIMIT 5
    """)
    top_calcs = cur.fetchall()

    # Oxirgi faol foydalanuvchilar
    cur.execute("""
        SELECT user_id, username, full_name, calc_count, last_seen 
        FROM users 
        ORDER BY last_seen DESC LIMIT 5
    """)
    recent_users = cur.fetchall()
    conn.close()

    return {
        "total_users": total_users,
        "active_today": active_today,
        "total_calcs": total_calcs,
        "calcs_today": calcs_today,
        "top_calcs": top_calcs,
        "recent_users": recent_users
    }


# ==================== MUHANDISLIK HISOBLASH FUNKSIYALARI ====================
def calc_water_supply(flow_lps: float, velocity: float = 1.2) -> str:
    if flow_lps <= 0:
        return "⚠️ Suv sarfi 0 dan katta bo'lishi kerak."
    q_m3s = flow_lps / 1000.0
    area = q_m3s / velocity
    exact_dia_mm = math.sqrt((4.0 * area) / math.pi) * 1000.0

    ppr_sizes = [
        ("20 × 3.4 mm", 13.2, 15, "16 × 2.2 mm"),
        ("25 × 4.2 mm", 16.6, 20, "20 × 2.8 mm"),
        ("32 × 5.4 mm", 21.2, 25, "25 × 3.5 mm"),
        ("40 × 6.7 mm", 26.6, 32, "32 × 4.4 mm"),
        ("50 × 8.3 mm", 33.4, 40, "40 × 5.5 mm"),
        ("63 × 10.5 mm", 42.0, 50, "50 × 6.9 mm"),
        ("75 × 12.5 mm", 50.0, 65, "63 × 8.6 mm"),
        ("90 × 15.0 mm", 60.0, 80, "75 mm"),
        ("110 × 18.3 mm", 73.4, 100, "90 mm")
    ]
    chosen = ppr_sizes[-1]
    for p in ppr_sizes:
        if p[1] >= exact_dia_mm * 0.94:
            chosen = p
            break

    act_area = (math.pi * math.pow(chosen[1] / 1000.0, 2)) / 4.0
    act_v = q_m3s / act_area
    flow_m3h = flow_lps * 3.6
    tank_vol = 50 if flow_m3h <= 2.5 else (80 if flow_m3h <= 4.0 else 100)

    return (
        f"🚰 <b>SUV TA'MINOTI VA QUVUR HISOBI (KMK 2.04.01-98):</b>\n\n"
        f"💧 <b>Hisobiy suv sarfi (Q):</b> <b>{flow_lps:.2f} l/s</b> ({flow_m3h:.2f} m³/h)\n"
        f"🎯 <b>Nazariy ichki diametr:</b> {exact_dia_mm:.1f} mm\n\n"
        f"📌 <b>Revit Quvur O'lchamlari:</b>\n"
        f"• <b>Pilsa PPR PN20:</b> <b>{chosen[0]}</b> (ichki d = {chosen[1]} mm)\n"
        f"• <b>Rehau RAUTITAN PE-Xa:</b> <b>{chosen[3]}</b>\n"
        f"• <b>Po'lat ВГП ГОСТ 3262-75:</b> <b>DN {chosen[2]}</b>\n"
        f"• <b>Haqiqiy tezlik:</b> <b>{act_v:.2f} m/s</b> (Norma: 0.7–1.5 m/s ✅)\n\n"
        f"⚡ <b>Bosim Oshirish Stansiyasi (Podkachka):</b>\n"
        f"• <b>Nasos:</b> Grundfos SCALA2 3-45 yoki Wilo HiMulti 3\n"
        f"• <b>Gidroakkumulyator:</b> <b>{tank_vol} Litr</b> (10 bar)"
    )

def calc_sewage_and_roof(roof_area_m2: float = 220.0) -> str:
    q_liv_lps = (roof_area_m2 * 65.0 * 1.0) / 10000.0
    funnels = max(2, math.ceil(q_liv_lps / 10.0))
    risers = max(1, math.ceil(roof_area_m2 / 200.0))
    return (
        f"🚽 <b>KANALIZATSIYA (K1) VA TOM VODOSTOKI (K2):</b>\n\n"
        f"<b>1. Maishiy Kanalizatsiya (K1 - KMK 2.04.01-98):</b>\n"
        f"• <b>DN 50 tarmoq (Dush, Umyvalnik, Moyka):</b> Uklon <b>i = 0.03 (3 sm/m)</b>\n"
        f"• <b>DN 110 magistral (Unitaz va stoyak):</b> Uklon <b>i = 0.02 (2 sm/m)</b>\n"
        f"• <b>Fanovaya truba:</b> DN 110 tom ustiga +0.5 m chiqariladi.\n\n"
        f"<b>2. Tom Yomg'ir Suvi Vodostoki (K2 - Maydon {roof_area_m2:.0f} m²):</b>\n"
        f"• <b>Toshkent yomg'ir sarfi (q₂₀ = 65):</b> <b>{q_liv_lps:.2f} l/s</b> ({(q_liv_lps*3.6):.2f} m³/h)\n"
        f"• <b>Zarur tom voronkalari:</b> <b>{funnels} ta voronka</b> (HL DN 110)\n"
        f"• <b>Vodostok stoyaklari:</b> <b>{risers} ta stoyak DN 110</b>"
    )

def calc_room_heat_loss(l: float, w: float, h: float, tin: float = 22.0, tout: float = -15.0) -> str:
    area = l * w
    vol = area * h
    dt = tin - tout
    win_area = min(3.6, area * 0.18)
    wall_gross = (l + w) * h
    wall_net = max(wall_gross - win_area, 0.0)

    q_wall = (wall_net * dt / 1.85) * 1.05
    q_win = (win_area * dt / 0.52) * 1.05
    q_floor = (area * max(tin - 5.0, 8.0)) / 2.5
    q_vent = 0.336 * vol * dt
    q_total = q_wall + q_win + q_floor + q_vent
    q_spec = q_total / area
    rad_sec = math.ceil(q_total / 160.0)

    return (
        f"🏠 <b>XONA TEPLOPOTERYASI (QMQ 2.01.04-97):</b>\n\n"
        f"📐 <b>O'lchamlar:</b> {l:.1f} × {w:.1f} × {h:.1f} m (Maydon S = <b>{area:.1f} m²</b>, V = {vol:.1f} m³)\n"
        f"🌡 <b>Harorat:</b> Ichki +{tin:.0f}°C / Tashqi {tout:.0f}°C (ΔT = {dt:.0f}°C)\n\n"
        f"🔥 <b>Jami issiqlik yo'qotishi:</b> <b>{round(q_total)} Vt</b> ({(q_total/1000):.2f} kW)\n"
        f"📊 <b>Solishtirma quvvat:</b> <b>{q_spec:.1f} W/m²</b>\n\n"
        f"• Devorlar orqali: {round(q_wall)} Vt\n"
        f"• Oynalar orqali: {round(q_win)} Vt\n"
        f"• Pol orqali: {round(q_floor)} Vt\n"
        f"• Shamollatish (Infiltratsiya): {round(q_vent)} Vt\n\n"
        f"✅ <b>Tavsiya:</b> <b>{rad_sec} ta seksiya</b> bimetall radiator yoki <b>~{round(area*6.7)} m</b> tyopliy pol trubasi (qadam 15 sm)."
    )

def calc_radiator_selection(q_demand: float, t_sup: float = 75.0, t_ret: float = 60.0, t_room: float = 20.0) -> str:
    dt = ((t_sup + t_ret) / 2.0) - t_room
    q_rifar = 204.0 * math.pow(dt / 70.0, 1.28)
    q_tubog = 370.0 * math.pow(dt / 70.0, 1.28)
    q_chugun = 160.0 * math.pow(dt / 70.0, 1.30)

    return (
        f"♨️ <b>RADIATOR QUVVATI (VAT) VA SEKSIYA PODBORI:</b>\n\n"
        f"🌡 <b>Harorat rejimi:</b> Podacha {t_sup:.0f}°C / Obratka {t_ret:.0f}°C / Xona {t_room:.0f}°C (ΔT = {dt:.1f}°C)\n"
        f"🎯 <b>Talab qilinadigan quvvat:</b> <b>{round(q_demand)} Vt</b>\n\n"
        f"1️⃣ <b>Rifar Base / Monolit 500 (Bimetall):</b>\n"
        f"   • 1 seksiya real quvvati: <b>{q_rifar:.1f} Vt</b> → Zarur: <b>{math.ceil(q_demand/q_rifar)} ta seksiya</b>\n\n"
        f"2️⃣ <b>Royal Thermo Tubog 2180 (Vertikal H=1800mm):</b>\n"
        f"   • 1 seksiya real quvvati: <b>{q_tubog:.1f} Vt</b> → Zarur: <b>{math.ceil(q_demand/q_tubog)} ta seksiya</b>\n\n"
        f"3️⃣ <b>Klassik Cho'yan MS-140-500:</b>\n"
        f"   • 1 seksiya real quvvati: <b>{q_chugun:.1f} Vt</b> → Zarur: <b>{math.ceil(q_demand/q_chugun)} ta seksiya</b>\n\n"
        f"🔧 <b>Revit ulanish:</b> DN 15 (½\") yoki DN 20 (¾\") diagonal sxemada."
    )

def calc_floor_heating(area_m2: float, covering: str = "kafel") -> str:
    q_flux = 90.0 if covering == "kafel" else 70.0
    power_kw = (area_m2 * q_flux) / 1000.0
    flow_m3h = (0.86 * power_kw) / 8.0
    flow_lpm = (flow_m3h * 1000.0) / 60.0
    pipe_len = round(area_m2 * 6.7 + 20)
    loops = max(2, math.ceil(pipe_len / 70.0))
    loop_len = round(pipe_len / loops)
    loop_flow = flow_lpm / loops

    pump = "Grundfos UPS 25-40 180 / ALPHA1 L 25-40" if area_m2 <= 120 else "Grundfos UPS 25-60 180 / Wilo Yonos PICO 25/1-6"
    kvs = "Kvs = 2.5 m³/h (DN 20)" if area_m2 <= 120 else "Kvs = 4.0 m³/h (DN 25)"

    return (
        f"🌀 <b>TYOPLIY POL VA NASOS PODBORI (EN 1264 / VALTEC):</b>\n\n"
        f"📐 <b>Maydon:</b> <b>{area_m2:.1f} m²</b> ({covering.capitalize()})\n"
        f"🔥 <b>Issiqlik quvvati:</b> <b>{power_kw:.2f} kW</b> ({q_flux:.0f} W/m²)\n"
        f"💧 <b>Sirkulyatsiya sarfi:</b> <b>{flow_m3h:.2f} m³/h</b> ({flow_lpm:.1f} l/min)\n\n"
        f"📌 <b>Kollektor va Quvurlar:</b>\n"
        f"• <b>Quvur (16×2.0 mm PE-RT / PE-Xa):</b> Jami <b>~{pipe_len} metr</b> (qadam 15 sm)\n"
        f"• <b>Konturlar soni (Loops):</b> <b>{loops} ta kontur</b> (har biri ~{loop_len} m)\n"
        f"• <b>Rotametr balansirovka oqimi:</b> <b>{loop_flow:.2f} l/min</b>\n\n"
        f"⚡ <b>Tavsiya Nasos va Smesitel Uzeli:</b>\n"
        f"• <b>Sirkulyatsiya nasosi:</b> <b>{pump}</b>\n"
        f"• <b>3 yo'lli klapan:</b> <b>{kvs}</b> (Valtec Dualmix / Combimix)"
    )

def calc_boiler_3d(power_kw: float, dt: float = 20.0) -> str:
    flow_m3h = (0.86 * power_kw) / dt
    q_m3s = flow_m3h / 3600.0
    pipe_d_mm = math.sqrt((4.0 * (q_m3s / 0.85)) / math.pi) * 1000.0
    pipe_dn = 25 if pipe_d_mm <= 25 else (32 if pipe_d_mm <= 35 else 40)

    body_d_mm = max(math.sqrt((4.0 * (q_m3s / 0.08)) / math.pi) * 1000.0, pipe_d_mm * 3.0)
    body_dn = 80 if body_d_mm <= 85 else (100 if body_d_mm <= 110 else 125)
    body_h = body_dn * 6

    exp_tank = 35 if power_kw <= 40 else (50 if power_kw <= 65 else 80)
    gas_m3h = (power_kw / (9.3 * 0.91)) + 1.1
    gas_meter = "Gazomer G4" if gas_m3h <= 5.5 else ("Gazomer G6" if gas_m3h <= 9.5 else "Gazomer G10")

    return (
        f"🔥 <b>KOTELNAYA, 3D GIDROSTRELKA VA BKN HISOBI:</b>\n\n"
        f"⚡ <b>Qozon quvvati:</b> <b>{power_kw:.0f} kW</b> (ΔT = {dt:.0f}°C)\n"
        f"💧 <b>Kotel suv sarfi:</b> <b>{flow_m3h:.2f} m³/h</b> ({(flow_m3h/3.6):.2f} l/s)\n\n"
        f"📐 <b>Gidrostrelka (Senyashin 3D Qoidasi):</b>\n"
        f"• <b>Patrubkalar diametri (d):</b> <b>DN {pipe_dn}</b> (d ≈ {pipe_d_mm:.0f} mm)\n"
        f"• <b>Korpus diametri (D = 3×d):</b> <b>DN {body_dn}</b>\n"
        f"• <b>Gidrostrelka balandligi (H):</b> <b>~{body_h} mm</b> (w ≤ 0.08 m/s ✅)\n\n"
        f"🎈 <b>Kengayish baki:</b> <b>{exp_tank} Litr</b> (3.0 bar klapan)\n"
        f"♨️ <b>Boyler (BKN):</b> 200 Litr ({round(power_kw*0.6)} kW zmeyevik)\n"
        f"🔥 <b>Tabiiy gaz sarfi:</b> <b>~{gas_m3h:.1f} m³/h</b> → <b>{gas_meter}</b>"
    )

def calc_vent_and_ac(area_m2: float, h: float = 3.0, people: int = 4) -> str:
    vol = area_m2 * h
    q_cool_kw = ((vol * 40.0) / 1000.0) + (people * 0.12) + 0.4
    btu = q_cool_kw * 3412.142

    model = "Split Model 12 (12,000 BTU / 3.5 kW)"
    freon = '1/4" (6.35 mm) + 1/2" (12.7 mm)'
    if btu > 14000 and btu <= 21000:
        model = "Split Model 18 (18,000 BTU / 5.3 kW)"
    elif btu > 21000:
        model = "Split Model 24 (24,000 BTU / 7.0 kW)"
        freon = '3/8" (9.52 mm) + 5/8" (15.88 mm)'

    vent_m3h = max(people * 30.0, vol * 1.0)
    return (
        f"❄️ <b>VENTILYATSIYA VA KONDITSIONER (TOSHKENT YOZI +42°C):</b>\n\n"
        f"📐 <b>Xona:</b> {area_m2:.1f} m² × {h:.1f} m (V = {vol:.1f} m³, {people} kishi)\n\n"
        f"❄️ <b>Konditsionerlash (BTU):</b>\n"
        f"• <b>Sovutish quvvati:</b> <b>{q_cool_kw:.2f} kW</b> (<b>{round(btu):,} BTU/h</b>)\n"
        f"• <b>Tavsiya model:</b> <b>{model}</b>\n"
        f"• <b>Freon mis trubalari:</b> <b>{freon}</b>\n"
        f"• <b>Drenaj:</b> DN 16 mm PVX\n\n"
        f"💨 <b>Ventilyatsiya (KMK 2.04.05-97):</b>\n"
        f"• <b>Zarur havo almashinuvi (L):</b> <b>{round(vent_m3h)} m³/h</b>\n"
        f"• <b>Kanal o'lchami:</b> 140×140 mm g'isht shaxta yoki Ø 125 mm spiro-quvur"
    )

def calc_pool_system(l: float = 7.0, w: float = 3.5, d: float = 1.5) -> str:
    area = l * w
    vol = area * d
    pump_m3h = vol / 4.0
    filter_dia = 500 if pump_m3h <= 10.5 else (650 if pump_m3h <= 16.5 else 800)
    heater_kw = round(((vol * 16.0 * 1.163) / 24.0) + (area * 0.18))
    evap_lph = area * 0.22
    evap_day = evap_lph * 24.0

    return (
        f"🏊 <b>BASSEYN FILTRATSIYASI, ISITISH VA OSUSHITEL (VDI 2089):</b>\n\n"
        f"📐 <b>Basseyn:</b> {l:.1f} × {w:.1f} × {d:.1f} m (Hajm V = <b>{vol:.1f} m³</b>, Yuza S = {area:.1f} m²)\n\n"
        f"💧 <b>Filtratsiya (Turnover 4 soat):</b>\n"
        f"• <b>Nasos unumdorligi:</b> <b>{pump_m3h:.1f} m³/h</b> (Emaux / Kripsol)\n"
        f"• <b>Qumli filtr bochkasi:</b> <b>Ø {filter_dia} mm</b>\n"
        f"• <b>Suvni isitish (Teploobmennik):</b> <b>{heater_kw} kW</b> (Pahlen / Bowman)\n\n"
        f"💨 <b>Basseyn Zali Namlik Quritgichi (Osushitel):</b>\n"
        f"• <b>Suv bug'lanishi (W):</b> <b>{evap_lph:.2f} l/soat</b> (~{evap_day:.0f} litr/sutka)\n"
        f"• <b>Tavsiya Osushitel:</b> <b>Dantherm CDP 50 / Calorex DH 75</b>"
    )


# ==================== TUGMALAR VA MENYULAR ====================
def get_hvac_main_keyboard(is_admin: bool = False) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup(row_width=2)
    # Web App tugmasi
    markup.add(
        types.InlineKeyboardButton(
            text="📱 10-Bo'limli Interaktiv Web Kalkulyatorni Ochish",
            web_app=types.WebAppInfo(url=WEBAPP_URL)
        )
    )
    markup.add(
        types.InlineKeyboardButton("🚰 Suv & Nasos", callback_data="hvac:water"),
        types.InlineKeyboardButton("🚽 Kanalizatsiya K1/K2", callback_data="hvac:sewage")
    )
    markup.add(
        types.InlineKeyboardButton("🏠 Teplopoterya", callback_data="hvac:teplo"),
        types.InlineKeyboardButton("♨️ Radiator (Vat)", callback_data="hvac:radiator")
    )
    markup.add(
        types.InlineKeyboardButton("🌀 Tyopliy Pol & Nasos", callback_data="hvac:floor"),
        types.InlineKeyboardButton("🔥 Kotelnaya & 3D", callback_data="hvac:boiler")
    )
    markup.add(
        types.InlineKeyboardButton("❄️ Konditsioner & Vent", callback_data="hvac:ac"),
        types.InlineKeyboardButton("🏊 Basseyn & Osushitel", callback_data="hvac:pool")
    )
    if is_admin:
        markup.add(types.InlineKeyboardButton("👑 Bosh Admin Statistikasi (/admin)", callback_data="admin_stat_cb"))
    return markup


# ==================== TELEGRAM HANDLERS ====================
@bot.message_handler(commands=['start', 'help', 'hvac'])
def handle_start(message: types.Message):
    user = message.from_user
    register_user(user)
    is_admin = (user.id == ADMIN_ID)
    first_name = user.first_name or "Muhandis"

    admin_line = "\n👑 <b>Bosh Administrator:</b> /admin — Bot statistikasi\n" if is_admin else ""

    text = (
        f"👋 <b>Assalomu alaykum, {first_name}!</b>\n\n"
        "🏛 <b>Revit Santexnika & HVAC Muhandislik Markazi</b>ning rasmiy botiga xush kelibsiz!\n\n"
        "📐 <b>Tezkor Muhandislik Buyruqlari:</b>\n"
        "• <code>/water 0.45</code> — Suv sarfi bo'yicha PPR/Rehau/Chelik diametri (l/s)\n"
        "• <code>/sewage 220</code> — Kanalizatsiya uklonlari va tom vodostoki (m²)\n"
        "• <code>/teplo 5 4 3</code> — Xona teplopoteryasi (Uzunlik Eni Balandlik)\n"
        "• <code>/radiator 1850</code> — Radiator quvvati (Vat) va seksiya podbori\n"
        "• <code>/floor 100 kafel</code> — Tyopliy pol konturlari va Grundfos nasos podbori\n"
        "• <code>/boiler 40</code> — Kotelnaya, 3D gidrostrelka, BKN va Gazomer (kW)\n"
        "• <code>/ac 38</code> yoki <code>/vent 38</code> — Konditsioner (BTU) va ventilyatsiya\n"
        "• <code>/pool 7 3.5 1.5</code> — Basseyn filtratsiyasi, teploobmennik va osushitel\n"
        f"{admin_line}\n"
        "👇 <i>Yoki quyidagi tugmalar orqali hisoblash bo'limini tanlang:</i>"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_hvac_main_keyboard(is_admin))


# ==================== ADMIN STATISTIKASI VA BROADCAST ====================
@bot.message_handler(commands=['admin', 'stat', 'stats'])
def handle_admin_stats(message: types.Message):
    user = message.from_user
    register_user(user)
    if user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔️ Ushbu bo'lim faqat bosh administrator (@usman_khasan) uchun mo'ljallangan.")
        return

    st = get_admin_stats()
    top_lines = "\n".join([f"  • <b>{r['calc_type']}:</b> {r['cnt']} marta" for r in st["top_calcs"]]) or "  • Hali hisoblar yo'q"
    recent_lines = []
    for u in st["recent_users"]:
        u_tag = f"@{u['username']}" if u['username'] else (u['full_name'] or str(u['user_id']))
        recent_lines.append(f"  • {html.escape(u_tag)} (<code>{u['user_id']}</code>) — {u['calc_count']} ta hisob | <i>{str(u['last_seen'])[:16]}</i>")
    recent_block = "\n".join(recent_lines) or "  • Hali foydalanuvchilar yo'q"

    text = (
        f"👑 <b>BOSH ADMINISTRATOR STATISTIKASI (@usman_khasan)</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> <b>{st['total_users']:,} ta</b>\n"
        f"⚡ <b>Bugun faol bo'lganlar:</b> <b>{st['active_today']:,} ta</b>\n"
        f"🧮 <b>Jami qilingan hisob-kitoblar:</b> <b>{st['total_calcs']:,} ta</b>\n"
        f"🔥 <b>Bugungi hisoblar:</b> <b>{st['calcs_today']:,} ta</b>\n\n"
        f"📈 <b>Eng ko'p ishlatilgan bo'limlar:</b>\n{top_lines}\n\n"
        f"🕒 <b>Oxirgi kirgan foydalanuvchilar:</b>\n{recent_block}\n\n"
        f"📢 <b>Xabar tarqatish:</b> <code>/broadcast &lt;xabar matni&gt;</code>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Yangilash", callback_data="admin_stat_cb"))
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.send_message(message.chat.id, "Foydalanish: <code>/broadcast &lt;xabar matni&gt;</code>", parse_mode="HTML")
        return

    text = args[1]
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()
    conn.close()

    sent = 0
    for u in users:
        try:
            bot.send_message(u["user_id"], text, parse_mode="HTML")
            sent += 1
            time.sleep(0.04)
        except Exception:
            pass

    bot.send_message(message.chat.id, f"✅ Xabar barcha muhandislarga yetkazildi ({sent} ta foydalanuvchi).")


# ==================== BUYRUQLAR BO'YICHA HISOBLASH ====================
@bot.message_handler(commands=['water'])
def cmd_water(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    flow = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 0.38
    res = calc_water_supply(flow)
    log_calculation(message.from_user.id, "Suv & Nasos (KMK)", f"flow={flow}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['sewage'])
def cmd_sewage(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    area = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 220.0
    res = calc_sewage_and_roof(area)
    log_calculation(message.from_user.id, "Kanalizatsiya K1/K2", f"area={area}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['teplo'])
def cmd_teplo(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    l, w, h = 5.0, 4.0, 3.0
    if len(args) >= 4:
        try:
            l, w, h = float(args[1]), float(args[2]), float(args[3])
        except ValueError:
            pass
    res = calc_room_heat_loss(l, w, h)
    log_calculation(message.from_user.id, "Teplopoterya QMQ", f"{l}x{w}x{h}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['radiator'])
def cmd_radiator(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    q = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 1850.0
    res = calc_radiator_selection(q)
    log_calculation(message.from_user.id, "Radiator Vat", f"q={q}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['floor'])
def cmd_floor(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    area = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 100.0
    cov = args[2].lower() if len(args) > 2 else "kafel"
    res = calc_floor_heating(area, cov)
    log_calculation(message.from_user.id, "Tyopliy Pol & Nasos", f"area={area}, cov={cov}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['boiler'])
def cmd_boiler(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    kw = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 40.0
    res = calc_boiler_3d(kw)
    log_calculation(message.from_user.id, "Kotelnaya & 3D", f"kw={kw}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['ac', 'vent'])
def cmd_ac(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    area = float(args[1]) if len(args) > 1 and args[1].replace('.', '', 1).isdigit() else 38.0
    res = calc_vent_and_ac(area)
    log_calculation(message.from_user.id, "Konditsioner & Vent", f"area={area}")
    bot.reply_to(message, res)

@bot.message_handler(commands=['pool'])
def cmd_pool(message: types.Message):
    register_user(message.from_user)
    args = message.text.split()
    l, w, d = 7.0, 3.5, 1.5
    if len(args) >= 4:
        try:
            l, w, d = float(args[1]), float(args[2]), float(args[3])
        except ValueError:
            pass
    res = calc_pool_system(l, w, d)
    log_calculation(message.from_user.id, "Basseyn & Osushitel", f"{l}x{w}x{d}")
    bot.reply_to(message, res)


# ==================== CALLBACK QUERY (TUGMALAR) ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call: types.CallbackQuery):
    data = call.data
    user = call.from_user
    register_user(user)

    if data == "admin_stat_cb":
        if user.id != ADMIN_ID:
            bot.answer_callback_query(call.id, "Faqat bosh admin uchun!", show_alert=True)
            return
        st = get_admin_stats()
        top_lines = "\n".join([f"  • <b>{r['calc_type']}:</b> {r['cnt']} marta" for r in st["top_calcs"]]) or "  • Hali hisoblar yo'q"
        recent_lines = []
        for u in st["recent_users"]:
            u_tag = f"@{u['username']}" if u['username'] else (u['full_name'] or str(u['user_id']))
            recent_lines.append(f"  • {html.escape(u_tag)} (<code>{u['user_id']}</code>) — {u['calc_count']} ta hisob | <i>{str(u['last_seen'])[:16]}</i>")
        recent_block = "\n".join(recent_lines) or "  • Hali foydalanuvchilar yo'q"

        text = (
            f"👑 <b>BOSH ADMINISTRATOR STATISTIKASI (@usman_khasan)</b>\n\n"
            f"👥 <b>Jami foydalanuvchilar:</b> <b>{st['total_users']:,} ta</b>\n"
            f"⚡ <b>Bugun faol bo'lganlar:</b> <b>{st['active_today']:,} ta</b>\n"
            f"🧮 <b>Jami qilingan hisob-kitoblar:</b> <b>{st['total_calcs']:,} ta</b>\n"
            f"🔥 <b>Bugungi hisoblar:</b> <b>{st['calcs_today']:,} ta</b>\n\n"
            f"📈 <b>Eng ko'p ishlatilgan bo'limlar:</b>\n{top_lines}\n\n"
            f"🕒 <b>Oxirgi kirgan foydalanuvchilar:</b>\n{recent_block}\n\n"
            f"📢 <b>Xabar tarqatish:</b> <code>/broadcast &lt;xabar matni&gt;</code>"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Yangilash", callback_data="admin_stat_cb"))
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        bot.answer_callback_query(call.id, "Statistika yangilandi!")
        return

    if data.startswith("hvac:"):
        sec = data.split(":")[1]
        bot.answer_callback_query(call.id)
        if sec == "water":
            log_calculation(user.id, "Suv & Nasos (KMK)", "tugma")
            bot.send_message(call.message.chat.id, calc_water_supply(0.38) + "\n\n💡 <i>Boshqa sarf uchun:</i> <code>/water 0.65</code>")
        elif sec == "sewage":
            log_calculation(user.id, "Kanalizatsiya K1/K2", "tugma")
            bot.send_message(call.message.chat.id, calc_sewage_and_roof(220.0) + "\n\n💡 <i>Boshqa tom maydoni uchun:</i> <code>/sewage 350</code>")
        elif sec == "teplo":
            log_calculation(user.id, "Teplopoterya QMQ", "tugma")
            bot.send_message(call.message.chat.id, calc_room_heat_loss(5.0, 4.0, 3.0) + "\n\n💡 <i>Boshqa xona uchun:</i> <code>/teplo 6 4.5 3.2</code>")
        elif sec == "radiator":
            log_calculation(user.id, "Radiator Vat", "tugma")
            bot.send_message(call.message.chat.id, calc_radiator_selection(1850.0) + "\n\n💡 <i>Boshqa quvvat uchun:</i> <code>/radiator 2400</code>")
        elif sec == "floor":
            log_calculation(user.id, "Tyopliy Pol & Nasos", "tugma")
            bot.send_message(call.message.chat.id, calc_floor_heating(100.0, "kafel") + "\n\n💡 <i>Boshqa maydon uchun:</i> <code>/floor 140 tarket</code>")
        elif sec == "boiler":
            log_calculation(user.id, "Kotelnaya & 3D", "tugma")
            bot.send_message(call.message.chat.id, calc_boiler_3d(40.0) + "\n\n💡 <i>Boshqa qozon quvvati uchun:</i> <code>/boiler 65</code>")
        elif sec == "ac":
            log_calculation(user.id, "Konditsioner & Vent", "tugma")
            bot.send_message(call.message.chat.id, calc_vent_and_ac(38.0) + "\n\n💡 <i>Boshqa xona maydoni uchun:</i> <code>/ac 50</code>")
        elif sec == "pool":
            log_calculation(user.id, "Basseyn & Osushitel", "tugma")
            bot.send_message(call.message.chat.id, calc_pool_system(7.0, 3.5, 1.5) + "\n\n💡 <i>Boshqa basseyn o'lchami uchun:</i> <code>/pool 10 4 1.6</code>")


# ==================== DASTURNI ISHGA TUSHIRISH ====================
if __name__ == '__main__':
    print("=" * 70)
    print("🏛 REVIT SANTEXNIKA & HVAC MUHANDISLIK BOTI ISHGA TUSHMOQDA...")
    print(f"👑 Bosh Admin ID: {ADMIN_ID} (@usman_khasan)")
    print(f"📊 SQLite Baza: {DB_FILE} (Statistika faol)")
    print(f"🌐 Web App URL: {WEBAPP_URL}")
    print("=" * 70)

    try:
        me = bot.get_me()
        print(f"✅ Telegram API ga muvaffaqiyatli ulandi: @{me.username} ({me.first_name})")
    except Exception as e:
        print(f"⚠️ Telegramga ulanish ogohlantirishi: {e}")

    # Polling orqali botni 24/7 uzluksiz yurgizish (Auto-reconnect bilan)
    print("🤖 Bot 24/7 uzluksiz polling rejimida ishga tushdi...")
    while True:
        try:
            bot.infinity_polling(timeout=35, long_polling_timeout=20, skip_pending=True)
        except (KeyboardInterrupt, SystemExit):
            print("\n🛑 Bot to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Polling xatosi (5 soniyada qayta ulanadi): {e}")
            time.sleep(5)
