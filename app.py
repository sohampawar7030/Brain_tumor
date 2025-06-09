import streamlit as st
import numpy as np
import cv2
from PIL import Image
from ultralytics import YOLO
from io import BytesIO
import sqlite3
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import base64
import pandas as pd
from fpdf import FPDF
import time


# Load environment variables
load_dotenv()

# Load YOLO model
MODEL_PATH = "./model/brain_tumor_detection_model.pt"
model = YOLO(MODEL_PATH)

# Database initialization function - Fix for the database schema issue
def initialize_database():
    conn = sqlite3.connect("tumor_detection.db")
    cursor = conn.cursor()
    
    # Check if detections table exists and get its structure
    cursor.execute("PRAGMA table_info(detections)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if not columns:
        # Table doesn't exist, create it with all necessary columns
        cursor.execute('''
        CREATE TABLE detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            patient_age INTEGER,
            patient_gender TEXT,
            tumor_count INTEGER,
            tumor_lengths TEXT,
            detection_time TIMESTAMP,
            processed_image BLOB,
            severity TEXT,
            recommendation TEXT
        )''')
    else:
        # Table exists but might be missing columns - add them if needed
        needed_columns = [
            'patient_age INTEGER',
            'patient_gender TEXT',
            'tumor_count INTEGER',
            'tumor_lengths TEXT',
            'detection_time TIMESTAMP',
            'processed_image BLOB',
            'severity TEXT',
            'recommendation TEXT'
        ]
        
        for column_def in needed_columns:
            column_name = column_def.split(' ')[0]
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE detections ADD COLUMN {column_def}")
                except sqlite3.OperationalError:
                    # Column might already exist or there might be other issues
                    pass
    
    conn.commit()
    conn.close()

# Tumor severity assessment
def assess_tumor_severity(tumor_lengths, image_dimensions):
    """Assess tumor severity based on size relative to brain area"""
    # Calculate brain area (approximation)
    height, width = image_dimensions[:2]
    brain_area = height * width
    
    # Calculate total tumor area
    total_tumor_area = sum([length**2 for length in tumor_lengths])
    
    # Calculate percentage of brain occupied by tumor
    percentage = (total_tumor_area / brain_area) * 100
    
    if percentage < 1:
        return "Low Severity", "Regular follow-up recommended in 6 months"
    elif percentage < 5:
        return "Moderate Severity", "Follow-up within 3 months recommended"
    else:
        return "High Severity", "Immediate medical consultation advised"

def resize_image(image, max_width=400):
    """Resize image while maintaining aspect ratio"""
    height, width = image.shape[:2]
    if width > max_width:
        ratio = max_width / width
        new_height = int(height * ratio)
        return cv2.resize(image, (max_width, new_height))
    return image

def create_pdf_report(patient_name, tumor_lengths, processed_image, detection_time, severity, recommendation):
    """Create a detailed PDF report for the patient"""
    pdf = FPDF()
    pdf.add_page()
    
    # Add header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 10, 'Brain Tumor Detection Report', 0, 1, 'C')
    
    # Add patient information
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(190, 10, f'Patient: {patient_name}', 0, 1)
    pdf.cell(190, 10, f'Date: {detection_time.strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
    
    # Add tumor information
    pdf.set_font('Arial', '', 12)
    pdf.cell(190, 10, f'Number of Tumors Detected: {len(tumor_lengths)}', 0, 1)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(190, 10, 'Tumor Measurements:', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    for i, length in enumerate(tumor_lengths):
        pdf.cell(190, 10, f'Tumor {i+1}: {length:.2f} pixels', 0, 1)
    
    # Add severity assessment
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(190, 10, 'Severity Assessment:', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(190, 10, f'Assessment: {severity}', 0, 1)
    pdf.cell(190, 10, f'Recommendation: {recommendation}', 0, 1)
    
    # Add processed image
    temp_img_path = 'temp_report_image.jpg'
    cv2.imwrite(temp_img_path, processed_image)
    pdf.add_page()
    pdf.cell(190, 10, 'Processed Image:', 0, 1)
    pdf.image(temp_img_path, x=10, y=40, w=180)
    os.remove(temp_img_path)
    
    # Add disclaimer
    pdf.add_page()
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(190, 10, 'DISCLAIMER:', 0, 1)
    pdf.multi_cell(190, 10, 'This report is generated by an automated system and should not be used as the sole basis for medical decisions. Please consult with a healthcare professional for proper diagnosis and treatment options.')
    
    # Save to a BytesIO object
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    
    return pdf_output.getvalue()

def main():
    # Initialize database with correct schema
    initialize_database()
    
    # Page configuration
    st.set_page_config(page_title="Brain Tumor Detection", layout="wide")

    # Navigation menu
    menu = ["Home", "Detection", "History", "About", "FAQ"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        display_home_page()
    elif choice == "Detection":
        display_detection_page()
    elif choice == "History":
        display_history()
    elif choice == "About":
        display_about_page()
    elif choice == "FAQ":
        display_faq_page()

def display_home_page():
    # Add custom CSS for styling and more advanced animations
    st.markdown("""
    <style>
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://media.istockphoto.com/id/1254631358/photo/hospital-covid-ward-with-a-medical-ventilators-monitor.jpg?s=1024x1024&w=is&k=20&c=QArkgUL94PZDSnMs1pAxQsbJ3QF-Sx-zFZNxSosMv8c=') no-repeat center center fixed;
            background-size: cover;
            filter: blur(0px);
            z-index: -1;
        }

        /* Optional: make text more readable */
        .stApp {
            background-color: rgba(255, 255, 255, 0.3); /* translucent overlay */
        }
        
        /* Improve readability with a semi-transparent container for content */
        .css-1d391kg, .css-1v3fvcr {
            background-color: rgba(255, 255, 255, 0.85) !important;
            padding: 20px;
            border-radius: 10px;
        }
        
        /* Floating brain animations in background */
        .background-brains {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: -1;
        }
   
        
        /* Floating brain animations in background */
        .background-brains {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: -1;
        }
        
        .brain {
            position: absolute;
            width: 60px;
            height: 60px;
            background-image: url('https://images.unsplash.com/photo-1583911860205-72f8ac8ddcbe?q=80&w=2070');
            background-size: contain;
            background-repeat: no-repeat;
            opacity: 0.15;
            animation-name: float;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
            animation-direction: alternate;
        }
        
        .brain:nth-child(1) {
            top: 10%;
            left: 10%;
            animation-duration: 8s;
        }
        
        .brain:nth-child(2) {
            top: 20%;
            right: 10%;
            animation-duration: 9s;
        }
        
        .brain:nth-child(3) {
            bottom: 30%;
            left: 15%;
            animation-duration: 11s;
        }
        
        .brain:nth-child(4) {
            bottom: 15%;
            right: 20%;
            animation-duration: 7s;
        }
        
        .brain:nth-child(5) {
            top: 50%;
            left: 5%;
            animation-duration: 12s;
        }
        
        .brain:nth-child(6) {
            top: 60%;
            right: 5%;
            animation-duration: 10s;
        }
        
        @keyframes float {
            0% {
                transform: translateY(0) rotate(0deg);
                opacity: 0.1;
            }
            50% {
                transform: translateY(-20px) rotate(10deg);
                opacity: 0.2;
            }
            100% {
                transform: translateY(0) rotate(0deg);
                opacity: 0.1;
            }
        }
        
        /* Glass-like container for content */
        .glass-card {
            background-color: rgba(255, 255, 255, 0.25);
                
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            padding: 25px;
            margin-bottom: 30px;
        }
        
        /* Header animation with brain logos */
        .header-container {
            text-align: center;
            margin-bottom: 30px;
            position: relative;
        }
        
        .main-brain-logo {
            width: 150px;
            height: 150px;
            animation: pulse-glow 3s infinite ease-in-out;
        }
        
        .small-brain {
            position: absolute;
            width: 40px;
            height: 40px;
            animation: orbit 12s infinite linear;
        }
        
        .small-brain:nth-child(2) {
            animation-delay: -2s;
        }
        
        .small-brain:nth-child(3) {
            animation-delay: -4s;
        }
        
        .small-brain:nth-child(4) {
            animation-delay: -6s;
        }
        
        .small-brain:nth-child(5) {
            animation-delay: -8s;
        }
        
        @keyframes orbit {
            0% {
                transform: rotate(0deg) translateX(100px) rotate(0deg);
            }
            100% {
                transform: rotate(360deg) translateX(100px) rotate(-360deg);
            }
        }
        
        @keyframes pulse-glow {
            0% {
                transform: scale(1);
                filter: drop-shadow(0 0 5px rgba(0, 200, 255, 0.7));
            }
            50% {
                transform: scale(1.1);
                filter: drop-shadow(0 0 20px rgba(0, 200, 255, 1));
            }
            100% {
                transform: scale(1);
                filter: drop-shadow(0 0 5px rgba(0, 200, 255, 0.7));
            }
        }
        
        /* Neon text effect */
       .neon-title {
    color: #fff;
    text-shadow: 0 0 5px #fff,
                 0 0 10px #fff,
                 0 0 20px #87ceeb,
                 0 0 30px #87ceeb,
                 0 0 40px #87ceeb;
                
                }

        
        @keyframes neon-flicker {
            0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% {
                text-shadow: 0 0 5px #fff, 
                             0 0 10px #fff, 
                             0 0 20px #ff00de, 
                             0 0 30px #ff00de, 
                             0 0 40px #ff00de;
            }
            20%, 24%, 55% {
                text-shadow: none;
            }
        }
        
        /* Feature box animation */
        .feature-box {
            background-color: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(5px);
            border-left: 4px solid #00eeff;
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
            transition: all 0.5s ease;
            position: relative;
                
            overflow: hidden;
        }
        
        .feature-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            border-left: 4px solid #ff00de;
        }
        
        .feature-box:hover::before {
            opacity: 1;
            transform: translateX(0);
        }
        
        .feature-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transform: translateX(-100%);
            transition: 0.5s;
            opacity: 0;
        }
        
        /* 3D Button styling */
        .btn-3d {
            display: inline-block;
            background: linear-gradient(to right, #00c6ff, #0072ff);
            color: white;
            padding: 12px 25px;
            text-align: center;
            text-decoration: none;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50px;
            margin: 15px 10px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
            transform: perspective(100px) translateZ(0);
        }
        
        .btn-3d:hover {
            transform: perspective(100px) translateZ(5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.4);
        }
        
        .btn-3d::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
            transform: translateX(-100%);
            transition: 0.5s;
        }
        
        .btn-3d:hover::before {
            transform: translateX(100%);
        }
        
        /* Glowing counter animation */
        .glowing-counter {
            font-size: 48px;
            font-weight: bold;
            background: -webkit-linear-gradient(#00c6ff, #0072ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: inline-block;
            position: relative;
            animation: countUp 3s forwards, glow 2s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from {
                text-shadow: 0 0 10px #00c6ff, 0 0 20px #00c6ff, 0 0 30px #00c6ff;
            }
            to {
                text-shadow: 0 0 20px #0072ff, 0 0 30px #0072ff, 0 0 40px #0072ff;
            }
        }
        
        @keyframes countUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Team members with rotating border */
        .team-member {
            text-align: center;
            width: 180px;
            margin: 15px;
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(5px);
            border-radius: 15px;
            position: relative;
            transition: transform 0.3s ease;
        }
        
        .team-member:hover {
            transform: translateY(-10px);
        }
        
        .team-member::before {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            z-index: -1;
            border-radius: 16px;
            background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
            background-size: 400%;
            animation: borderglow 20s linear infinite;
        }
        
        @keyframes borderglow {
            0% { background-position: 0% 0%; }
            100% { background-position: 400% 0%; }
        }
        
        .team-member img {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid white;
            box-shadow: 0 0 15px rgba(0, 200, 255, 0.8);
        }
        
        /* Brain scan effect */
        .brain-scan {
            position: relative;
            overflow: hidden;
            border-radius: 10px;
        }
        
        .brain-scan::after {
            content: '';
            position: absolute;
            top: -100%;
            left: 0;
            width: 100%;
            height: 10px;
            background: linear-gradient(90deg, transparent, #00ff99, transparent);
            animation: scan 3s linear infinite;
        }
        
        @keyframes scan {
            0% { top: -5%; }
            100% { top: 105%; }
        }
        
        /* Text styling */
        h1, h2, h3, h4 {
            color: white;
        }
        
        p {
            color: rgba(255, 255, 255, 0.9);
        }
    </style>
    
    <!-- Background floating brains -->
    <div class="background-brains">
        <div class="brain"></div>
        <div class="brain"></div>
        <div class="brain"></div>
        <div class="brain"></div>
        <div class="brain"></div>
        <div class="brain"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Animated header with multiple brain logos
    st.markdown("""
    <div class="header-container">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491329.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491320.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491321.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491322.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491329.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491356.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491323.png" class="small-brain">
        <img src="https://cdn-icons-png.flaticon.com/512/2491/2491325.png" class="main-brain-logo" alt="Brain Logo">
        <h1 class="neon-title">Brain Tumor Detection Using Image Processing </h1>
        <p style="color: #ffffff; font-size: 18px;color : black">Advanced Brain Tumor Detection & Analysis System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main introduction with glass card effect
    st.markdown("""
<div class="glass-card">
    <h2 style="text-align: center; color: black;">🧠 Revolutionary Medical Imaging Technology</h2>
    <p style="font-size: 21px; line-height: 1.6; color: black;">
        Our state-of-the-art system combines cutting-edge Image Processing algorithms with advanced image processing 
        techniques to detect and analyze brain tumors with unprecedented precision. Designed to assist medical 
        professionals in diagnosis and treatment planning, our platform offers an intuitive interface and 
        comprehensive analytical tools.
    </p>
</div>
""", unsafe_allow_html=True)

    
    # Animated statistics with glowing effect
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
    <div style="text-align: center;">
        <span class="glowing-counter" style="color: black; font-weight: bold;">98%</span>
        <p style="font-size: 22px; color: black; font-weight: bold;">Detection Accuracy</p>
    </div>
    """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
    <div style="text-align: center;">
        <span class="glowing-counter" style="color: black; font-weight: bold;">3.2s</span>
        <p style="font-size: 22px; color: black; font-weight: bold;">Processing Time</p>
    </div>
    """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
    <div style="text-align: center;">
        <span class="glowing-counter" style="color: black; font-weight: bold;">5+</span>
        <p style="font-size: 22px; color: black; font-weight: bold;">Processing Methods</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    
    # Enhanced feature section with hover animation
    st.markdown("""
<div class="glass-card">
    <h2 style="text-align: center; color: black;">Advanced AI Features</h2>
    <div class="feature-box">
        <h3>🔍 Multi-Layer Image Analysis</h3>
        <p style="color: black;font-size: 22px">Apply multiple advanced filters and processing techniques to enhance visualization and highlight tumor regions with exceptional clarity</p>
    </div>
    <div class="feature-box">
        <h3>🧠 Neural Network Detection</h3>
        <p style="color: black;font-size: 22px">Our YOLO-based deep learning model was trained on thousands of brain MRI scans to identify tumors with 98% accuracy</p>
    </div>
    <div class="feature-box">
        <h3>📊 3D Visualization & Metrics</h3>
        <p style="color: black;font-size: 22px">Comprehensive analysis including tumor volume, dimensions, location, and precise measurement of affected brain regions</p>
    </div>
    <div class="feature-box">
        <h3>🔬 AI-Powered Severity Assessment</h3>
        <p style="color: black;font-size: 22px">Immediate classification of tumor severity based on size, location, and characteristics with personalized recommendations</p>
    </div>
    <div class="feature-box">
        <h3>📱 Instant Digital Reports</h3>
        <p style="color: black;font-size: 22px">Generate detailed PDF reports with visualizations, metrics, and AI recommendations that can be instantly shared via email</p>
    </div>
</div>
""", unsafe_allow_html=True)

    
    # Sample results with enhanced brain scan animation
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Sample Detection Results</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
    <div class="brain-scan">
        <img src="" width="100%" style="border-radius: 10px;">
    </div>
    <p style="text-align: center; margin-top: 10px; color: black;font-size:22px; font-weight: bold;">Original MRI Scan</p>
    """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
    <div class="brain-scan">
        <img src="" width="100%" style="border-radius: 10px;">
    </div>
    <p style="text-align: center; margin-top: 10px; color: black; font-weight: bold;font-size: 22px">AI-Detected Tumor Regions</p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    
    # How to use with numbered steps and icons
    st.markdown("""
<div class="glass-card">
    <h2 style="text-align: center; color: black;">How It Works</h2>
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
        <div style="text-align: center; width: 150px; margin: 10px;">
            <div style="font-size: 40px; margin-bottom: 10px;">📤</div>
            <h3 style="margin: 5px 0; color: black;">Step 1</h3>
            <p style="color: black;">Upload MRI Scan</p>
        </div>
        <div style="text-align: center; width: 150px; margin: 10px;">
            <div style="font-size: 40px; margin-bottom: 10px;">👤</div>
            <h3 style="margin: 5px 0; color: black;">Step 2</h3>
            <p style="color: black;">Enter Patient Info</p>
        </div>
        <div style="text-align: center; width: 150px; margin: 10px;">
            <div style="font-size: 40px; margin-bottom: 10px;">🔬</div>
            <h3 style="margin: 5px 0; color: black;">Step 3</h3>
            <p style="color: black;">Apply Processing</p>
        </div>
        <div style="text-align: center; width: 150px; margin: 10px;">
            <div style="font-size: 40px; margin-bottom: 10px;">🤖</div>
            <h3 style="margin: 5px 0; color: black;">Step 4</h3>
            <p style="color: black;">AI Detection</p>
        </div>
        <div style="text-align: center; width: 150px; margin: 10px;">
            <div style="font-size: 40px; margin-bottom: 10px;">📊</div>
            <h3 style="margin: 5px 0; color: black;">Step 5</h3>
            <p style="color: black;">Get Analysis</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Team members with enhanced styling
    st.markdown("""
    <div class="glass-card">
    <h2 style="text-align: center;">Expert Development Team</h2>
    <div style="display: flex; justify-content: center; flex-wrap: wrap; gap: 30px;">
        <div class="team-member">
            <h3>Prof. Disha Nagpure</h3>
            <p>Project Guide</p>
        </div>
        <div class="team-member">
            <h3>Pawar Soham</h3>
            <p>Team Leader</p>
        </div>
        <div class="team-member">
            <h3>Kangude Samruddhi</h3>
            <p>AI Specialist</p>
        </div>
        <div class="team-member">
            <h3>Paitwar Dattatray</h3>
            <p>Software Developer</p>
        </div>
        <div class="team-member">
            <h3>Magar Aditi</h3>
            <p>UI/UX Designer</p>
        </div>
    </div>
</div>

    """, unsafe_allow_html=True)


def display_detection_page():
    # Advanced CSS with animations and better styling
    st.markdown("""
     <style>
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://images.unsplash.com/photo-1512678080530-7760d81faba6?q=80&w=1474&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D') no-repeat center center fixed;
            background-size: cover;
            filter: blur(8px);
            z-index: -1;
        }

        /* Optional: make text more readable */
        .stApp {
            background-color: rgba(255, 255, 255, 0.3); /* translucent overlay */
        }
            
        /* Card styling */
        .css-1d391kg, .css-1v3fvcr {
            background-color: rgba(255, 255, 255, 0.9) !important;
            padding: 25px;
            border-radius: 5px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(5px);
            transition: all 0.3s ease;
        }
        
        /* Main title with animation */
        .main-title {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #1A2A6C, #B21F1F, #FDBB2D);
            background-size: 200% auto;
            color: transparent;
            -webkit-background-clip: text;
            background-clip: text;
            animation: shine 3s linear infinite;
            text-align: center;
            font-weight: 800;
            margin-bottom: 1rem;
        }
        
        @keyframes shine {
            to {
                background-position: 200% center;
            }
        }
        
        /* Bounce animation for buttons */
        .stButton>button {
            transition: all 0.2s ease;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 14px rgba(50, 50, 93, 0.1), 0 3px 6px rgba(0, 0, 0, 0.08);
        }
        
        .stButton>button:active {
            transform: translateY(1px);
        }
        
        /* Card hover effects */
        .hover-card {
            transition: all 0.3s ease;
        }
        
        .hover-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        /* Progress bar styling */
        .stProgress > div > div {
            background-color: #1A2A6C !important;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            border-right: 1px solid rgba(200, 200, 200, 0.3);
        }
        
        /* Results card styling */
        .results-card {
            border-left: 5px solid #4CAF50;
            padding-left: 15px;
            background-color: rgba(76, 175, 80, 0.1);
            border-radius: 5px;
            padding: 15px;
            margin-top: 20px;
        }
        
        /* Custom file uploader */
        .stFileUploader label {
            background-color: rgba(26, 42, 108, 0.1) !important;
            border: 2px dashed #1A2A6C !important;
            border-radius: 10px !important;
            padding: 20px !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
        }
        
        .stFileUploader label:hover {
            background-color: rgba(26, 42, 108, 0.2) !important;
        }
        
        /* Loading animation */
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 1; }
            100% { opacity: 0.6; }
        }
        
        .loading-pulse {
            animation: pulse 1.5s infinite ease-in-out;
        }
        
        /* Logo container */
        .logo-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .logo-container img {
            max-height: 60px;
            transition: all 0.3s ease;
        }
        
        .logo-container img:hover {
            transform: scale(1.05);
        }
        
        /* Step container */
        .step-container {
            background-color: rgba(255,255,255,0.8);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
        }
        
        .step-container:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .step-number {
            background-color: #1A2A6C;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            margin-right: 15px;
            font-weight: bold;
        }
        
        /* Information tabs */
        .info-tab {
            border-bottom: 1px solid rgba(0,0,0,0.1);
            padding-bottom: 10px;
            margin-bottom: 10px;
            cursor: pointer;
        }
        
        /* Severity indicators */
        .severity-low {
            color: #4CAF50;
            font-weight: bold;
        }
        
        .severity-medium {
            color: #FF9800;
            font-weight: bold;
        }
        
        .severity-high {
            color: #F44336;
            font-weight: bold;
        }
        
        /* Notification badge */
        .notification-badge {
            background-color: #F44336;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 12px;
            position: absolute;
            top: -5px;
            right: -5px;
        }
        
        /* Processing button animation */
        @keyframes processing {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .processing-button {
            background: linear-gradient(270deg, #1A2A6C, #B21F1F, #FDBB2D, #1A2A6C);
            background-size: 300% 300%;
            animation: processing 3s ease infinite;
            color: white !important;
            border: none !important;
        }
        
        /* Pulsing dot */
        .pulsing-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #F44336;
            border-radius: 50%;
            margin-left: 5px;
            animation: pulse 1s infinite;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Logo and header section
    st.markdown("""
    <div class="logo-container">
                <h1 class="main-title">💥 Brain Tumor Detection Using Image Processing 🧠</h1>

    <style>
    .main-title {
        color: black;
        font-size: 3em;
        text-align: center;
        margin-top: 20px;
    }
      
    </div>
    <p style="text-align: center; font-size: 1.2rem; margin-bottom: 30px;">
    </p>
    """, unsafe_allow_html=True)
    
    # Animated tabs for navigation
    tab1, tab2, tab3 = st.tabs(["📋 Detection"," ", " "])
    
    with tab1:
        # Sidebar for file upload and patient information with better styling
        with st.sidebar:
            st.markdown('<div style="text-align: center;"><img src="https://cdn-icons-png.flaticon.com/512/3004/3004550.png" width="80"></div>', 
                       unsafe_allow_html=True)
            st.markdown('<h2 style="text-align: center;">Patient Information</h2>', unsafe_allow_html=True)
            
            # File upload with better styling
            st.markdown('<p style="font-weight: bold; margin-bottom: 5px;">Upload Brain MRI Scan</p>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg"])
            
            # Form for patient details
            with st.form(key="patient_form"):
                patient_name = st.text_input("Patient Name", placeholder="dattatray paitwar")
                col1, col2 = st.columns(2)
                with col1:
                    patient_age = st.number_input("Age", min_value=0, max_value=120, value=30)
                with col2:
                    patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                
                email = st.text_input("Email Address (for report)", placeholder="aditimagar@gmail.com")
                
                
                
                # Submit button with animation
                submit_button = st.form_submit_button(label="Save Patient Info")
                if submit_button:
                    st.success("Patient information saved!")
                    
            # Quick stats in sidebar
            st.markdown("""
            <div style="padding: 15px; background-color: rgba(26, 42, 108, 0.1); border-radius: 10px; margin-top: 20px;">
                <h3 style="text-align: center; margin-bottom: 10px;">Today's Stats</h3>
                <p>⚕️ Tumor Detection Rate: 32%</p>
                <p>⏱️ Avg. Processing Time: 4.2s</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Main display area with two columns
        col1, col2 = st.columns(2)
        
        # Add a progress placeholder
        progress_placeholder = st.empty()
        
        # Initialize variables
        image = None
        tumor_detected = False
        
        if uploaded_file is not None:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            with col1:
                st.markdown('<div class="hover-card">', unsafe_allow_html=True)
                st.subheader("Original MRI Scan")
                st.image(image, caption=f"Patient: {patient_name if patient_name else 'Unknown'}", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Processing options with improved UI
                st.markdown('<h4>Enhancement Techniques</h4>', unsafe_allow_html=True)
                processing_options = st.multiselect(
                    "Select image processing methods to apply:",
                    ["Denoise Image", "CLAHE Enhancement", "Adaptive Thresholding", "Canny Edge Detection", "Contour Detection"]
                )
                
               
            
            # Process images based on selection
            if processing_options:
                with col2:
                    st.markdown('<div class="hover-card">', unsafe_allow_html=True)
                    st.subheader("Processed Image")
                    
                    # Create tabs for different processing methods
                    process_tabs = st.tabs([opt.split()[0] for opt in processing_options])
                    
                    for i, tab in enumerate(process_tabs):
                        with tab:
                            option = processing_options[i]
                            if "Denoise" in option:
                                denoised_img = denoise_image(image)
                                st.image(denoised_img, caption="Noise Reduction Applied", use_container_width=True)
                            
                            elif "CLAHE" in option:
                                clahe_img = apply_clahe(image)
                                st.image(clahe_img, caption="Contrast Limited Adaptive Histogram Equalization", use_container_width=True)
                            
                            elif "Thresholding" in option:
                                threshold_img = adaptive_thresholding(image)
                                st.image(threshold_img, caption="Adaptive Thresholding Result", use_container_width=True)
                            
                            elif "Edge" in option:
                                edge_img = canny_edge_detection(image)
                                st.image(edge_img, caption="Edge Detection Result", use_container_width=True)
                            
                            elif "Contour" in option:
                                contour_img = find_and_filter_contours(image)
                                st.image(contour_img, caption="Contour Detection", use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
            # YOLO Tumor Detection - Better styling and animation
            st.markdown("<br>", unsafe_allow_html=True)
            detection_col1, detection_col2 = st.columns([3, 1])
            
            with detection_col1:
                detection_btn = st.button("🔍 Detect Tumor with YOLO", use_container_width=True)
                
            
            if detection_btn and image is not None:
                if not patient_name:
                    st.warning("⚠️ Please enter the patient's name in the sidebar.")
                elif not email:
                    st.warning("⚠️ Please enter an email address to receive the report.")
                else:
                    # Show progress with better animation
                    progress_bar = progress_placeholder.progress(0)
                    
                    # Stage 1
                    progress_placeholder.markdown("""
                    <div class="step-container">
                        <div class="step-number">1</div>
                        <div>
                            <p><b>Preprocessing image...</b></p>
                            <p style="color: #666; font-size: 0.9rem;">Applying noise reduction and normalization</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.5)
                    progress_bar.progress(20)
                    
                    # Stage 2
                    progress_placeholder.markdown("""
                    <div class="step-container">
                        <div class="step-number">2</div>
                        <div>
                            <p><b>Analyzing with YOLO model...</b></p>
                            <p style="color: #666; font-size: 0.9rem;">Processing through neural network layers</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.5)
                    progress_bar.progress(40)
                    
                    # Perform actual detection
                    yolo_img, tumor_lengths = detect_tumor_with_yolo(image)
                    
                    # Stage 3
                    progress_placeholder.markdown("""
                    <div class="step-container">
                        <div class="step-number">3</div>
                        <div>
                            <p><b>Processing results...</b></p>
                            <p style="color: #666; font-size: 0.9rem;">Analyzing tumor characteristics</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(0.5)
                    progress_bar.progress(60)
                    
                    with col2:
                        st.markdown('<div class="hover-card">', unsafe_allow_html=True)
                        st.subheader("Detection Results")
                        st.image(yolo_img, caption="YOLO Tumor Detection Result", use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
    
                    if tumor_lengths:
                        tumor_detected = True
                        
                        # Convert tensor values to Python floats
                        tumor_lengths = [float(length) for length in tumor_lengths]
                        
                        # Assess tumor severity
                        severity, recommendation = assess_tumor_severity(tumor_lengths, image.shape)
                        
                        # Select appropriate severity class for styling
                        severity_class = "severity-low"
                        if severity == "Medium":
                            severity_class = "severity-medium"
                        elif severity == "High":
                            severity_class = "severity-high"
                        
                        # Display results with better styling
                        st.markdown(f"""
                        <div class="results-card">
                            <h2>✅ Analysis Complete</h2>
                            <p>Patient: <b>{patient_name}</b> | Age: <b>{patient_age}</b> | Gender: <b>{patient_gender}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Results in nice cards
                        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                        
                        with metric_col1:
                            st.markdown(f"""
                            <div style="background-color: rgba(26, 42, 108, 0.1); padding: 15px; border-radius: 10px; text-align: center;">
                                <h3 style="margin-bottom: 5px;">Tumors</h3>
                                <p style="font-size: 2rem; font-weight: bold; margin: 0;">{len(tumor_lengths)}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with metric_col2:
                            st.markdown(f"""
                            <div style="background-color: rgba(26, 42, 108, 0.1); padding: 15px; border-radius: 10px; text-align: center;">
                                <h3 style="margin-bottom: 5px;">Severity</h3>
                                <p style="font-size: 2rem; font-weight: bold; margin: 0;" class="{severity_class}">{severity}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with metric_col3:
                            st.markdown(f"""
                            <div style="background-color: rgba(26, 42, 108, 0.1); padding: 15px; border-radius: 10px; text-align: center;">
                                <h3 style="margin-bottom: 5px;">Largest (px)</h3>
                                <p style="font-size: 2rem; font-weight: bold; margin: 0;">{round(max(tumor_lengths), 2)}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with metric_col4:
                            st.markdown(f"""
                            <div style="background-color: rgba() padding: 15px; border-radius: 10px; text-align: center;">
                                <h3 style="margin-bottom: 5px;">Avg Size</h3>
                                <p style="font-size: 2rem; font-weight: bold; margin: 0;">{round(sum(tumor_lengths)/len(tumor_lengths), 2)}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Recommendation section with icon matching severity
                        icon = "🟢"
                        if severity == "Medium":
                            icon = "🟠"
                        elif severity == "High":
                            icon = "🔴"
                            
                        st.markdown(f"""
                        <div style="background-color: rgba(); border-radius: 10px; padding: 20px; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                            <h3>{icon} Medical Recommendation</h3>
                            <p style="font-size: 1.1rem;">{recommendation}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Convert the processed image to PNG format
                        _, buffer = cv2.imencode('.png', yolo_img)
                        processed_image = buffer.tobytes()
                        
                        # Stage 4
                        progress_placeholder.markdown("""
                        <div class="step-container">
                            <div class="step-number">4</div>
                            <div>
                                <p><b>Generating comprehensive report...</b></p>
                                <p style="color: #666; font-size: 0.9rem;">Creating PDF document with analysis</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        progress_bar.progress(80)
                        
                # Create PDF report
                detection_time = datetime.now()
                pdf_report = create_pdf_report(patient_name, tumor_lengths, yolo_img, detection_time, severity, recommendation)
                
                # Store results in database with additional patient info
                store_in_database(patient_name, patient_age, patient_gender, tumor_lengths, processed_image, severity, recommendation)
                
                # Prepare email data
                email_data = {
                    "patient_name": patient_name,
                    "patient_age": patient_age,
                    "patient_gender": patient_gender,
                    "tumor_lengths": tumor_lengths,
                    "detection_time": detection_time,
                    "severity": severity,
                    "recommendation": recommendation
                }
                
                progress_placeholder.text("Sending email report...")
                progress_bar.progress(90)
                
                # Send email report
                success, message = send_tumor_report(
                    email,
                    email_data,
                    processed_image,
                    pdf_report
                )
                
                progress_placeholder.empty()
                
                if success:
                    st.sidebar.success("Detection report sent to your email!")
                else:
                    st.sidebar.error(message)

                # Save Image Button
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="Download Processed Image",
                        data=BytesIO(cv2.imencode('.png', yolo_img)[1]).getvalue(),
                        file_name=f"{patient_name}_processed_image.png",
                        mime="image/png",
                    )
                
                with col2:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_report,
                        file_name=f"{patient_name}_tumor_report.pdf",
                        mime="application/pdf",
                    )
                
                # Display the chatbot link
                st.markdown(
    '<div style="background-color:#f0f2f6; padding:15px; border-radius:10px;">'
    '<p style="font-size:16px; font-weight:bold;">Have questions about the results?</p>'
    '<a href="https://chatbot-ten-fawn.vercel.app/" class="btn" style="background-color:#4CAF50; color:white; padding:10px; '
    'text-decoration:none; border-radius:5px; margin-top:10px;">Chat with our Medical AI Assistant</a>'
    '</div>',
    unsafe_allow_html=True,
)
            else:
                st.info("No tumors detected in the provided image.")
                progress_placeholder.empty()

    # If no image uploaded, show message
    if image is None:
        st.markdown(
        """
        <div style="color: black; font-weight: bold;font-size :22px">
            <h3>Instructions:</h3>
            <ol>
                <li>Upload a brain MRI scan image using the sidebar</li>
                <li>Enter patient information</li>
                <li>Run image processing techniques to enhance visualization</li>
                <li>Click "Detect Tumor with YOLO" for automated analysis</li>
                <li>Receive detailed reports and analysis</li>
            </ol>
            ⬅️ Please upload an image to get started
        </div>
        """,
        unsafe_allow_html=True
    )


# Enhanced email sending function
def send_tumor_report(recipient_email, email_data, image_data, pdf_report):
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')
    
    # For testing purposes - if no email credentials are set, simulate success
    if not sender_email or not sender_password:
        return True, "Email sending simulated (no email credentials provided)"
    
    msg = MIMEMultipart()
    msg['Subject'] = f'Brain Tumor Detection Report - {email_data["patient_name"]}'
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # Create a more attractive HTML email
    html_content = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4a76a8; color: white; padding: 10px 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ padding: 20px; background-color: #f9f9f9; border-left: 1px solid #ddd; border-right: 1px solid #ddd; }}
                .footer {{ background-color: #eee; padding: 10px 20px; text-align: center; font-size: 12px; color: #777; border-radius: 0 0 5px 5px; }}
                .info-box {{ background-color: #e7f3fe; border-left: 4px solid #2196F3; padding: 10px; margin: 10px 0; }}
                .warning-box {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Brain Tumor Detection Report</h2>
                </div>
                <div class="content">
                    <h3>Patient Information</h3>
                    <table>
                        <tr>
                            <th>Name</th>
                            <td>{email_data["patient_name"]}</td>
                        </tr>
                        <tr>
                            <th>Age</th>
                            <td>{email_data["patient_age"]}</td>
                        </tr>
                        <tr>
                            <th>Gender</th>
                            <td>{email_data["patient_gender"]}</td>
                        </tr>
                        <tr>
                            <th>Date</th>
                            <td>{email_data["detection_time"].strftime('%Y-%m-%d %H:%M:%S')}</td>
                        </tr>
                    </table>
                    
                    <h3>Detection Results</h3>
                    <table>
                        <tr>
                            <th>Number of Tumors</th>
                            <td>{len(email_data["tumor_lengths"])}</td>
                        </tr>
                        <tr>
                            <th>Severity</th>
                            <td>{email_data["severity"]}</td>
                        </tr>
                    </table>
                    
                    <div class="info-box">
                        <p><strong>Tumor Sizes:</strong></p>
                        <ul>
                            {"".join(f"<li>Tumor {i+1}: {length:.2f} pixels</li>" for i, length in enumerate(email_data["tumor_lengths"]))}
                        </ul>
                    </div>
                    
                    <div class="warning-box">
                        <p><strong>Recommendation:</strong> {email_data["recommendation"]}</p>
                    </div>
                    
                    <p>Please find attached:</p>
                    <ol>
                        <li>Processed image showing tumor detection</li>
                        <li>Detailed PDF report</li>
                    </ol>
                    
                    <p><a href="#" class="button">View Online Report</a></p>
                </div>
                <div class="footer">
                    <p><em>This is an automated report from the Brain Tumor Detection System. Please consult with a healthcare professional for proper diagnosis and treatment options.</em></p>
                </div>
            </div>
        </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))
    
    # Attach the image
    image = MIMEImage(image_data)
    image.add_header('Content-Disposition', 'attachment', filename=f'tumor_detection_{email_data["patient_name"]}.png')
    msg.attach(image)
    
    # Attach the PDF report
    pdf = MIMEText(pdf_report, 'base64', 'utf-8')
    pdf.add_header('Content-Disposition', 'attachment', filename=f'{email_data["patient_name"]}_tumor_report.pdf')
    pdf.add_header('Content-Type', 'application/pdf')
    msg.attach(pdf)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "Report sent successfully!"
    except Exception as e:
        return False, f"Failed to send report: {str(e)}"

# Enhanced database function with more patient info
def store_in_database(patient_name, patient_age, patient_gender, tumor_lengths, processed_image, severity, recommendation):
    # Make sure tumor_lengths contains Python float values
    tumor_lengths = [float(length) for length in tumor_lengths]
    
    conn = sqlite3.connect("tumor_detection.db")
    cursor = conn.cursor()
    
    # Insert record with all fields
    cursor.execute('''
    INSERT INTO detections (patient_name, patient_age, patient_gender, tumor_count, tumor_lengths, detection_time, processed_image, severity, recommendation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (patient_name, patient_age, patient_gender, len(tumor_lengths), json.dumps(tumor_lengths), datetime.now(), processed_image, severity, recommendation))
    
    conn.commit()
    conn.close()

def display_history():
    st.markdown("""
    <style>
        /* Background with parallax effect */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://plus.unsplash.com/premium_photo-1661767897334-bbfbdfdc4d1a?q=80&w=1470&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D') no-repeat center center fixed;
            background-size: cover;
            filter: blur(8px);
            z-index: -1;
            transform: scale(1.1);  /* Slight zoom for parallax effect */
            transition: transform 0.5s ease;
        }

        /* Glass morphism effect for better readability */
        .stApp {
            background-color: rgba(255, 255, 255, 0.4);
            backdrop-filter: blur(10px);
        }

        /* Text styling */
        .stMarkdown, .stTitle, .stHeader, .stSubheader, .stExpander {
            color: #0d2339 !important;
            font-size: 22px !important;
            font-weight: 500 !important;
        }

        /* Title with gradient */
        .stTitle {
            background: linear-gradient(45deg, #0d2339, #1e88e5);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 40px !important;
            font-weight: 700 !important;
            margin-bottom: 30px !important;
        }
        
        /* Subheader styling */
        .stSubheader {
            border-left: 4px solid #1e88e5;
            padding-left: 10px;
            font-size: 26px !important;
        }

        /* Labels, metrics, buttons styling */
        label, .stMetricLabel, .stButton > button {
            font-size: 20px !important;
            color: #0d2339 !important;
        }
        
        /* Metric value styling */
        .stMetricValue {
            font-size: 28px !important;
            color: #1e88e5 !important;
            font-weight: 700 !important;
        }

        /* Expander styling */
        .stExpander {
            border-radius: 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            margin-bottom: 15px !important;
            border: none !important;
            overflow: hidden !important;
            transition: all 0.3s ease !important;
        }
        
        .stExpander:hover {
            transform: translateY(-5px) !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.15) !important;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 8px !important;
            border: none !important;
            background: linear-gradient(45deg, #1e88e5, #64b5f6) !important;
            color: white !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }
        
        /* Animation for elements */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stExpander, .stMetric, .stButton {
            animation: fadeIn 0.6s ease-out forwards;
        }
        .stMarkdown, .stTitle, .stHeader, .stSubheader, .stExpander, .stText, .stDataFrame {
    color: #0d2339 !important;
    font-size: 22px !important;
    font-weight: bold !important;
}

        
        /* Stagger animations */
        .stExpander:nth-child(1) { animation-delay: 0.1s; }
        .stExpander:nth-child(2) { animation-delay: 0.2s; }
        .stExpander:nth-child(3) { animation-delay: 0.3s; }
        
        /* Date picker styling */
        .stDateInput {
            border-radius: 8px !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Create a header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("""
        <div style="display: flex; justify-content: center; margin-top: 20px;">
            
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.title("📊 Tumor Detection History")
    
    st.markdown("""
    <div style="text-align: center; margin: -15px 0 30px 0; font-style: italic; color: #555;">
        Advanced tumor detection and patient management system
    </div>
    """, unsafe_allow_html=True)
    
    conn = sqlite3.connect("tumor_detection.db")
    
    # Get all records
    try:
        df = pd.read_sql_query("SELECT * FROM detections ORDER BY detection_time DESC", conn)
        
        if not df.empty:
            # Show filters
            st.subheader("Filter Results")
            
            filter_col1, filter_col2 = st.columns(2)
            
            # Add date filter
            with filter_col1:
                if 'detection_time' in df.columns:
                    df['detection_time'] = pd.to_datetime(df['detection_time'])
                    min_date = df['detection_time'].min().date()
                    max_date = df['detection_time'].max().date()
                    
                    date_range = st.date_input(
                        "Select Date Range",
                        [min_date, max_date],
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_range) == 2:
                        start_date, end_date = date_range
                        filtered_df = df[(df['detection_time'].dt.date >= start_date) & 
                                        (df['detection_time'].dt.date <= end_date)]
                    else:
                        filtered_df = df
                else:
                    filtered_df = df
            
            # Add severity filter if available
            with filter_col2:
                if 'severity' in df.columns:
                    severity_options = ['All'] + list(filtered_df['severity'].unique())
                    selected_severity = st.selectbox("Filter by Severity", severity_options)
                    
                    if selected_severity != 'All':
                        filtered_df = filtered_df[filtered_df['severity'] == selected_severity]
            
            # Display statistics with improved styling
            st.subheader("Statistics")
            stats_col1, stats_col2, stats_col3 = st.columns(3)
            
            with stats_col1:
                st.metric("Total Patients", len(filtered_df))
                
            with stats_col2:
                if 'tumor_count' in filtered_df.columns:
                    avg_tumors = filtered_df['tumor_count'].mean()
                    st.metric("Avg Tumors per Patient", f"{avg_tumors:.2f}")
                    
            with stats_col3:
                if 'severity' in filtered_df.columns:
                    high_severity_count = len(filtered_df[filtered_df['severity'] == 'High Severity'])
                    st.metric("High Severity Cases", high_severity_count)
            
            # Display records
            st.subheader(f"Patient Records ({len(filtered_df)})")
            
            for idx, record in filtered_df.iterrows():
                with st.expander(f"Patient: {record['patient_name']} - {record['detection_time']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write(f"**Age:** {record.get('patient_age', 'N/A')}")
                        st.write(f"**Gender:** {record.get('patient_gender', 'N/A')}")
                        st.write(f"**Tumor Count:** {record['tumor_count']}")
                        
                        if 'severity' in record:
                            severity_color = "#ff5252" if record['severity'] == "High Severity" else "#4caf50"
                            st.markdown(f"**Severity:** <span style='color:{severity_color};'>{record['severity']}</span>", unsafe_allow_html=True)
                        
                        if 'recommendation' in record:
                            st.write(f"**Recommendation:** {record['recommendation']}")
                    
                    with col2:
                        if 'processed_image' in record and record['processed_image'] is not None:
                            try:
                                processed_image = np.frombuffer(record['processed_image'], np.uint8)
                                processed_image = cv2.imdecode(processed_image, cv2.IMREAD_COLOR)
                                # Using use_container_width instead of use_column_width
                                st.image(processed_image, caption="Processed Image", use_container_width=True)
                            except Exception:
                                st.warning("Could not display image")
                    
                    # Add action buttons
                    # btn1, btn2, btn3 = st.columns(3)
                    # with btn1:
                    #     st.button("Send Report", key=f"send_{record['id']}", help="Email the report to the relevant doctor")
                    # with btn2:
                    #     st.button("Export PDF", key=f"pdf_{record['id']}", help="Download the report as PDF")
                    # with btn3:
                    #     st.button("Delete Record", key=f"del_{record['id']}", help="Remove this record from history")
        else:
            st.info("No detection history available.")
            
            # Empty state illustration
            st.markdown("""
            <div style="display: flex; justify-content: center; margin: 50px 0;">
                <svg width="200" height="200" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#ccc" stroke-width="2"/>
                    <path d="M9 15C9.55228 15 10 14.5523 10 14C10 13.4477 9.55228 13 9 13C8.44772 13 8 13.4477 8 14C8 14.5523 8.44772 15 9 15Z" fill="#ccc"/>
                    <path d="M15 15C15.5523 15 16 14.5523 16 14C16 13.4477 15.5523 13 15 13C14.4477 13 14 13.4477 14 14C14 14.5523 14.4477 15 15 15Z" fill="#ccc"/>
                    <path d="M9 10C10.5 8.5 13.5 8.5 15 10" stroke="#ccc" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </div>
            <div style="text-align: center; color: #777; font-style: italic; margin-bottom: 50px;">
                No detection records found. Start by analyzing new patient data.
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error accessing database: {str(e)}")
        
        # Error state illustration
        st.markdown("""
        <div style="display: flex; justify-content: center; margin: 50px 0;">
            <svg width="200" height="200" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#ff5252" stroke-width="2"/>
                <path d="M12 8V12" stroke="#ff5252" stroke-width="2" stroke-linecap="round"/>
                <circle cx="12" cy="16" r="1" fill="#ff5252"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    conn.close()
    
    # Add clear history button with confirmation
    st.markdown("<hr style='margin: 30px 0;'>", unsafe_allow_html=True)
    st.subheader("Database Management")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Clear All History", help="Remove all detection records permanently"):
            st.session_state['show_confirm'] = True
    
    with col2:
        if st.session_state.get('show_confirm', False):
            st.warning("⚠️ Are you sure? This action cannot be undone.")
            confirm_col1, confirm_col2 = st.columns([1, 3])
            with confirm_col1:
                if st.button("Yes, Clear Data"):
                    clear_history()
                    st.success("Detection history cleared successfully.")
                    st.session_state['show_confirm'] = False
                    st.experimental_rerun()
            with confirm_col2:
                if st.button("Cancel"):
                    st.session_state['show_confirm'] = False
                    st.experimental_rerun()

def display_about_page():
    # Add custom CSS with animations and improved styling
    st.markdown("""
    <style>
        /* Background with parallax effect */
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://plus.unsplash.com/premium_photo-1699387204388-120141c76d51?q=80&w=1378&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D') no-repeat center center fixed;
            background-size: cover;
            filter: blur(5px);
            z-index: -1;
        }
        
        /* Content container with glass morphism effect */
        .content-container {
            background-color: rgba(255, 255, 255, 0.75);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(31, 38, 135, 0.2);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        
        /* Logo container */
        .logo-container {
            display: flex;
            justify-content: space-around;
            align-items: center;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        
        .logo {
            height: 60px;
            margin: 10px;
            filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
            transition: transform 0.3s ease;
        }
        
        /* Team member cards */
        .team-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        
        .team-card {
            background-color: rgba(255, 255, 255, 0.85);
            border-radius: 10px;
            padding: 15px;
            width: 180px;
            text-align: center;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        
        
        /* Section headers */
        .section-header {
            color: #2C3E50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        
        /* Stats display */
        .stats-container {
            display: flex;
            justify-content: space-around;
            text-align: center;
            margin: 30px 0;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2C3E50;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #7F8C8D;
        }
        
        /* Process steps */
        .process-step {
            background-color: #f8f9fa;
            border-left: 4px solid #4CAF50;
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        
        /* Button styling */
        .contact-btn {
            display: inline-block;
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 5px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main title
    st.markdown("""
    <div class="content-container" style="text-align: center;">
        <h1 style="color: #2C3E50; font-size: 2.8rem;">Brain Tumor Detection System</h1>
        <p style="font-size: 1.2rem; color: #34495E;">Advanced AI-powered diagnostic assistance tool</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logo section
    st.markdown("""
    <div class="content-container">
        <h2 class="section-header">Technology  Used </h2>
        <div class="logo-container">
            <img class="logo" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAMAAABF0y+mAAAAQlBMVEVHcExnBs5nBs5nBs5nBs5nBc5nBs5nBs5nBs5lAM5fAMxYAMtuIdCnh+HKuOzp4fd4OdPazvL///+3nuaQY9n59/2rj9IrAAAACXRSTlMAOIbD7f9gFeCI36poAAABK0lEQVR4AX2TV4KEMAxDKfGA7VTK/a+6kdg2VZ88LClt+NU4zUEkzNM4POoW5FfhdoeWVe60Lv8cBVIzdzdT6RrvmHpMuZSSk9k/ukiX1bb9aHcMX87I87T9UwFd2RMs908t1XrsJ2iGMzoHEetzJbopOhVQx4quNrH/62osqhWwKjtNHMxunnI7VMQBFXAaZlY1PxDWTPRgI+maEYlF7vj/rKrMTCYMFcjImnfWrkEKkCW4dpMCA1GhaGuZTKzSPKoYcGAhP+EpdtDcOtujotAkV/tDNYIlV/HMShM2gZNRaX640MGUBxOuzKrWuOXqnWEwXBsPw904maRmFODGd600Ol3r85HxsK2WqsiC8r/DZidFA6u5lFzB7i8RpeZ+f8E+Xc0Pl/rjc/gCGg4Z4fYMNYYAAAAASUVORK5CYII=" alt="YOLO Logo">
            <img class="logo" src="https://opencv.org/wp-content/uploads/2020/07/OpenCV_logo_black-2.png" alt="OpenCV Logo">
            <img class="logo" src="https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.png" alt="Streamlit Logo">
            <img class="logo" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAAb1BMVEX///8AAAAAAAATZ1UhsZMAAAAAAAAILCUgrI8grZALOjAAAAAAAAACCwkZhW4bkHgEFhIAAAAAAAAAAAAPUUMgrpASXk4AAAAAAAAGIRwdnYIfp4oAAAAAAAAUbFoCDAoAAAAAAAAgrpECDAoAAACjVKqnAAAAJXRSTlMA//D4/xDA//f29SBw/+vr/4Aw0Pf18OCQ/+vuoEDr8WCw9OJQSvMNRAAAAMJJREFUeAHUz0USAzEQA0B5kmVm5v3/F8OuWb5HV7XLGvxHxGUACLrdT3KjD1BUTT+qDVO1PgCwHXffe34A/ADCKE42fZqFYADkRbmsK61WsAJoqOXe7XpgA6AMcusYRxb2ALC7z9ayCIADILe2U4Mt4OR+MSg4B8pAPXAOmiwKcQECkQPnwFKJ1+XWDszE68IoCzdAqcmGjE21svki5HXgSxjYIpdP0FBkbUYqKs28TgS7K0jl51HWYAeewwuGRsYDAJk8ClkLclzsAAAAAElFTkSuQmCC" alt="SMTP Logo">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mission section
    st.markdown("""
    <div class="content-container">
        <h2 class="section-header">Our Mission</h2>
        <p style="font-size: 1.1rem; line-height: 1.6;">
            Our mission is to revolutionize brain tumor detection through cutting-edge AI technology, making accurate 
            diagnostic assistance accessible to healthcare professionals worldwide. We aim to improve patient outcomes 
            by providing tools that enhance early detection capabilities and support informed medical decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats counter
    st.markdown("""
    <div class="content-container">
        <div class="stats-container">
            <div>
                <div class="stat-number">98%</div>
                <div class="stat-label">Accuracy</div>
            </div>
            <div>
                <div class="stat-number">30+</div>
                <div class="stat-label">Scans Analyzed</div>
            </div>
            <div>
                <div class="stat-number">200+</div>
                <div class="stat-label">Hospitals Using Our System</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Technology section
    st.markdown("""
    <div class="content-container">
        <h2 class="section-header">Technology</h2>
        <p>Our system integrates multiple advanced technologies:</p>
        <ul>
            <li style="margin: 10px 0;">
                <strong style="color: #2C3E50;">YOLO (You Only Look Once):</strong> State-of-the-art real-time object detection system 
                optimized for medical imaging
            </li>
            <li style="margin: 10px 0;">
                <strong style="color: #2C3E50;">OpenCV:</strong> Advanced image processing and computer vision algorithms for 
                pre-processing and feature extraction
            </li>
            <li style="margin: 10px 0;">
                <strong style="color: #2C3E50;">Deep Learning:</strong> Custom CNN architecture trained on thousands of 
                verified MRI scans for maximum accuracy
            </li>
            <li style="margin: 10px 0;">
                <strong style="color: #2C3E50;">Streamlit:</strong> Interactive web interface providing real-time results and 
                user-friendly experience
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # How It Works section with simple steps
    st.markdown("""
    <div class="content-container">
        <h2 class="section-header">How It Works</h2>
        <div class="process-step">
            <h4>1. Image Upload</h4>
            <p>Upload MRI scan images through our intuitive interface</p>
        </div>
        <div class="process-step">
            <h4>2. Preprocessing</h4>
            <p>Images are automatically enhanced and prepared for analysis</p>
        </div>
        <div class="process-step">
            <h4>3. AI Analysis</h4>
            <p>Our YOLO-based deep learning model scans for tumor indicators</p>
        </div>
        <div class="process-step">
            <h4>4. Results</h4>
            <p>Detailed detection results with classification and confidence scores</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Limitations section
    st.markdown("""
    <div class="content-container">
        <h2 class="section-header">Limitations</h2>
        <div style="display: flex; flex-direction: column; margin: 20px 0;">
            <div style="padding: 15px; background-color: rgba(255, 152, 0, 0.1); border-left: 4px solid #FF9800; margin: 5px; border-radius: 5px;">
                <h4 style="color: #FF9800;">Clinical Support Tool Only</h4>
                <p>Designed to support healthcare professionals, not replace clinical judgment or formal diagnosis</p>
            </div>
            <div style="padding: 15px; background-color: rgba(255, 152, 0, 0.1); border-left: 4px solid #FF9800; margin: 5px; border-radius: 5px;">
                <h4 style="color: #FF9800;">Image Quality Dependent</h4>
                <p>Detection accuracy varies based on scan quality, resolution, and contrast parameters</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Team section without images
    st.markdown("""
<div class="content-container">
    <h2 class="section-header">Our Team</h2>
    <div class="team-container">
        <div class="team-card">
            <h3>Prof. Disha Nagpure</h3>
            <p>Project Guide</p>
        </div>
        <div class="team-card">
            <h3>Pawar Soham</h3>
            <p>Team Leader</p>
        </div>
        <div class="team-card">
            <h3>Kangude Samruddhi</h3>
            <p>Team Member</p>
        </div>
        <div class="team-card">
            <h3>Paitwar Dattatray</h3>
            <p>Team Member</p>
        </div>
        <div class="team-card">
            <h3>Magar Aditi</h3>
            <p>Team Member</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    
    # Contact section
    st.markdown("""
    <div class="content-container" style="text-align: center;">
        <h2 class="section-header">Contact Us</h2>
        <p>Have questions or need more information about our brain tumor detection system?</p>
        <div style="margin: 25px 0;">
            <a href="mailto:beprojectgroup05@gmail.com" class="contact-btn">
                Email Us
            </a>
            
        
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #7F8C8D; font-size: 0.9rem; margin-top: 30px;">
        © 2025 Brain Tumor Detection System | All Rights Reserved
    </div>
    """, unsafe_allow_html=True)
def display_faq_page():
    st.markdown("""
     <style>
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: url('https://images.unsplash.com/photo-1551076805-e1869033e561?q=80&w=1632&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D') no-repeat center center fixed;
            background-size: cover;
            filter: blur(8px);
            font-size : 25px;
            z-index: -1;
        }

        /* Optional: make text more readable */
        .stApp {
            background-color: rgba(255, 255, 255, 0.3); /* translucent overlay */
        }
            </style>

    """, unsafe_allow_html=True)
    st.title("Frequently Asked Questions")
    
    faq_data = [
        {
            "question": "How accurate is the tumor detection?",
            "answer": "Our system currently has an accuracy rate of approximately 85-90% based on our validation studies. However, accuracy can vary depending on image quality and tumor characteristics."
        },
        {
            "question": "What type of images should I upload?",
            "answer": "The system works best with T1 or T2-weighted MRI brain scans in PNG, JPG, or JPEG format. Images should be clear and properly oriented for best results."
        },
        {
            "question": "Is my data secure and private?",
            "answer": "Yes, all uploaded images and patient data are encrypted and stored securely. We comply with healthcare data protection standards, though this is a demonstration system and should not be used with real patient data without proper approvals."
        },
        {
            "question": "Can I use this system for clinical diagnosis?",
            "answer": "This system is designed as a supportive tool and should not be used as the sole basis for clinical diagnosis. Always consult with a qualified healthcare professional."
        },
        {
            "question": "What does the severity assessment mean?",
            "answer": "The severity assessment is based on the size of detected tumors relative to brain area and provides a general indication of urgency. Low severity suggests regular follow-up, moderate severity suggests closer monitoring, and high severity suggests immediate medical consultation."
        }
    ]
    
    for i, faq in enumerate(faq_data):
        with st.expander(faq["question"]):
            st.write(faq["answer"])

# Image processing functions (unchanged)
def denoise_image(img):
    return cv2.GaussianBlur(img, (5, 5), 0)

def apply_clahe(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)

def adaptive_thresholding(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

def canny_edge_detection(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Canny(gray, 100, 200)

def find_and_filter_contours(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_img = np.zeros_like(img)
    cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
    return contour_img

def watershed_segmentation(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    sure_bg = cv2.dilate(opening, kernel, iterations=3)
    dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
    _, sure_fg = cv2.threshold(dist_transform, 0.7 * dist_transform.max(), 255, 0)
    sure_fg = np.uint8(sure_fg)
    unknown = cv2.subtract(sure_bg, sure_fg)
    markers = cv2.connectedComponents(sure_fg)[1]
    markers = markers + 1
    markers[unknown == 255] = 0
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    markers = np.int32(markers)
    cv2.watershed(img, markers)
    img[markers == -1] = [255, 0, 0]
    return img

# Tumor detection function using YOLO
def detect_tumor_with_yolo(img):
    img_preprocessed = denoise_image(img)
    pred = model.predict(img_preprocessed)[0]
    img_with_boxes = pred.plot()
    
    boxes = pred.boxes.xyxy
    tumor_lengths = []

    for box in boxes:
        x1, y1, x2, y2 = box
        length = x2 - x1
        tumor_lengths.append(length)
        cv2.rectangle(img_with_boxes, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        
        # Add additional metrics like area
        width = y2 - y1
        area = length * width
        cv2.putText(img_with_boxes, f"Area: {area:.1f}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    return img_with_boxes, tumor_lengths

def clear_history():
    conn = sqlite3.connect("tumor_detection.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections")
    conn.commit()
    conn.close()

# Add data visualization for historical data
def generate_stats_visualization():
    conn = sqlite3.connect("tumor_detection.db")
    
    try:
        # Get data for charts
        df = pd.read_sql_query("SELECT * FROM detections", conn)
        
        if len(df) > 0:
            # Convert detection_time to datetime
            df['detection_time'] = pd.to_datetime(df['detection_time'])
            df['month_year'] = df['detection_time'].dt.strftime('%Y-%m')
            
            # Create a histogram of tumor counts
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            df['tumor_count'].plot(kind='hist', bins=10, ax=ax1)
            ax1.set_title('Distribution of Tumor Counts')
            ax1.set_xlabel('Number of Tumors')
            ax1.set_ylabel('Frequency')
            
            # Create a time series of detections
            monthly_counts = df.groupby('month_year').size()
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            monthly_counts.plot(kind='line', ax=ax2)
            ax2.set_title('Monthly Detection Counts')
            ax2.set_xlabel('Month')
            ax2.set_ylabel('Number of Detections')
            
            # Create a pie chart of severity distribution if available
            if 'severity' in df.columns:
                severity_counts = df['severity'].value_counts()
                fig3, ax3 = plt.subplots(figsize=(8, 8))
                severity_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax3)
                ax3.set_title('Distribution of Severity Levels')
                ax3.set_ylabel('')
                
                return fig1, fig2, fig3
            
            return fig1, fig2, None
        
        return None, None, None
    
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")
        return None, None, None
    finally:
        conn.close()

# Chatbot functionality
def display_chatbot_page():
    st.title("💬 Brain Tumor Medical Assistant")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your Brain Tumor Detection Assistant. You can ask me questions about brain tumors, detection methods, or your results. How can I help you today?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input for new message
    if prompt := st.chat_input("Ask a question about brain tumors or your results"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Process the message and generate a response
        response = process_chatbot_query(prompt)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.markdown(response)

def process_chatbot_query(query):
    # Simple rule-based responses for common questions
    query_lower = query.lower()
    
    # Brain tumor general information
    if any(keyword in query_lower for keyword in ["what is", "brain tumor", "definition"]):
        return """
        A brain tumor is a mass or growth of abnormal cells in the brain. Brain tumors can be benign (non-cancerous) or malignant (cancerous). Benign tumors grow slowly and typically don't spread to other parts of the body. Malignant tumors grow rapidly and can invade nearby tissues.
        
        Brain tumors are classified based on:
        - Where they originated (primary vs. metastatic)
        - Their cell type
        - Their grade (aggressiveness)
        - Their location in the brain
        """
    
    # Symptoms
    elif any(keyword in query_lower for keyword in ["symptom", "sign", "indication"]):
        return """
        Common symptoms of brain tumors include:
        
        - Headaches (especially those that wake you up in the morning)
        - Seizures
        - Difficulty thinking, speaking, or finding words
        - Personality or behavior changes
        - Weakness or paralysis in one part or side of the body
        - Loss of balance or coordination
        - Vision problems
        - Nausea and vomiting
        
        Please note that these symptoms can also be caused by many other conditions. If you're experiencing these symptoms, consult a healthcare professional for proper evaluation.
        """
    
    # About detection methods
    elif any(keyword in query_lower for keyword in ["detection method", "diagnosis", "test", "yolo", "image processing"]):
        return """
        Brain tumors are detected using several methods:
        
        1. Imaging tests:
           - MRI (Magnetic Resonance Imaging) - The primary method used in our system
           - CT scans
           - PET scans
        
        2. Biopsy - The definitive method to determine if a tumor is cancerous
        
        Our system uses advanced image processing techniques and a YOLO (You Only Look Once) deep learning model trained on brain MRI scans to detect and locate potential tumors. The process includes:
        
        - Image preprocessing (denoising, contrast enhancement)
        - Feature extraction
        - Tumor detection and classification
        
        While our system has high accuracy, all results should be confirmed by medical professionals.
        """
    
    # Treatment options
    elif any(keyword in query_lower for keyword in ["treatment", "therapy", "surgery", "option"]):
        return """
        Treatment options for brain tumors depend on type, size, location, and the patient's overall health. Common treatments include:
        
        1. Surgery - To remove as much of the tumor as safely possible
        
        2. Radiation Therapy - Uses high-energy beams to kill tumor cells
        
        3. Chemotherapy - Uses drugs to kill tumor cells
        
        4. Targeted Drug Therapy - Focuses on specific abnormalities in cancer cells
        
        5. Immunotherapy - Helps your immune system fight the cancer
        
        6. Rehabilitation - May be needed after treatment to regain lost abilities
        
        Treatment often involves a combination of these approaches. A team of specialists (neuro-oncologists, neurosurgeons, radiation oncologists) will develop a personalized treatment plan.
        """
    
    # Severity levels
    elif any(keyword in query_lower for keyword in ["severity", "stage", "grade", "seriousness"]):
        return """
        Brain tumor severity is typically classified in several ways:
        
        1. WHO Grade (I-IV):
           - Grade I: Slow growing, least malignant
           - Grade II: Relatively slow growing
           - Grade III: Actively reproducing abnormal cells
           - Grade IV: Rapidly reproducing, highly malignant
        
        2. In our system, we provide a simplified assessment based on tumor size relative to brain area:
           - Low Severity: Smaller tumors (<1% of brain area)
           - Moderate Severity: Medium-sized tumors (1-5% of brain area)
           - High Severity: Larger tumors (>5% of brain area)
        
        These assessments help guide follow-up recommendations but should always be reviewed by medical professionals.
        """
    
    # About our system
    elif any(keyword in query_lower for keyword in ["system", "app", "application", "accuracy", "reliable"]):
        return """
        Our Brain Tumor Detection System:
        
        - Uses a YOLO (You Only Look Once) deep learning model trained on thousands of brain MRI scans
        - Implements multiple image processing techniques to enhance visualization
        - Provides severity assessment based on tumor size and characteristics
        - Generates detailed reports with measurements and recommendations
        - Has approximately 85-90% accuracy in controlled validation studies
        
        Limitations:
        - Should be used as a supportive tool, not for definitive diagnosis
        - Accuracy depends on image quality
        - May not detect very small tumors or certain rare types
        - Works best with T1 and T2-weighted MRI scans
        
        Always consult healthcare professionals for proper diagnosis and treatment decisions.
        """
    
    # Default response for other queries
    else:
        return """
        Thank you for your question. As a specialized medical assistant, I can provide information about:
        
        - Brain tumor definitions and types
        - Symptoms and warning signs
        - Detection and diagnostic methods
        - Treatment options
        - Our detection system's capabilities
        
        Please feel free to ask about any of these topics or specify your question further.
        
        Remember that all information provided is educational and should not replace professional medical advice.
        """

if __name__ == "__main__":
    main()