import streamlit as st
import cv2
import yt_dlp
import numpy as np
import os
import tempfile
import shutil
import time
import base64
import zipfile
from PIL import Image

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="LectureNotes Pro", page_icon="⚡", layout="wide")

# --- SESSION STATE INITIALIZATION (CRITICAL: MUST BE AT TOP) ---
if 'setup_active' not in st.session_state:
    st.session_state['setup_active'] = False
if 'setup_step' not in st.session_state:
    st.session_state['setup_step'] = 1
if 'video_info' not in st.session_state:
    st.session_state['video_info'] = None
if 'url_input' not in st.session_state:
    st.session_state['url_input'] = ""
if 'cookies_path' not in st.session_state:
    st.session_state['cookies_path'] = None
if 'scan_complete' not in st.session_state:
    st.session_state['scan_complete'] = False
if 'scan_temp_dir' not in st.session_state:
    st.session_state['scan_temp_dir'] = tempfile.mkdtemp()

# Config State Initialization (For persistence across wizard/workspace)
if 'sensitivity' not in st.session_state: st.session_state['sensitivity'] = 35
if 'strictness' not in st.session_state: st.session_state['strictness'] = 1.0
if 'min_skip' not in st.session_state: st.session_state['min_skip'] = 2
if 'max_skip' not in st.session_state: st.session_state['max_skip'] = 10

# Ensure step is within valid range if phase count changes
if st.session_state['setup_step'] > 6:
    st.session_state['setup_step'] = 6

# --- QUERY PARAM HANDLING (For HTML Button) ---
# Check if the HTML button was clicked via URL param
if "setup" in st.query_params:
    st.session_state['setup_active'] = True
    # We do NOT clear query params immediately to allow the #anchor to work for scrolling
    # st.query_params.clear() 

# --- CREATOR BADGE (FIXED POSITION) ---
st.markdown("""
<div style="position: fixed; top: 0.8rem; right: 1rem; z-index: 999999; background: rgba(0,0,0,0.8); border: 1px solid #00f3ff; border-radius: 4px; padding: 5px 10px; box-shadow: 0 0 10px rgba(0,243,255,0.2);">
    <a href="https://www.linkedin.com/in/pawan-kumar-verma" target="_blank" style="text-decoration: none; display: flex; align-items: center; gap: 8px;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #aaa;">SYSTEM_ARCHITECT:</span>
        <span style="font-family: 'Oswald', sans-serif; font-size: 0.85rem; color: #00f3ff; letter-spacing: 1px;">PAWAN KUMAR VERMA</span>
    </a>
</div>
""", unsafe_allow_html=True)

