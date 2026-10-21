import streamlit as st
import pandas as pd
from datetime import datetime
import math
import io
import os

# 1. Page Configuration
st.set_page_config(page_title="Sales Manager Live Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")

DATA_FILE = "saved_vendor_data.pkl"

# Custom CSS for Dark Theme Executive Dashboard Styling
st.markdown("""
    <style>
    .main {
        background-color: #0b132b;
    }
    .metric-card {
        background-color: #1c2541;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #3a506b;
        margin-bottom: 15px;
        color: white;
    }
    .metric-title {
        font-size: 14px;
        color: #8d99ae;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-value {
        font-size: 32px;
        color: #ffffff;
        font-weight: bold;
        margin-top: 5px;
    }
    .metric-sub {
        font-size: 12px;
        color: #e63946;
        margin-top: 5px;
    }
    .metric-sub-green {
        font-size: 12px;
        color: #2ec4b6;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to render Proper Speedometer
def render_speedometer_html(client_name, rate, ontime, delay, total):
    clamped_rate = max(0.0, min(100.0, float(rate)))
    
    if clamped_rate >= 80:
        val_color = "#2ec4b6"  # Green
    elif clamped_rate >= 50:
        val_color = "#ffb703"  # Yellow
    else:
        val_color = "#e63946"  # Red

    cx, cy = 120, 110
    
    ticks_svg = ""
    for p in range(0, 101, 10):
        rad = math.radians(180 - (p * 1.8))
        r_inner = 62 if p % 20 == 0 else 65
        r_outer = 70
        x1 = cx + r_inner * math.cos(rad)
        y1 = cy - r_inner * math.sin(rad)
        x2 = cx + r_outer * math.cos(rad)
        y2 = cy - r_outer * math.sin(rad)
        stroke_w = "2" if p % 20 == 0 else "1"
        ticks_svg += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#8d99ae" stroke-width="{stroke_w}"/>'

    labels_svg = ""
    for p in [0, 25, 50, 75, 100]:
        rad = math.radians(180 - (p * 1.8))
        r_lbl = 98
        lx = cx + r_lbl * math.cos(rad)
        ly = cy - r_lbl * math.sin(rad) + 4
        labels_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#8d99ae" font-size="10" font-weight="bold" text-anchor="middle" font-family="Arial">{p}%</text>'

    n_rad = math.radians(180 - (clamped_rate * 1.8))
    tip_x = cx + 65 * math.cos(n_rad)
    tip_y = cy - 65 * math.sin(n_rad)
    
    perp_rad = n_rad + (math.pi / 2)
    b1_x = cx + 4.5 * math.cos(perp_rad)
    b1_y = cy - 4.5 * math.sin(perp_rad)
    b2_x = cx - 4.5 * math.cos(perp_rad)
    b2_y = cy + 4.5 * math.sin(perp_rad)
    tail_x = cx - 12 * math.cos(n_rad)
    tail_y = cy + 12 * math.sin(n_rad)

    needle_points = f"{b1_x:.1f},{b1_y:.1f} {tip_x:.1f},{tip_y:.1f} {b2_x:.1f},{b2_y:.1f} {tail_x:.1f},{tail_y:.1f}"

    html_lines = [
        f'<div class="metric-card" style="text-align: center; padding: 18px 15px;">',
        f'<div class="metric-title" style="margin-bottom: 8px;">{client_name} Performance</div>',
        f'<svg viewBox="0 0 240 130" width="100%" style="max-width: 260px; margin: 0 auto; display: block;">',
        f'<path d="M 40 110 A 80 80 0 0 1 200 110" fill="none" stroke="#0b132b" stroke-width="18" stroke-linecap="round"/>',
        f'<path d="M 40 110 A 80 80 0 0 1 120 30" fill="none" stroke="#e63946" stroke-width="14" stroke-linecap="butt"/>',
        f'<path d="M 120 30 A 80 80 0 0 1 184.72 62.98" fill="none" stroke="#ffb703" stroke-width="14" stroke-linecap="butt"/>',
        f'<path d="M 184.72 62.98 A 80 80 0 0 1 200 110" fill="none" stroke="#2ec4b6" stroke-width="14" stroke-linecap="butt"/>',
        ticks_svg,
        labels_svg,
        f'<polygon points="{needle_points}" fill="#ffffff"/>',
        f'<circle cx="{cx}" cy="{cy}" r="8" fill="#ffffff"/>',
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="#1c2541"/>',
        f'</svg>',
        f'<div style="font-size: 32px; font-weight: bold; color: {val_color}; margin-top: 2px;">{rate}%</div>',
        f'<div style="font-size: 13px; color: #8d99ae; margin-top: 6px;">',
        f'<span style="color:#2ec4b6;">On-Time: <b>{ontime}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#e63946;">Delay: <b>{delay}</b></span> &nbsp;|&nbsp; ',
        f'<span style="color:#ffffff;">Total: <b>{total}</b></span>',
        f'</div>',
        f'</div>'
    ]
    return "".join(html_lines)

# Helper
