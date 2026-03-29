import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from fpdf import FPDF
import tempfile
import os

# ضبط إعدادات الصفحة لتكون عريضة واحترافية
st.set_page_config(page_title="SciCalibrator", layout="wide")

# --- 1. دالة إنشاء ملف PDF الاحترافي (شعار + رسوم + نصوص) ---
def create_pdf(results_list, logo_path=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for res in results_list:
        pdf.add_page()
        
        # --- الهيدر (الشعار والعنوان) ---
        if logo_path and os.path.exists(logo_path):
            # إضافة الشعار في الزاوية اليمنى العليا (تعديل الإحداثيات حسب الرغبة)
            pdf.image(logo_path, x=160, y=10, w=35) 
        
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(44, 62, 80) # لون أزرق داكن رسمي
        pdf.cell(0, 15, txt="SciCalibrator - Analysis Report", ln=True, align='L')
        
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(127, 140, 141) # لون رمادي للتاريخ
        from datetime import datetime
        pdf.cell(0, 5, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='L')
        pdf.ln(10)
        pdf.set_text_color(0, 0, 0) # إعادة اللون للأسود

        # --- قسم تفاصيل المحلل ---
        # تنظيف الاسم من الرموز التي تسبب خطأ Unicode
        safe_name = str(res['name']).encode('ascii', 'ignore').decode('ascii').strip()
        if not safe_name: safe_name = "Unknown Analyte"
        
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240) # خلفية رمادية فاتحة للعنوان
        pdf.cell(0, 10, txt=f"Analyte: {safe_name}", ln=True, fill=True)
        pdf.ln(5)

        # --- إضافة الرسم البياني ---
        # نتحقق من وجود مسار الصورة المؤقتة
        if 'plot_path' in res and os.path.exists(res['plot_path']):
            # إضافة الصورة (تعديل x, y, w, h لضبط المكان والحجم)
            # وضعناها في المنتصف بعرض 160 ملم
            pdf.image(res['plot_path'], x=25, y=pdf.get_y(), w=160)
            pdf.ln(95) # ترك مساحة تحت الصورة (اعتماداً على الـ height المُحدد)

        # --- قسم النتائج الإحصائية ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="Statistical Results:", ln=True)
        
        pdf.set_font("Arial", size=11)
        # إنشاء جدول بسيط للنتائج
        col_width = pdf.epw / 4 # تقسيم عرض الصفحة على 4
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(col_width, 8, "Slope", border=1, align='C')
        pdf.cell(col_width, 8, "Intercept", border=1, align='C')
        pdf.cell(col_width, 8, "R-squared", border=1, align='C')
        pdf.cell(col_width, 8, "Std Error", border=1, align='C')
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        pdf.cell(col_width, 8, f"{float(res['slope']):.4f}", border=1, align='C')
        pdf.cell(col_width, 8, f"{float(res['intercept']):.4f}", border=1, align='C')
        pdf.cell(col_width, 8, f"{float(res['r2']):.4f}", border=1, align='C')
        pdf.cell(col_width, 8, f"{float(res['std_err']):.4f}", border=1, align='C')
        pdf.ln(15)
        
        # إضافة خط فاصل في نهاية الصفحة
        pdf.set_draw_color(189, 195, 199)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    # حفظ الملف النهائي في مسار مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

# --- 2. واجهة التطبيق الرئيسية ---
col_head1, col_head2 = st.columns([1, 4])
with col_head1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120)
with col_head2:
    st.title("SciCalibrator 🧪")
    st.write("Professional Calibration Data Analysis & Reporting")

file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

if file is not None:
    try:
        # قراءة وتنظيف البيانات
        if file.name.endswith(".csv"):
            data = pd.read_csv(file)
        else:
            data = pd.read_excel(file)

        for col in data.columns:
            data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', ''), errors='coerce')
        data = data.dropna()

        st.subheader("Data Preview")
        st.dataframe(data, use_container_width=True)

        if st.button("Run Full Analysis"):
            # تنظيف النتائج السابقة وحذف الصور المؤقتة القديمة
            if "results" in st.session_state:
                for res in st.session_state.results:
                    if 'plot_path' in res and os.path.exists(res['plot_path']):
                        os.remove(res['plot_path'])
            
            st.session_state.results = [] 
            concentration = data.iloc[:, 0]

            for column in data.columns[1:]:
                y = data[column]
                slope, intercept, r_value, p_value, std_err = linregress(concentration, y)
                y_pred = slope * concentration + intercept
                
                st.markdown(f"### Analysis: **{column}**")
                
                # إنشاء الرسم البياني ودمج المنحنى والبواقي في شكل واحد للـ PDF
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
                ax1.scatter(concentration, y, color='#3498db', label='Actual Data') # لون أزرق جميل
                ax1.plot(concentration, y_pred, color='#e74c3c', label='Linear Fit') # لون أحمر
                ax1.set_title("Calibration Curve")
                ax1.set_xlabel("Concentration")
                ax1.set_ylabel("Response")
                ax1.legend()
                ax1.grid(True, linestyle='--', alpha=0.5)
                
                ax2.scatter(concentration, y - y_pred, color='#2ecc71') # لون أخضر
                ax2.axhline(0, color='black', linestyle='--')
                ax2.set_title("Residual Plot")
                ax2.set_xlabel("Concentration")
                ax2.set_ylabel("Residuals")
                ax2.grid(True, linestyle='--', alpha=0.5)
                
                st.pyplot(fig)

                # --- حفظ الرسم كصورة مؤقتة لإدراجها في الـ PDF ---
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_plot:
                    fig.savefig(tmp_plot.name, dpi=100, bbox_inches='tight')
                    plot_path = tmp_plot.name
                
                # إغلاق الشكل لتوفير الذاكرة
                plt.close(fig)

                # حفظ النتائج مع مسار الصورة في session_state
                st.session_state.results.append({
                    "name": column, 
                    "slope": slope, 
                    "intercept": intercept, 
                    "r2": r_value**2, 
                    "std_err": std_err,
                    "plot_path": plot_path # المسار السحري للصورة
                })
                st.success(f"Successfully analyzed {column}")

    except Exception as e:
        st.error(f"Error processing file: {e}")

# --- 3. قسم تصدير التقرير (دائماً في الأسفل) ---
if "results" in st.session_state and st.session_state.results:
    st.divider()
    st.subheader("📊 Export Professional Report")
    
    col_pdf1, col_pdf2 = st.columns([2, 1])
    with col_pdf1:
        st.info("The generated PDF report will include the application logo, calibration curves, residual plots, and statistical summary for each analyzed analyte.")
    
    with col_pdf2:
        try:
            # استدعاء الدالة الجديدة مع مسار الشعار
            pdf_path = create_pdf(st.session_state.results, logo_path="logo.png")
            
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 Download Professional PDF Report",
                    data=f,
                    file_name="SciCalibrator_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Could not generate PDF: {e}")
            st.warning("Ensure 'logo.png' exists in your repository and column names do not contain special characters.")
