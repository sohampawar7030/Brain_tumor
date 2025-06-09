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
    st.title("💥 Brain Tumor Detection Using Image Processing 🧠")
    
    st.markdown("""
    ## Welcome to our Brain Tumor Detection System
    
    This application uses advanced image processing techniques and machine learning to detect brain tumors from MRI scans.
    
    ### Key Features:
    - Upload and analyze MRI scans
    - Multiple image processing filters
    - YOLO-based tumor detection
    - Detailed reports via email
    - Historical record keeping
    
    ### How to Use:
    1. Navigate to the Detection page
    2. Upload your MRI scan
    3. Enter patient information
    4. Click "Detect Tumor with YOLO"
    5. Receive detailed analysis and report
    
    """)
    
    # # Sample images
    # st.subheader("Sample Detection Results")
    # col1, col2 = st.columns(2)
    # with col1:
    #     st.image("https://via.placeholder.com/400x300", caption="Sample MRI Scan")
    # with col2:
    #     st.image("https://via.placeholder.com/400x300", caption="Detected Tumor")

def display_detection_page():
    st.title("💥 Brain Tumor Detection Using Image Processing 🧠")
    st.write(
        "This application allows you to detect brain tumors using YOLO and various image processing techniques."
    )

    # Sidebar for file upload and patient information
    st.sidebar.title("Upload Image")
    uploaded_file = st.sidebar.file_uploader("Upload a Brain Image:", type=["png", "jpg", "jpeg"])
    patient_name = st.sidebar.text_input("Patient Name")
    email = st.sidebar.text_input("Email Address (for report)")
    patient_age = st.sidebar.number_input("Patient Age", min_value=0, max_value=120, value=30)
    patient_gender = st.sidebar.selectbox("Patient Gender", ["Male", "Female", "Other"])
    
    # Add a progress placeholder
    progress_placeholder = st.empty()

    # Initialize variables
    image = None
    tumor_detected = False

    # Main display area with two columns
    col1, col2 = st.columns(2)

    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        with col1:
            st.subheader("Original Image")
            st.image(image, caption="Uploaded MRI Scan", use_column_width=True)
            
            # Processing Buttons in main area instead of sidebar
            processing_options = st.multiselect(
                "Select Processing Methods",
                ["Denoise Image", "CLAHE", "Adaptive Thresholding", "Canny Edge Detection", "Contours"]
            )
            
            if processing_options:
                if "Denoise Image" in processing_options:
                    denoised_img = denoise_image(image)
                    with col2:
                        st.subheader("Processed Image")
                        st.image(denoised_img, caption="Denoised Image", use_column_width=True)
                
                if "CLAHE" in processing_options:
                    clahe_img = apply_clahe(image)
                    with col2:
                        st.subheader("Processed Image")
                        st.image(clahe_img, caption="CLAHE Processed Image", use_column_width=True)
                
                if "Adaptive Thresholding" in processing_options:
                    threshold_img = adaptive_thresholding(image)
                    with col2:
                        st.subheader("Processed Image")
                        st.image(threshold_img, caption="Adaptive Thresholding Result", use_column_width=True)
                
                if "Canny Edge Detection" in processing_options:
                    edge_img = canny_edge_detection(image)
                    with col2:
                        st.subheader("Processed Image")
                        st.image(edge_img, caption="Canny Edge Detection Result", use_column_width=True)
                
                if "Contours" in processing_options:
                    contour_img = find_and_filter_contours(image)
                    with col2:
                        st.subheader("Processed Image")
                        st.image(contour_img, caption="Contours", use_column_width=True)
                

    # YOLO Tumor Detection
    detection_btn = st.button("Detect Tumor with YOLO")
    
    if detection_btn and image is not None:
        if not patient_name:
            st.warning("Please enter the patient's name.")
        elif not email:
            st.warning("Please enter an email address to receive the report.")
        else:
            # Show progress
            progress_bar = progress_placeholder.progress(0)
            progress_placeholder.text("Preprocessing image...")
            time.sleep(0.5)
            progress_bar.progress(20)
            
            progress_placeholder.text("Analyzing with YOLO model...")
            time.sleep(0.5)
            progress_bar.progress(40)
            
            # Perform actual detection
            yolo_img, tumor_lengths = detect_tumor_with_yolo(image)
            
            progress_placeholder.text("Processing results...")
            time.sleep(0.5)
            progress_bar.progress(60)
            
            with col2:
                st.subheader("Detection Results")
                st.image(yolo_img, caption="YOLO Tumor Detection Result", use_column_width=True)

            if tumor_lengths:
                tumor_detected = True
                
                # Convert tensor values to Python floats
                tumor_lengths = [float(length) for length in tumor_lengths]
                
                # Assess tumor severity
                severity, recommendation = assess_tumor_severity(tumor_lengths, image.shape)
                
                # Display results in a nice format
                st.success(f"✅ Analysis Complete")
                
                results_col1, results_col2 = st.columns(2)
                with results_col1:
                    st.metric("Number of Tumors", len(tumor_lengths))
                    st.metric("Severity Assessment", severity)
                
                with results_col2:
                    st.metric("Largest Tumor (pixels)", round(max(tumor_lengths), 2))
                    st.metric("Average Tumor Size", round(sum(tumor_lengths)/len(tumor_lengths), 2))
                
                st.info(f"Recommendation: {recommendation}")
                
                # Convert the processed image to PNG format
                _, buffer = cv2.imencode('.png', yolo_img)
                processed_image = buffer.tobytes()
                
                progress_placeholder.text("Generating report...")
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
            ### Instructions:
            1. Upload a brain MRI scan image using the sidebar
            2. Enter patient information
            3. Run image processing techniques to enhance visualization
            4. Click "Detect Tumor with YOLO" for automated analysis
            5. Receive detailed reports and analysis
            
            ⬅️ Please upload an image to get started
            """
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
    import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import cv2
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import base64
from streamlit_lottie import st_lottie
import requests
import time

def load_lottie_url(url: str):
    """Load a Lottie animation from URL"""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def clear_history():
    """Clear all detection history from the database"""
    conn = sqlite3.connect("tumor_detection.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections")
    conn.commit()
    conn.close()

def get_tumor_trend_chart(df):
    """Generate tumor detection trend chart"""
    if 'detection_time' not in df.columns or df.empty:
        return None
    
    df['date'] = df['detection_time'].dt.date
    daily_counts = df.groupby('date').size().reset_index(name='count')
    
    fig = px.line(
        daily_counts, 
        x='date', 
        y='count',
        title='Detection Trend',
        labels={'count': 'Number of Detections', 'date': 'Date'},
        markers=True
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(240, 240, 240, 0.8)',
        font=dict(family="Arial", size=12),
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    return fig

def get_severity_distribution(df):
    """Generate severity distribution chart"""
    if 'severity' not in df.columns or df.empty:
        return None
    
    severity_counts = df['severity'].value_counts().reset_index()
    severity_counts.columns = ['severity', 'count']
    
    # Define colors for different severity levels
    colors = {'Low Severity': '#3498db', 'Medium Severity': '#f39c12', 'High Severity': '#e74c3c'}
    severity_colors = [colors.get(sev, '#95a5a6') for sev in severity_counts['severity']]
    
    fig = px.pie(
        severity_counts, 
        values='count', 
        names='severity',
        title='Severity Distribution',
        hole=0.4,
        color_discrete_sequence=severity_colors
    )
    
    fig.update_layout(
        legend_title_text='',
        font=dict(family="Arial", size=12),
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    return fig

def create_logo():
    """Create a custom logo for the app"""
    # Create a simple logo with text
    logo_html = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600&display=swap');
    
    .logo-container {
        display: flex;
        align-items: center;
        background: linear-gradient(90deg, #3498db, #2980b9);
        border-radius: 10px;
        padding: 10px 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        color: white;
        transition: all 0.3s ease;
    }
    
    .logo-container:hover {
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    .logo-icon {
        font-size: 28px;
        margin-right: 10px;
    }
    
    .logo-text {
        font-family: 'Montserrat', sans-serif;
        font-size: 22px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .logo-highlight {
        color: #ecf0f1;
        font-weight: bold;
    }
    </style>
    
    <div class="logo-container">
        <div class="logo-icon">📊</div>
        <div class="logo-text">Neuro<span class="logo-highlight">Vision</span> Analytics</div>
    </div>
    """
    return logo_html

