import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from fpdf import FPDF
import tempfile
import os

# --- 1. دالة إنشاء ملف PDF مع معالجة صارمة للرموز ---
def create_pdf(results_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SciCalibrator - Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    for res in results_list:
        # تحويل أي اسم إلى نصوص ASCII فقط وحذف الرموز غير المعرفة
        # هذا يمنع خطأ FPDFUnicodeEncodingException نهائياً
        raw_name = str(res['name'])
        safe_name = raw_name.encode('ascii', 'ignore').decode('ascii').strip()
        if not safe_name:
            safe_name = "Unknown Analyte"

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Analyte: {safe_name}", ln=True)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 8, txt=f"- Slope: {float(res['slope']):.4f}", ln=True)
        pdf.cell(200, 8, txt=f"- Intercept: {float(res['intercept']):.4f}", ln=True)
        pdf.cell(200, 8, txt=f"- R-squared: {float(res['r2']):.4f}", ln=True)
        pdf.cell(200, 8, txt=f"- Std Error: {float(res['std_err']):.4f}", ln=True)
        pdf.ln(5)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

# --- 2. واجهة التطبيق الرئيسية ---
st.title("SciCalibrator 🧪")
st.write("Professional Calibration Data Analysis")

file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if file is not None:
    try:
        # قراءة الملف
        if file.name.endswith(".csv"):
            data = pd.read_csv(file)
        else:
            data = pd.read_excel(file)

        # تنظيف البيانات: تحويل كل الأعمدة لأرقام وحذف الصفوف الفارغة
        for col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', ''), errors='coerce')
        data = data.dropna()

        st.subheader("Data Preview")
        st.dataframe(data)

        if st.button("Run Full Analysis"):
            st.session_state.results = [] 
            concentration = data.iloc[:, 0]

            for column in data.columns[1:]:
                y = data[column]
                slope, intercept, r_value, p_value, std_err = linregress(concentration, y)
                y_pred = slope * concentration + intercept
                
                st.markdown(f"### Analysis: **{column}**")
                
                # عرض الرسوم البيانية
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
                ax1.scatter(concentration, y, color='blue', label='Actual')
                ax1.plot(concentration, y_pred, color='red', label='Fit')
                ax1.set_title("Calibration Curve")
                ax1.legend()
                
                ax2.scatter(concentration, y - y_pred, color='green')
                ax2.axhline(0, color='black', linestyle='--')
                ax2.set_title("Residual Plot")
                st.pyplot(fig)

                # حفظ النتائج في session_state
                st.session_state.results.append({
                    "name": column, 
                    "slope": slope, 
                    "intercept": intercept, 
                    "r2": r_value**2, 
                    "std_err": std_err
                })
                st.success(f"Successfully analyzed {column}")

    except Exception as e:
        st.error(f"Error processing file: {e}")

# --- 3. قسم تصدير التقرير (خارج بلوك الـ file لضمان الثبات) ---
if "results" in st.session_state and st.session_state.results:
    st.divider()
    st.subheader("📊 Export Results")
    
    try:
        pdf_path = create_pdf(st.session_state.results)
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Download Analysis Report (PDF)",
                data=f,
                file_name="Calibration_Report.pdf",
                mime="application/pdf"
            )
    except Exception as e:
        st.warning("Could not generate PDF due to special characters in data names. Check your column titles.")