# --- ULTRA MODERN DARK THEME CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&family=JetBrains+Mono:wght@400;500;800&family=Oswald:wght@500;700&display=swap');

    :root {
        --bg-depth: #050505;
        --bg-surface: #121212;
        --bg-card: #0a0a0a;
        --text-primary: #e0e0e0;
        --text-secondary: #808080;
        --accent-primary: #6366f1; 
        --accent-glow: rgba(99, 102, 241, 0.3);
        --border: #333;
        --success: #00ff9d;
        --yt-red: #ff0000;
        --radius-sm: 2px;
        --radius-md: 4px;
        --neon-blue: #00f3ff;
    }
    
    /* GLOBAL RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
        color: var(--text-primary);
        background-color: var(--bg-depth);
        font-size: 1rem;
        -webkit-font-smoothing: antialiased;
    }
    
    /* Force Dark Background on Main Container with Grid */
    .stApp {
        background-color: #000;
        /* GLOBAL BACKGROUND GRID (Increased Visibility) */
        background-image: 
            linear-gradient(rgba(0, 243, 255, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 243, 255, 0.08) 1px, transparent 1px);
        background-size: 40px 40px;
        background-attachment: fixed;
    }

    /* HIDE STREAMLIT CHROME */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        max-width: 95rem; 
    }

    /* --- TECHY HERO SECTION (ANIMATED) --- */
    .hero-container {
        position: relative;
        text-align: center;
        margin-bottom: 2rem; 
        padding: 8rem 3rem 6rem 3rem; 
        background-color: rgba(5, 5, 5, 0.7); 
        /* HERO SPECIFIC GRID (Distinct Tech Look) */
        background-image: 
            linear-gradient(rgba(99, 102, 241, 0.15) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 102, 241, 0.15) 1px, transparent 1px);
        background-size: 20px 20px;
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        box-shadow: inset 0 0 50px rgba(0,0,0,0.8);
        overflow: hidden;
        transition: all 0.3s ease;
        backdrop-filter: blur(4px);
    }

    /* Scanning Line Animation */
    .scan-line {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 0.125rem; /* 2px */
        background: linear-gradient(90deg, transparent, #6366f1, transparent);
        opacity: 0.5;
        animation: scan 3s ease-in-out infinite;
        box-shadow: 0 0 0.9375rem rgba(99, 102, 241, 0.8);
        pointer-events: none;
    }

    @keyframes scan {
        0% { top: -10%; }
        100% { top: 110%; }
    }

    /* Glitch Title Effect */
    .hero-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 4rem;
        font-weight: 800;
        color: #fff;
        text-transform: uppercase;
        letter-spacing: -0.05em;
        position: relative;
        display: inline-block;
        margin-bottom: 1rem;
        text-shadow: 3px 3px 0px rgba(99, 102, 241, 0.8), -2px -2px 0px rgba(6, 182, 212, 0.8);
    }
    
    .hero-title::before {
        content: attr(data-text);
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: #0b0d11;
        opacity: 0.8;
        clip-path: polygon(0 0, 100% 0, 100% 45%, 0 45%);
        transform: translate(-0.1875rem, 0);
        animation: glitch-anim-1 2.5s infinite linear alternate-reverse;
    }
    
    .hero-title::after {
        content: attr(data-text);
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: #0b0d11;
        opacity: 0.8;
        clip-path: polygon(0 55%, 100% 55%, 100% 100%, 0 100%);
        transform: translate(0.1875rem, 0);
        animation: glitch-anim-2 3s infinite linear alternate-reverse;
    }
    @keyframes glitch-anim-1 {
        0% { clip-path: inset(20% 0 80% 0); transform: translate(-0.125rem, 0.0625rem); }
        20% { clip-path: inset(60% 0 10% 0); transform: translate(0.125rem, -0.0625rem); }
        40% { clip-path: inset(40% 0 50% 0); transform: translate(-0.125rem, 0.125rem); }
        60% { clip-path: inset(80% 0 5% 0); transform: translate(0.0625rem, -0.125rem); }
        80% { clip-path: inset(10% 0 70% 0); transform: translate(-0.0625rem, 0.0625rem); }
        100% { clip-path: inset(30% 0 20% 0); transform: translate(0.125rem, -0.0625rem); }
    }
    @keyframes glitch-anim-2 {
        0% { clip-path: inset(10% 0 60% 0); transform: translate(0.125rem, -0.0625rem); }
        20% { clip-path: inset(80% 0 5% 0); transform: translate(-0.125rem, 0.125rem); }
        40% { clip-path: inset(30% 0 20% 0); transform: translate(0.0625rem, -0.125rem); }
        60% { clip-path: inset(10% 0 80% 0); transform: translate(-0.0625rem, 0.0625rem); }
        80% { clip-path: inset(50% 0 30% 0); transform: translate(0.125rem, -0.125rem); }
        100% { clip-path: inset(20% 0 70% 0); transform: translate(-0.125rem, 0.0625rem); }
    }

    /* Robot Text Animation */
    @keyframes robot-glitch-text {
        0% { opacity: 1; transform: translateX(0); text-shadow: 0 0 5px rgba(99, 102, 241, 0.8); }
        1% { opacity: 0.8; transform: translateX(2px); text-shadow: 2px 0 0 red; }
        2% { opacity: 1; transform: translateX(-2px); text-shadow: -2px 0 0 blue; }
        3% { opacity: 1; transform: translateX(0); text-shadow: 0 0 5px rgba(99, 102, 241, 0.8); }
        50% { opacity: 1; }
        51% { opacity: 0.5; transform: skewX(10deg); }
        52% { opacity: 1; transform: skewX(0deg); }
        100% { opacity: 1; }
    }

    /* --- TEXT ROTATOR FOR SUBTITLE --- */
    .hero-subtitle-container {
        position: relative;
        height: 1.875rem; /* Fixed height ~30px */
        width: 100%;
        display: flex;
        justify-content: center;
        overflow: hidden;
        margin-bottom: 2rem;
    }
    .hero-subtitle {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-secondary);
        font-size: 0.95rem;
        letter-spacing: 0.05em;
        position: absolute;
        width: 100%;
        text-align: center;
        opacity: 0;
        animation: rotate-text 16s infinite; 
    }
    
    .hero-subtitle:nth-child(1) { animation-delay: 0s; }
    .hero-subtitle:nth-child(2) { animation-delay: 4s; }
    .hero-subtitle:nth-child(3) { animation-delay: 8s; }
    .hero-subtitle:nth-child(4) { animation-delay: 12s; }
    @keyframes rotate-text {
        0% { opacity: 0; transform: translateY(1.25rem); }
        5% { opacity: 1; transform: translateY(0); }
        25% { opacity: 1; transform: translateY(0); }
        30% { opacity: 0; transform: translateY(-1.25rem); }
        100% { opacity: 0; transform: translateY(-1.25rem); }
    }
    
    .robot-text {
        display: inline-block;
        font-weight: 700;
        color: #fff;
        animation: robot-glitch-text 4s infinite linear;
    }

    /* --- HERO CTA BUTTON (Robotic/YouTube) --- */
    .hero-btn-wrapper {
        display: flex;
        justify-content: center;
        margin-top: 1rem;
        z-index: 10;
        position: relative;
    }
    .hero-scan-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
        background-color: #FF0000; /* FIXED: Red Background */
        color: #ffffff !important; /* FIXED: White Text */
        text-decoration: none;
        padding: 0.8rem 2rem;
        border-radius: 0.25rem; /* Slightly rounded like YT */
        font-family: 'Oswald', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        border: 1px solid #FF0000;
        box-shadow: 0 0 1.5rem rgba(255, 0, 0, 0.2);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
    }
    .hero-scan-btn:hover {
        background-color: #CC0000; /* HOVER: Darker Red */
        color: #ffffff !important; /* HOVER: White Text */
        box-shadow: 0 0 2.5rem rgba(255, 0, 0, 0.7);
        transform: scale(1.05);
        border-color: #CC0000;
    }
    
    /* Active State to appear clicked */
    .hero-scan-btn:active {
        transform: scale(0.98);
    }
    .btn-icon {
        font-size: 1.2rem;
        display: flex;
        align-items: center;
    }

    /* --- TECH CARDS (OVERVIEW) --- */
    .tech-card-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(15.625rem, 1fr));
        gap: 1.25rem;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1; /* Sit above the faded text */
    }
    
    .tech-card {
        background-color: #0b0d11;
        background-image: 
            linear-gradient(rgba(255, 255, 255, 0.03) 0.0625rem, transparent 0.0625rem),
            linear-gradient(90deg, rgba(255, 255, 255, 0.03) 0.0625rem, transparent 0.0625rem);
        background-size: 1.25rem 1.25rem; /* 20px */
        border: 0.0625rem solid var(--border);
        border-radius: 0.5rem;
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        box-shadow: 0 0.25rem 1.25rem rgba(0,0,0,0.4);
    }
    
    /* YOUTUBE CARD SPECIAL STYLING */
    .card-yt {
        border-color: #333;
        border-left: 0.25rem solid var(--yt-red);
        background: linear-gradient(180deg, rgba(255, 0, 0, 0.05) 0%, #0f0f0f 100%);
    }
    
    .card-yt:hover {
        box-shadow: 0 0 1.875rem rgba(255, 0, 0, 0.15) inset;
        transform: translateY(-0.1875rem);
    }
    
    /* YouTube Logo Construction in Pure CSS */
    .yt-logo-css {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.25rem;
        height: 1.5rem;
        background-color: var(--yt-red);
        border-radius: 0.375rem;
        margin-right: 0.625rem;
        box-shadow: 0 0 0.625rem var(--yt-red);
        position: relative;
    }
    
    .yt-play-icon {
        width: 0; 
        height: 0; 
        border-top: 0.3125rem solid transparent;
        border-bottom: 0.3125rem solid transparent;
        border-left: 0.5rem solid white;
        margin-left: 0.125rem;
    }
    /* Other Cards */
    .card-cv:hover { border-color: #22d3ee; box-shadow: 0 0 1.25rem rgba(34, 211, 238, 0.15) inset; transform: translateY(-0.1875rem); }
    .card-dl:hover { border-color: #10b981; box-shadow: 0 0 1.25rem rgba(16, 185, 129, 0.15) inset; transform: translateY(-0.1875rem); }
    .card-title {
        font-family: 'Oswald', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        letter-spacing: 0.03125rem;
    }
    
    .card-desc {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    .card-scan-overlay {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: repeating-linear-gradient(0deg, rgba(0,0,0,0.2) 0px, rgba(0,0,0,0.2) 0.0625rem, transparent 0.0625rem, transparent 0.125rem);
        pointer-events: none;
    }
    /* Highlighted Text */
    .highlight-yt {
        color: #fff;
        background: rgba(255, 0, 0, 0.2);
        padding: 0.1rem 0.3rem;
        border-radius: 0.2rem;
        border: 1px solid rgba(255, 0, 0, 0.4);
        font-weight: 600;
    }
    
    .highlight-exam {
        color: #fff;
        background: rgba(16, 185, 129, 0.2);
        padding: 0.1rem 0.3rem;
        border-radius: 0.2rem;
        border: 1px solid rgba(16, 185, 129, 0.4);
        font-weight: 600;
    }

    /* --- DEMO VISUALIZER --- */
    .demo-container {
        margin: 2rem 0;
        padding: 2rem;
        background: #080a0f;
        border: 1px solid #334155;
        border-radius: 12px;
        position: relative;
        overflow: hidden;
    }
    
    .demo-header {
        font-family: 'JetBrains Mono', monospace;
        color: #64748b;
        font-size: 0.8rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem;
    }
    
    .demo-stage {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        position: relative;
        z-index: 2;
    }
    
    .demo-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 2;
        width: 100px;
    }
    
    .node-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        background: #1e293b;
        border: 1px solid #475569;
        margin-bottom: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.5);
    }
    
    .yt-icon { color: #ff0000; border-color: rgba(255,0,0,0.3); animation: pulse-red 2s infinite; }
    .ai-icon { color: #22d3ee; border-color: rgba(34,211,238,0.3); animation: pulse-cyan 2s infinite; }
    
    .node-label {
        font-family: 'Oswald', sans-serif;
        color: #f8fafc;
        font-size: 0.9rem;
        letter-spacing: 1px;
    }
    
    .node-status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        color: #64748b;
        margin-top: 4px;
    }
    
    .demo-link {
        flex: 1;
        height: 2px;
        background: #1e293b;
        position: relative;
        margin: 0 20px;
        top: -25px; /* Adjust based on icon height */
    }
    
    .data-packet {
        position: absolute;
        width: 20px;
        height: 4px;
        background: #6366f1;
        top: -1px;
        border-radius: 2px;
        box-shadow: 0 0 10px #6366f1;
        animation: flow 1.5s infinite linear;
        opacity: 0;
    }
    
    .packet-green {
        background: #10b981;
        box-shadow: 0 0 10px #10b981;
    }
    
    @keyframes flow {
        0% { left: 0%; opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { left: 100%; opacity: 0; }
    }
    
    @keyframes pulse-red { 0%, 100% { box-shadow: 0 0 0 rgba(255,0,0,0); } 50% { box-shadow: 0 0 15px rgba(255,0,0,0.3); } }
    @keyframes pulse-cyan { 0%, 100% { box-shadow: 0 0 0 rgba(34,211,238,0); } 50% { box-shadow: 0 0 15px rgba(34,211,238,0.3); } }
    
    /* Slide Stack Animation */
    .slide-stack { position: relative; width: 60px; height: 60px; margin-bottom: 10px; }
    .slide {
        position: absolute;
        width: 40px;
        height: 28px;
        background: #1e293b;
        border: 1px solid #10b981;
        border-radius: 4px;
        left: 10px;
        top: 16px;
        opacity: 0;
    }
    
    .s1 { animation: slide-pop 3s infinite; animation-delay: 0s; z-index: 1; }
    .s2 { animation: slide-pop 3s infinite; animation-delay: 1s; z-index: 2; transform: translate(5px, -5px); background: #0f1117; }
    .s3 { animation: slide-pop 3s infinite; animation-delay: 2s; z-index: 3; transform: translate(10px, -10px); background: #0f1117; }
    
    @keyframes slide-pop {
        0% { opacity: 0; transform: translateY(10px) scale(0.9); }
        20% { opacity: 1; transform: translateY(0) scale(1); }
        80% { opacity: 1; }
        100% { opacity: 0; }
    }
    
    .demo-terminal {
        background: #000;
        padding: 1rem;
        border-radius: 6px;
        border-left: 2px solid #6366f1;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #4ade80;
        display: flex;
        flex-direction: column;
        gap: 5px;
    }
    .term-line { opacity: 0.8; }

    /* --- INPUTS --- */
    .stTextInput input {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: #00f3ff !important; /* Neon Blue Text */
        font-family: 'JetBrains Mono', monospace;
        border-radius: 0px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput input:focus {
        border-color: #00f3ff !important;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.2) !important;
    }

    /* --- BUTTONS --- */
    div.stButton > button {
        background-color: var(--bg-surface);
        border: 1px solid var(--border);
        color: var(--text-primary);
        border-radius: 0px; /* Square corners for robotics look */
        padding: 0.6rem 1.2rem;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
        transition: all 0.2s ease;
    }
    
    div.stButton > button:hover {
        background-color: var(--border);
        border-color: var(--text-secondary);
    }
    
    button[kind="primary"] {
        background: rgba(0, 243, 255, 0.1) !important;
        border: 1px solid #00f3ff !important;
        color: #00f3ff !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2);
    }
    
    button[kind="primary"]:hover {
        background: rgba(0, 243, 255, 0.2) !important;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
    }
    
    /* SPECIAL SCAN BUTTON STYLE */
    button[kind="secondary"] {
        background-color: #000 !important;
        border: 1px solid var(--yt-red) !important;
        color: var(--yt-red) !important;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 2px;
        font-weight: 800;
        box-shadow: 0 0 10px rgba(255, 0, 0, 0.2) !important;
    }
    button[kind="secondary"]:hover {
        background-color: var(--yt-red) !important;
        color: #fff !important;
        box-shadow: 0 0 20px rgba(255, 0, 0, 0.5) !important;
    }

    /* --- CONSOLE OUTPUT --- */
    .console-box {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8125rem;
        background: #000000;
        border: 1px solid #333;
        border-left: 3px solid var(--success);
        padding: 0.875rem;
        color: #4ade80; /* Terminal Green */
        display: flex;
        align-items: center;
        gap: 0.75rem;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
    }
    
    .blink { animation: blinker 1s step-end infinite; }
    @keyframes blinker { 50% { opacity: 0; } }

    /* --- GENERAL UI --- */
    .section-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #00f3ff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        padding-bottom: 5px;
    }
    
    /* UNIVERSAL IMAGE STYLING */
    div[data-testid="stImage"] {
        border-radius: 4px;
        border: 1px solid #333;
        overflow: hidden;
    }
    
    div[data-testid="stImage"] img {
        transition: transform 0.3s ease;
    }
    
    div[data-testid="stImage"]:hover {
        border-color: #00f3ff;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    }
    
    /* --- SETUP PROTOCOL STYLING --- */
    div[data-testid="stVerticalBlock"]:has(div.setup-wizard-marker) {
        background-color: rgba(5, 5, 5, 0.95); 
        border: 1px solid #222; 
        box-shadow: 0 0 50px rgba(0,0,0,0.8) inset;
        border-radius: 4px;
        padding: 2rem;
        margin-top: 1.5rem; 
        position: relative;
        overflow: hidden;
        animation: slideDown 0.6s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    
    /* INPUT CONSOLE STYLING */
    div[data-testid="stVerticalBlock"]:has(div.input-console-marker) {
        background-color: #000;
        border: 1px solid #333;
        border-left: 4px solid var(--yt-red); 
        padding: 1.5rem;
        box-shadow: 0 0 20px rgba(0,0,0,0.8) inset;
        margin-bottom: 2rem;
        position: relative;
    }
    
    /* FOOTER STYLING */
    .tech-footer {
        margin-top: 5rem;
        padding: 2rem 0;
        border-top: 1px solid #222;
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #555;
    }
    .tech-footer a {
        color: #00f3ff;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    .tech-footer a:hover {
        color: #fff;
        text-shadow: 0 0 5px #00f3ff;
    }
    
    @keyframes slideDown { 
        from { opacity: 0; transform: translateY(-10px); } 
        to { opacity: 1; transform: translateY(0); } 
    }
</style>
""", unsafe_allow_html=True)

# --- HELPERS ---

def get_video_info(url, cookies=None, proxy=None):
    opts = {
        'quiet': True, 
        'nocheckcertificate': True, 
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'noplaylist': True,
        'force_ipv4': True,  # ADDED: Forces IPv4 to reduce block chance
        'cachedir': False,   # ADDED: Disables cache to avoid stale auth data
    }
    if cookies: opts['cookiefile'] = cookies
    if proxy: opts['proxy'] = proxy
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False), None
    except Exception as e:
        return None, str(e)

# Removed create_pdf as it is no longer needed in this flow
def fmt(s):
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{int(h):02}:{int(m):02}:{int(s):02}"

def create_zip_from_dir(directory):
    if not os.path.exists(directory) or not os.listdir(directory):
        return None
    zip_path = os.path.join(tempfile.gettempdir(), "captured_slides.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    return zip_path

# --- HERO SECTION (CONDITIONAL) ---
if not st.session_state['setup_active']:
    st.markdown("""
    <div class="hero-container">
    <div class="scan-line"></div>
    <div class="hero-title" data-text="LECTURENOTES_PRO">LECTURENOTES_PRO</div>
    <br>
    <div class="hero-subtitle-container">
    <div class="hero-subtitle">>> INITIALIZING <span class="robot-text">INTELLIGENT VIDEO PARSER v1.0</span>...</div>
    <div class="hero-subtitle">>> DETECTING SIGNIFICANT VISUAL CHANGES IN LECTURE STREAMS...</div>
    <div class="hero-subtitle">>> GENERATING EXAM-READY STUDY MATERIAL AUTOMATICALLY...</div>
    <div class="hero-subtitle">>> OPTIMIZING CONTENT FOR RAPID KNOWLEDGE INGESTION...</div>
    </div>
    <div class="hero-btn-wrapper">
    <a href="?setup=true#setup_location" class="hero-scan-btn" target="_self">
    <span class="btn-icon">▶</span> SCAN_LECTURE // INITIATE_SETUP
    </a>
    </div>
    </div>
    """, unsafe_allow_html=True)

# --- SETUP PROTOCOL WIZARD ---
if st.session_state.get('setup_active', False): 
    st.markdown('<div id="setup_location"></div>', unsafe_allow_html=True)
    
    if 'setup_step' not in st.session_state:
        st.session_state.setup_step = 1
    
    step = st.session_state.setup_step
    
    # Placeholder Logic
    def get_step_image(step_num):
        fname = f"step_0{step_num}.jpg"
        if os.path.exists(fname): return fname
        return None

    # Distinct Container
    with st.container():
        st.markdown('<div class="setup-wizard-marker"></div>', unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div style="text-align:center; margin-bottom: 2rem;">
            <div style="display:flex; justify-content:center; gap:8px; margin-bottom:5px; opacity:0.6;">
                <div style="width:12px; height:4px; background:var(--text-secondary);"></div>
                <div style="width:12px; height:4px; background:var(--text-secondary);"></div>
                <div style="width:12px; height:4px; background:var(--text-secondary);"></div>
            </div>
            <div style="font-family:'JetBrains Mono', monospace; font-size: 3rem; font-weight:800; color:var(--text-secondary); letter-spacing: -2px; text-transform:uppercase;">
                <span style="opacity:0.5;">SETUP EASILY AND USE</span> <span style="background: linear-gradient(to bottom, #ff0000, #550000); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 4rem;">FREE</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        status_map = {
            1: "INSTALLING_BRIDGE",
            2: "VERIFYING_SESSION",
            3: "INITIATING_EXTRACT",
            4: "EXPORTING_TOKEN",
            5: "AWAITING_UPLOAD",
            6: "TARGET_ACQUISITION"
        }
        
        is_verified = st.session_state.get('cookies_path') is not None
        status_text = "AUTH_VERIFIED" if is_verified else status_map.get(step, "PROCESSING")
        status_color = "#10b981" if is_verified else "#ef4444" 
        
        st.markdown(f"""
            <div style="border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; font-family: 'JetBrains Mono'; font-size: 0.8rem;">
                <span style="color: #00f3ff;">>> SETUP_PROTOCOL // PHASE_{step:02d}</span>
                <span style="color:{status_color}">STATUS: {status_text}</span>
            </div>
        """, unsafe_allow_html=True)
        
        if step < 6:
            c_text, c_img = st.columns([1, 1], gap="medium")
            with c_text:
                if step == 1:
                    st.info("⚠️ **ACTION REQUIRED**")
                    st.markdown("""
                        **1. Install Authentication Bridge**
                        To access restricted content, the system requires a verified session token.
                        Download **[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?pli=1)**.
                    """)
                elif step == 2:
                    st.info("🔐 **VERIFY SESSION**")
                    st.markdown("""
                        **2. Open Target Source**
                        Open **YouTube.com** in a new browser tab and ensure you are **Signed In**.
                        **3. Access Extensions**
                        Click the **Extensions Puzzle Piece** icon in Chrome.
                    """)
                elif step == 3:
                    st.info("🖱️ **SELECT EXTRACTOR**")
                    st.markdown("""
                        **4. Initialize Extraction**
                        Click **'Get cookies.txt LOCALLY'** from your extensions list to prepare session data.
                    """)
                elif step == 4:
                    st.info("⬇️ **EXPORT CREDENTIALS**")
                    st.markdown("""
                        **5. Download Session Token**
                        Click the **Blue 'Export' Button** in the extension popup to get the `.txt` file.
                    """)
                elif step == 5:
                    st.success("✅ **UPLOAD VERIFICATION**")
                    st.markdown("**6. Authorize System**\nUpload `www.youtube.com_cookies.txt` below.")
                    uploaded_cookie = st.file_uploader("UPLOAD COOKIES.TXT", type=['txt'], label_visibility="collapsed")
                    if uploaded_cookie:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='wb') as fp:
                            fp.write(uploaded_cookie.getvalue())
                            st.session_state['cookies_path'] = fp.name
                        # Removed st.rerun() to prevent loop
                        st.info("Configuration Loaded. Proceed to Next Phase.")
            with c_img:
                img_path = get_step_image(step)
                st.markdown('<div class="step-image-container">', unsafe_allow_html=True)
                if img_path:
                    st.image(img_path, use_container_width=True)
                else:
                    st.code(f"[SYSTEM_ERR: VISUAL_GUIDE_MISSING]\nLoading: step_0{step}.jpg...", language="bash")
                st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            # --- STEP 6: INTEGRATED SCANNING ---
            st.markdown("""
            <div style="border: 1px dashed #444; padding: 10px; background: rgba(0,0,0,0.5); font-family:'JetBrains Mono'; font-size:0.8rem; color:#888;">
            // TARGET ACQUISITION MODE_
            </div>
            """, unsafe_allow_html=True)
            
            # Embedded Input Console Styling
            st.markdown('<div class="input-console-marker"></div>', unsafe_allow_html=True)
            
            # Input Row
            col_in, col_btn = st.columns([3, 1])
            with col_in:
                url_wiz = st.text_input("INPUT SOURCE", value=st.session_state['url_input'], placeholder="ENTER_SECURE_LINK [https://youtube.com/...]", label_visibility="collapsed", key="wiz_url")
            with col_btn:
                if st.button(">> INITIALIZE_TARGET_LOCK", type="primary", use_container_width=True):
                    if not url_wiz:
                        st.warning("Target URL required.")
                    else:
                        st.session_state['url_input'] = url_wiz
                        st.session_state['scan_complete'] = False # Reset scan status
                        # Fetch proxy from secrets if available
                        proxy_url = None
                        try:
                            proxy_url = st.secrets["proxy_url"]
                        except Exception:
                            pass # Development mode or no secrets file
                        
                        info, err = get_video_info(url_wiz, cookies=st.session_state.get('cookies_path'), proxy=proxy_url)
                        if info:
                            st.session_state['video_info'] = info
                        else:
                            st.error(f"TARGET LOCK FAILED: {err}")
            
            # If Video Info is loaded, show controls and Scan Button
            if st.session_state['video_info']:
                meta = st.session_state['video_info']
                
                # --- NEW: Thumbnail and Duration Display ---
                col_meta_img, col_meta_text = st.columns([1, 2])
                with col_meta_img:
                    # (a. thumbnail of the video)
                    if meta.get('thumbnail'):
                        st.image(meta.get('thumbnail'), use_container_width=True)
                with col_meta_text:
                    st.markdown(f"<div style='font-family: Oswald; font-size: 1.5rem; color: #fff;'>{meta.get('title')[:60]}...</div>", unsafe_allow_html=True)
                    duration = meta.get('duration') or 0
                    st.markdown(f"<span style='color:#00f3ff; font-family: JetBrains Mono;'>DURATION_LOCK: {fmt(duration)}</span>", unsafe_allow_html=True)
                
                # Configuration Area (Sliders)
                with st.expander(">> CONFIGURATION_MATRIX", expanded=True):
                    # Quality & Time
                    c_conf1, c_conf2 = st.columns(2)
                    with c_conf1:
                        st.markdown("**STREAM PARAMETERS**")
                        # Format Logic
                        fmts = [f for f in meta.get('formats', []) if f.get('height')]
                        heights = sorted(list(set(f['height'] for f in fmts)), reverse=True)
                        q_map = {f"{h}p RAW": f"bestvideo[height<={h}]/best[height<={h}]" for h in heights}
                        q_map["AUTO_NEGOTIATE"] = "bestvideo/best"
                        qual = st.selectbox("QUALITY STREAM", list(q_map.keys()), label_visibility="collapsed")
                    
                    with c_conf2:
                        st.markdown("**TEMPORAL WINDOW**")
                        if duration <= 0: duration = 100
                        # Slider with KEY to prevent resetting
                        start_t, end_t = st.slider("PROCESS WINDOW (Seconds)", 0, duration, (0, duration), key="time_range_slider")
                        st.caption(f"Selected Range: {fmt(start_t)} - {fmt(end_t)}")
                        
                    st.markdown("---")
                    
                    c_adv1, c_adv2 = st.columns(2)
                    with c_adv1:
                        st.caption("VISUAL SENSITIVITY")
                        st.slider("Pixel Delta (Sensitivity)", 10, 100, key='sensitivity', help="Higher = Less sensitive to subtle pixel changes")
                        st.slider("Strictness (% Area)", 0.1, 5.0, key='strictness', help="Min % of screen that must change to trigger capture")
                    with c_adv2:
                        st.caption("TEMPORAL SKIPPING")
                        st.slider("Min Skip (Seconds)", 1, 5, key='min_skip', help="Minimum time to wait after a capture")
                        st.slider("Max Skip (Seconds)", 5, 60, key='max_skip', help="Maximum time to jump if no changes found")
                # EXECUTION & STOP BUTTONS
                c_exec, c_stop = st.columns([3, 1])
                with c_exec:
                    init_scan = st.button(">> EXECUTE_ANALYSIS_SEQUENCE", type="secondary", use_container_width=True)
                with c_stop:
                    # Stop button logic: this triggers a rerun, effectively stopping the loop
                    st.button("STOP", type="primary", use_container_width=True, help="Interrupts scan.")
                if init_scan:
                    # --- SCANNIN LOGIC MOVED HERE ---
                    st.session_state['scan_complete'] = False
                    
                    # CLEANUP TEMP DIR FOR NEW SCAN
                    if os.path.exists(st.session_state['scan_temp_dir']):
                        shutil.rmtree(st.session_state['scan_temp_dir'])
                    os.makedirs(st.session_state['scan_temp_dir'], exist_ok=True)
                    
                    console_ph = st.empty()
                    console_ph.markdown('<div class="console-box"><span class="blink">_</span> ALLOCATING BUFFER...</div>', unsafe_allow_html=True)
                    prog_bar = st.progress(0)
                    
                    # Layout for live feed and last captured
                    st.markdown("**LIVE FEED & LATEST ARTIFACT:**")
                    live_col1, live_col2 = st.columns([2, 3])
                    with live_col1:
                        live_capture_area = st.empty()
                    with live_col2:
                        # Placeholder for the immediate download trigger
                        download_trigger_area = st.empty()
                        # Placeholder for showing the image
                        last_artifact_area = st.empty()
                    
                    ydl_opts = {
                        'format': q_map[qual], 
                        'quiet': True, 
                        'nocheckcertificate': True, 
                        'noplaylist': True,
                        'force_ipv4': True,  # FORCE IPV4 TO AVOID BLOCKS
                        'cachedir': False,   # DISABLE CACHE TO AVOID STALE COOKIES
                        'cookiefile': st.session_state.get('cookies_path'),
                        # ADDED: detailed headers to mimic a real browser to avoid 403/signature issues
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Accept': '*/*',
                            'Accept-Language': 'en-US,en;q=0.5',
                        }
                    }
                    
                    # Add proxy if available in secrets
                    try:
                        if "proxy_url" in st.secrets:
                            ydl_opts['proxy'] = st.secrets["proxy_url"]
                    except Exception:
                        pass
                    
                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            stream_link = ydl.extract_info(url_wiz, download=False).get('url')
                            
                            if stream_link:
                                console_ph.markdown(f'<div class="console-box"><span class="blink">●</span> STREAM LOCKED. SEEKING: {fmt(start_t)}</div>', unsafe_allow_html=True)
                                
                                cap = cv2.VideoCapture(stream_link, cv2.CAP_FFMPEG)
                                if cap.isOpened():
                                    fps = cap.get(cv2.CAP_PROP_FPS) or 30
                                    cap.set(cv2.CAP_PROP_POS_MSEC, start_t * 1000)
                                    
                                    last = None
                                    curr = int(start_t * fps)
                                    end = int(end_t * fps)
                                    total = max(1, end - curr)
                                    origin = curr
                                    
                                    sensitivity = st.session_state['sensitivity']
                                    strictness = st.session_state['strictness']
                                    min_skip = st.session_state['min_skip']
                                    max_skip = st.session_state['max_skip']
                                    
                                    slide_counter = 0
                                    start_scan_time = time.time()
                                    max_scan_duration = 600  # 10 minutes limit
                                    max_slides_limit = 100    # Max 100 slides
                                    retry_tolerance = 5
                                    retries = 0
                                    
                                    while curr < end:
                                        # 1. Timeout Check
                                        if time.time() - start_scan_time > max_scan_duration:
                                            st.warning(f"Scan paused after {max_scan_duration}s to prevent timeout. Download results below.")
                                            break
                                        
                                        # 2. Slide Limit Check
                                        if slide_counter >= max_slides_limit:
                                            st.warning(f"Slide limit ({max_slides_limit}) reached to conserve storage.")
                                            break
                                        
                                        cap.set(cv2.CAP_PROP_POS_FRAMES, curr)
                                        ret, frame = cap.read()
                                        
                                        # 3. Stream Stability Check (Retry Logic)
                                        if not ret:
                                            retries += 1
                                            if retries > retry_tolerance:
                                                st.error("Stream connection lost after multiple retries.")
                                                break
                                            time.sleep(1) # Wait a bit before retry
                                            continue
                                        retries = 0 # Reset retries on success
                                        if not ret: break
                                        
                                        # Update metrics
                                        p = (curr - origin) / total
                                        prog_bar.progress(min(max(p, 0.0), 1.0))
                                        ts = fmt(curr / fps)
                                        console_ph.markdown(f'<div class="console-box"><span class="blink">●</span> PROCESSING: {ts} | BUFFER: OK</div>', unsafe_allow_html=True)
                                        
                                        # CV Logic
                                        small = cv2.resize(frame, (640, 360))
                                        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                                        gray = cv2.GaussianBlur(gray, (21, 21), 0)
                                        
                                        is_diff = False
                                        if last is None:
                                            is_diff = True
                                            last = gray
                                        else:
                                            d = cv2.absdiff(last, gray)
                                            _, th = cv2.threshold(d, sensitivity, 255, cv2.THRESH_BINARY)
                                            if np.sum(th) > (640 * 360 * (strictness/100) * 255):
                                                is_diff = True
                                                last = gray
                                        
                                        if is_diff:
                                            slide_counter += 1
                                            
                                            # SAVE TO DISK (DISK BUFFER)
                                            file_name = f"slide_{slide_counter:03d}.jpg"
                                            save_path = os.path.join(st.session_state['scan_temp_dir'], file_name)
                                            # 4. JPEG Compression (Quality 50) to save disk space
                                            cv2.imwrite(save_path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                                            
                                            # Live Updates
                                            disp_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                            live_capture_area.image(disp_img, caption=f"LIVE SCAN: {ts}", use_container_width=True)
                                            
                                            # Update Last Artifact View (Only one image stored in view)
                                            last_artifact_area.image(disp_img, caption=f"LAST CAPTURED: Slide {slide_counter}", use_container_width=True)
                                            
                                            st.toast(f"Event Logged: {ts} -> Saved to Disk")
                                            curr += int(fps * max_skip)
                                        else:
                                            curr += int(fps * min_skip)
                                    
                                    cap.release()
                                    prog_bar.progress(1.0)
                                    st.session_state['scan_complete'] = True 
                                    console_ph.markdown('<div class="console-box" style="color:#10b981; border-color:#10b981;">✓ SEQUENCE COMPLETE</div>', unsafe_allow_html=True)
                                    
                                else:
                                    st.error("STREAM HANDSHAKE FAILED. Try refreshing cookies or ensure your IP is not blocked.")
                    except Exception as e:
                        st.error(f"Error during scan: {str(e)}")
            # --- DISPLAY RESULTS (IF ANY IMAGES EXIST ON DISK) ---
            # Checks if temp dir exists and is not empty
            has_files = False
            if os.path.exists(st.session_state['scan_temp_dir']) and len(os.listdir(st.session_state['scan_temp_dir'])) > 0:
                has_files = True
            if has_files:
                st.markdown("---")
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 10px; margin-bottom: 20px; color: #10b981; font-family: 'JetBrains Mono'; text-align: center;">
                ✓ DATA_EXTRACTION_BUFFER_READY
                </div>
                """, unsafe_allow_html=True)
                
                # ZIP Download Logic
                zip_path = create_zip_from_dir(st.session_state['scan_temp_dir'])
                if zip_path and os.path.exists(zip_path):
                    with open(zip_path, "rb") as f:
                        st.download_button(">> DOWNLOAD CAPTURED IMAGES [ZIP]", f.read(), "lecture_slides.zip", "application/zip", type="primary", use_container_width=True)
                else:
                    st.warning("Could not generate ZIP archive.")
                
                # LATEST IMAGE PREVIEW (Optional: Shows the last image in the folder)
                files = sorted(os.listdir(st.session_state['scan_temp_dir']))
                if files:
                    last_img_path = os.path.join(st.session_state['scan_temp_dir'], files[-1])
                    st.image(last_img_path, caption="LATEST_CAPTURED_ARTIFACT", width=300)
        # Navigation Footer
        st.write("")
        c_nav1, c_nav2, c_nav3 = st.columns([1, 4, 1])
        
        with c_nav1:
            if step > 1:
                if st.button("<< PREV"):
                    st.session_state.setup_step -= 1
                    st.rerun()
        
        with c_nav2:
            pass # Removed dots for cleaner robotics look
            
        with c_nav3:
            if step < 6: # Standard Next for steps 1-5
                if st.button("NEXT >>"):
                    st.session_state.setup_step += 1
                    st.rerun()

# --- OTHER SECTIONS (HIDDEN WHEN SETUP IS ACTIVE) ---
if not st.session_state['setup_active']:
    st.divider()
    # --- VISUAL DEMONSTRATION SECTION ---
    st.markdown("""
    <div class="demo-container">
    <div class="demo-header">>> LIVE_DEMONSTRATION // NEURAL_PROCESSING_VISUALIZER</div>
    <div class="demo-stage">
    <!-- STAGE 1: RAW STREAM -->
    <div class="demo-node">
    <div class="node-icon yt-icon">▶</div>
    <div class="node-label">RAW_STREAM</div>
    <div class="node-status">BUFFERING...</div>
    </div>
    <!-- CONNECTION 1 -->
    <div class="demo-link">
    <div class="data-packet"></div>
    <div class="data-packet" style="animation-delay: 0.5s"></div>
    <div class="data-packet" style="animation-delay: 1.0s"></div>
    </div>
    <!-- STAGE 2: AI FILTER -->
    <div class="demo-node">
    <div class="node-icon ai-icon">⌾</div>
    <div class="node-label">SCAN</div>
    <div class="node-status" style="color:#22d3ee;">ANALYZING</div>
    </div>
    <!-- CONNECTION 2 -->
    <div class="demo-link">
    <div class="data-packet packet-green"></div>
    <div class="data-packet packet-green" style="animation-delay: 0.6s"></div>
    </div>
    <!-- STAGE 3: SLIDES -->
    <div class="demo-node">
    <div class="slide-stack">
    <div class="slide s1"></div>
    <div class="slide s2"></div>
    <div class="slide s3"></div>
    </div>
    <div class="node-label">SMART_DECK</div>
    <div class="node-status" style="color:#10b981;">OPTIMIZED</div>
    </div>
    </div>
    <div class="demo-terminal">
    <span class="term-line">> INGESTING_FRAME_BUFFER...</span>
    <span class="term-line">> DETECTING_REDUNDANCY... [SKIP]</span>
    <span class="term-line">> DETECTING_UNIQUE_CONTENT... [CAPTURE]</span>
    <span class="term-line blink">> COMPILING_ESSENTIAL_KNOWLEDGE...</span>
    </div>
    </div>
    """, unsafe_allow_html=True)
    # --- ROBOTIC SYSTEM OVERVIEW ---
    st.markdown("""
    <div style="text-align:center; margin-bottom: 2rem; margin-top: 3rem;">
        <div style="display:flex; justify-content:center; gap:8px; margin-bottom:5px; opacity:0.6;">
            <div style="width:12px; height:12px; background:var(--text-secondary); border-radius:2px;"></div>
            <div style="width:12px; height:12px; background:var(--text-secondary); border-radius:2px;"></div>
            <div style="width:12px; height:12px; background:var(--text-secondary); border-radius:2px;"></div>
        </div>
        <div style="font-family:'JetBrains Mono', monospace; font-size: 4.5rem; font-weight:800; color:var(--border); opacity:0.25; letter-spacing: -2px; -webkit-mask-image: linear-gradient(to bottom, black 50%, transparent 100%); mask-image: linear-gradient(to bottom, black 50%, transparent 100%);">
            SYSTEM ARCHITECTURE
        </div>
    </div>
    """, unsafe_allow_html=True)
    # Cards
    st.markdown("""
    <div class="tech-card-container">
    <div class="tech-card card-yt">
    <div class="card-scan-overlay"></div>
    <div class="card-title">
    <div class="yt-logo-css"><div class="yt-play-icon"></div></div>
    <span style="color:#fff;">LECTURE_FEED_INGEST</span>
    </div>
    <div class="card-desc">
    Feed the system any <span class="highlight-yt">YouTube Lecture URL</span>. The parser establishes a direct data pipe to the source, bypassing standard playback to access raw visual data.
    </div>
    </div>
    <div class="tech-card card-cv">
    <div class="card-scan-overlay"></div>
    <div class="card-title" style="color: #22d3ee;">
    <span style="font-size:1.2rem; margin-right:0.625rem;">⌾</span> SCAN
    </div>
    <div class="card-desc">
    <strong>Neural Scan Active.</strong> The algorithm compares consecutive scenes to detect significant visual changes (blackboard updates, new slides), filtering out noise and instructor movement.
    </div>
    </div>
    <div class="tech-card card-dl">
    <div class="card-scan-overlay"></div>
    <div class="card-title" style="color: #10b981;">
    <span style="font-size:1.2rem; margin-right:0.625rem;">🎓</span> RAPID_REVIEW_ARTIFACT
    </div>
    <div class="card-desc">
    <span class="highlight-exam">Exam Mode Enabled.</span> Essential visual data is captured and compiled into a streamlined PDF. Perfect for one-night-before study sessions and last-minute revision.
    </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

# --- FOOTER (ALWAYS VISIBLE) ---
st.markdown("""
<div class="tech-footer">
    SYSTEM_DESIGN BY 
    <a href="https://www.linkedin.com/in/pawan-kumar-verma" target="_blank">PAWAN KUMAR VERMA</a> 
    // <span style="opacity:0.5">ALL_RIGHTS_RESERVED_2024</span>
</div>
""", unsafe_allow_html=True)