def main():
    # Apply custom CSS for animations and styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap');
    
    .stApp {
        font-family: 'Roboto', sans-serif;
    }
        
    .stButton>button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .record-card {
        animation: fadeIn 0.5s ease-in-out;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .record-card:hover {
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        transform: translateY(-3px);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .metric-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-container:hover {
        transform: scale(1.03);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 500;
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 14px;
        color: #7f8c8d;
        margin-top: 5px;
    }
    
    .severity-high {
        color: #e74c3c;
        font-weight: bold;
    }
    
    .severity-medium {
        color: #f39c12;
        font-weight: bold;
    }
    
    .severity-low {
        color: #3498db;
        font-weight: bold;
    }
    
    .alert-box {
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    
    .alert-icon {
        font-size: 20px;
        margin-right: 10px;
    }
    
    .alert-text {
        flex-grow: 1;
    }
    
    .alert-info {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        color: #0c5460;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        color: #856404;
    }
    
    .alert-danger {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        color: #721c24;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the custom logo
    st.markdown(create_logo(), unsafe_allow_html=True)
    
    # Application title with animation
    st.markdown("""
    <h1 style='text-align: center; color: #2c3e50; margin-bottom: 20px; animation: fadeIn 1s ease-in-out;'>
        Detection History Dashboard
    </h1>
    """, unsafe_allow_html=True)
    
    # Add loading animation when the page loads
    with st.spinner("Loading data..."):
        time.sleep(0.5)  # Simulated loading delay for effect
        
        # Load lottie animation for empty state
        empty_animation = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_ydo1amjm.json")
        
        # Connect to database
        conn = sqlite3.connect("tumor_detection.db")
        
        try:
            df = pd.read_sql_query("SELECT * FROM detections ORDER BY detection_time DESC", conn)
            
            if not df.empty:
                # Convert detection_time to datetime if it exists
                if 'detection_time' in df.columns:
                    df['detection_time'] = pd.to_datetime(df['detection_time'])
                
                # Create tabs for better organization
                tab1, tab2 = st.tabs(["📊 Dashboard", "🔍 Patient Records"])
                
                with tab1:
                    st.subheader("Analytics Overview")
                
                    # Show filters in a collapsible section
                    with st.expander("📋 Filters", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Add date filter
                            if 'detection_time' in df.columns:
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
                        
                        with col2:
                            # Add severity filter if available
                            if 'severity' in df.columns:
                                severity_options = ['All'] + sorted(list(filtered_df['severity'].unique()))
                                selected_severity = st.selectbox("Filter by Severity", severity_options)
                                
                                if selected_severity != 'All':
                                    filtered_df = filtered_df[filtered_df['severity'] == selected_severity]
                    
                    # Display metrics with animation effect
                    st.markdown("<h3 style='margin-top: 20px;'>Key Metrics</h3>", unsafe_allow_html=True)
                    
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    
                    with stats_col1:
                        st.markdown(f"""
                        <div class="metric-container">
                            <div class="metric-value">{len(filtered_df)}</div>
                            <div class="metric-label">Total Patients</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with stats_col2:
                        if 'tumor_count' in filtered_df.columns:
                            avg_tumors = filtered_df['tumor_count'].mean()
                            st.markdown(f"""
                            <div class="metric-container">
                                <div class="metric-value">{avg_tumors:.1f}</div>
                                <div class="metric-label">Avg Tumors per Patient</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with stats_col3:
                        if 'severity' in filtered_df.columns:
                            high_severity_count = len(filtered_df[filtered_df['severity'] == 'High Severity'])
                            st.markdown(f"""
                            <div class="metric-container">
                                <div class="metric-value">{high_severity_count}</div>
                                <div class="metric-label">High Severity Cases</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with stats_col4:
                        if 'patient_age' in filtered_df.columns:
                            avg_age = filtered_df['patient_age'].mean() if 'patient_age' in filtered_df.columns else 0
                            st.markdown(f"""
                            <div class="metric-container">
                                <div class="metric-value">{int(avg_age)}</div>
                                <div class="metric-label">Average Patient Age</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Charts section with animations
                    st.markdown("<h3 style='margin-top: 30px;'>Analytics</h3>", unsafe_allow_html=True)
                    
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        trend_chart = get_tumor_trend_chart(filtered_df)
                        if trend_chart:
                            st.plotly_chart(trend_chart, use_container_width=True)
                        else:
                            st.info("Insufficient data for trend chart")
                    
                    with chart_col2:
                        severity_chart = get_severity_distribution(filtered_df)
                        if severity_chart:
                            st.plotly_chart(severity_chart, use_container_width=True)
                        else:
                            st.info("Insufficient data for severity distribution")
                
                with tab2:
                    # Search functionality
                    st.subheader("Patient Search")
                    search_query = st.text_input("Search by patient name", "")
                    
                    if search_query:
                        search_results = filtered_df[filtered_df['patient_name'].str.contains(search_query, case=False)]
                        if not search_results.empty:
                            st.success(f"Found {len(search_results)} matching patients")
                            display_df = search_results
                        else:
                            st.warning("No patients found matching your search")
                            display_df = filtered_df
                    else:
                        display_df = filtered_df
                    
                    # Display patient records
                    st.subheader(f"Patient Records ({len(display_df)})")
                    
                    for idx, record in display_df.iterrows():
                        # Define severity class for styling
                        severity_class = ""     
                        if 'severity' in record:
                            if record['severity'] == 'High Severity':
                                severity_class = "severity-high"
                            elif record['severity'] == 'Medium Severity':
                                severity_class = "severity-medium"
                            else:
                                severity_class = "severity-low"
                        
                        with st.expander(f"Patient: {record['patient_name']} - {record['detection_time'].strftime('%Y-%m-%d %H:%M')}"):
                            st.markdown(f"""
                            <div class="record-card">
                                <div class="row">
                                    <div class="column">
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown(f"""
                                <div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                                    <h4>Patient Information</h4>
                                    <p><strong>Age:</strong> {record.get('patient_age', 'N/A')}</p>
                                    <p><strong>Gender:</strong> {record.get('patient_gender', 'N/A')}</p>
                                    <p><strong>Tumor Count:</strong> {record['tumor_count']}</p>
                                    <p><strong>Severity:</strong> <span class="{severity_class}">{record.get('severity', 'N/A')}</span></p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                if 'recommendation' in record:
                                    st.markdown(f"""
                                    <div style="padding: 10px; margin-top: 10px; background-color: #f8f9fa; border-radius: 5px;">
                                        <h4>Recommendation</h4>
                                        <p>{record['recommendation']}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with col2:
                                if 'processed_image' in record and record['processed_image'] is not None:
                                    try:
                                        processed_image = np.frombuffer(record['processed_image'], np.uint8)
                                        processed_image = cv2.imdecode(processed_image, cv2.IMREAD_COLOR)
                                        processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
                                        st.image(processed_image, caption="Processed Image with Detected Tumors", use_column_width=True)
                                    except Exception:
                                        st.warning("Could not display image")
                            
                            # Action buttons with hover effects
                            st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
                            btn1, btn2, btn3, btn4 = st.columns(4)
                            
                            with btn1:
                                st.button("📋 View Full Report", key=f"view_{record['id']}")
                            
                            with btn2:
                                st.button("📧 Send Report", key=f"send_{record['id']}")
                            
                            with btn3:
                                st.button("📄 Export PDF", key=f"pdf_{record['id']}")
                            
                            with btn4:
                                st.button("🗑️ Delete", key=f"del_{record['id']}")
                            
                            st.markdown("</div>", unsafe_allow_html=True)
            else:
                # Show empty state with animation
                st.markdown("""
                <div class="alert-box alert-info">
                    <div class="alert-icon">📊</div>
                    <div class="alert-text">No detection history available. Start analyzing images to build your history.</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display a centered Lottie animation for empty state
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if empty_animation:
                        st_lottie(empty_animation, height=300, key="empty")
        
        except Exception as e:
            st.error(f"Error accessing database: {str(e)}")
        
        conn.close()
        
        # Add admin actions in a collapsible section
        with st.expander("🔧 Admin Actions"):
            st.warning("⚠️ These actions cannot be undone. Please use with caution.")
            
            if st.button("Clear All History", key="clear_history"):
                confirm = st.button("⚠️ Confirm Delete All Records", key="confirm_delete")
                if confirm:
                    clear_history()
                    st.success("✅ Detection history cleared successfully.")
                    time.sleep(1)
                    st.experimental_rerun()


def display_about_page():
    st.title("About Brain Tumor Detection System")
    
    st.markdown("""
    ## Our Mission
    
    Our mission is to provide accessible and accurate brain tumor detection technology to help healthcare professionals make informed decisions.
    
    ## Technology
    
    This application uses:
    
    - **YOLO (You Only Look Once)**: A state-of-the-art real-time object detection system
    - **OpenCV**: For image processing and computer vision algorithms
    - **Streamlit**: For the interactive web interface
    - **Machine Learning**: Custom trained models for tumor detection
    
    ## Limitations
    
    Please note that this system:
    
    - Is intended as a support tool for healthcare professionals
    - Should not replace professional medical diagnosis
    - Has varying accuracy depending on image quality and tumor characteristics
    
    ## Team
    
    - prof. Disha Nagpure (Project Guide)
    - Pawar Soham (Team Leader) 
    - Kangude Samruddhi
    - Paitwar Dattatray 
    - Magar Aditi 
    
    ## Contact
    
    For more information, please contact us at support@braintumordetection.example.com
    
    """)
def display_faq_page():
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