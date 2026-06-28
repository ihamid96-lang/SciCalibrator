import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from fpdf import FPDF
import tempfile
import os
from datetime import datetime

# ضبط إعدادات الصفحة لتكون عريضة واحترافية
st.set_page_config(page_title="SciCalibrator", layout="wide")

# --- دالة ذكية ومطورة لقراءة جميع أنواع ملفات الـ CSV وتخطي الأسطر النصية ---
def smart_load_data(file_uploaded):
    """
    تقرأ الملف وتتخطى الأسطر التوضيحية تلقائياً (التي تبدأ بـ # أو نصوص)
    وتتعامل مع الفواصل المختلفة (سواء كانت مسافات أو فواصل عادية).
    """
    if file_uploaded.name.endswith(".xlsx"):
        return pd.read_excel(file_uploaded)
    
    # إذا كان الملف CSV، نقرأ الأسطر الأولى لمعرفة عدد أسطر التعليقات
    preview_file = file_uploaded.getvalue().decode("utf-8").splitlines()
    skip_lines = 0
    
    for line in preview_file:
        # إذا كان السطر يبدأ بعلامة تعليق أو فارغ أو يحتوي على نصوص وصفية طويلة
        if line.strip().startswith('#') or line.strip().startswith('/*') or not line.strip():
            skip_lines += 1
        else:
            break
            
    # إعادة مؤشر الملف للبداية للقراءة بواسطة pandas
    file_uploaded.seek(0)
    
    # القراءة الذكية باستخدام محرّك python للتعامل مع الفواصل العشوائية والمسافات (\s+)
    df = pd.read_csv(
        file_uploaded,
        skiprows=skip_lines,
        sep=r'\s+|,',          # تعديل سحري: يقرأ الفواصل العادية أو المسافات المتعددة معاً
        engine='python',
        on_bad_lines='skip'    # يتجاهل أي سطر يسبب خطأ بدلاً من إيقاف البرنامج
    )
    
    # تنظيف أسماء الأعمدة من أي رموز أو مسافات زائدة
    df.columns = [str(col).strip().replace('"', '').replace("'", "") for col in df.columns]
    return df

# --- 1. دالة إنشاء ملف PDF الارترافي (شعار + رسوم + نصوص) ---
def create_pdf(results_list, logo_path=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    for res in results_list:
        pdf.add_page()
        
        # --- الهيدر (الشعار والعنوان) ---
        if logo_path and os.path.exists(logo_path):
            pdf.image(logo_path, x=160, y=10, w=35) 
        
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(44, 62, 80) # لون أزرق داكن رسمي
        pdf.cell(0, 15, txt="SciCalibrator - Analysis Report", ln=True, align='L')
        
        pdf.set_font("Arial", 'I', 10)
        pdf.set_text_color(127, 140, 141) # لون رمادي للتاريخ
        pdf.cell(0, 5, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='L')
        pdf.ln(10)
        pdf.set_text_color(0, 0, 0) # إعادة اللون للأسود

        # --- قسم تفاصيل المحلل ---
        safe_name = str(res['name']).encode('ascii', 'ignore').decode('ascii').strip()
        if not safe_name: safe_name = "Unknown Analyte"
        
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240) # خلفية رمادية فاتحة للعنوان
        pdf.cell(0, 10, txt=f"Analyte: {safe_name}", ln=True, fill=True)
        pdf.ln(5)

        # --- إضافة الرسم البياني ---
        if 'plot_path' in res and os.path.exists(res['plot_path']):
            pdf.image(res['plot_path'], x=25, y=pdf.get_y(), w=160)
            pdf.ln(95) 

        # --- قسم النتائج الإحصائية ---
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt="Statistical Results:", ln=True)
        
        pdf.set_font("Arial", size=11)
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
        # 1. القراءة الذكية للملف وتجاوز الأسطر التوضيحية تلقائياً
        if file.name.endswith(".csv"):
            data = pd.read_csv(
                file, 
                comment='#',        # يتجاهل أي سطر يبدأ بـ # كأسلوب ملفات NOAA
                sep=None,           # يكتشف الفاصل تلقائياً (فاصلة أو مسافات)
                engine='python', 
                on_bad_lines='skip' # يتخطى الأسطر المعطوبة
            )
        else:
            data = pd.read_excel(file)

        # تنظيف مساحات الأسماء في العناوين
        data.columns = data.columns.str.strip()

        # 2. تحويل ذكي للأعمدة الرقمية فقط دون تدمير البيانات
        for col in data.columns:
            # محاولة تحويل العمود إلى رقمي مع استبدال الفواصل
            converted = pd.to_numeric(data[col].astype(str).str.replace(',', '').str.strip(), errors='coerce')
            
            # إذا كان العمود يحتوي على أرقام فعلية (أكثر من 30% من الأسطر أرقام)، نعتمد التحويل
            if converted.notna().sum() > (len(data) * 0.3):
                data[col] = converted

        # 3. حذف الأسطر الفارغة تماماً فقط، بدلاً من حذف الأسطر التي تحتوي على نص
        # هذا يضمن بقاء البيانات الرقمية مطابقة لعناوينها
        data = data.dropna(subset=[data.columns[0]]) # يضمن وجود قيمة في العمود الأول على الأقل
        data = data.reset_index(drop=True)

        st.subheader("Data Preview")
        st.dataframe(data, use_container_width=True)

            if st.button("Run Full Analysis"):
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
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
                    ax1.scatter(concentration, y, color='#3498db', label='Actual Data')
                    ax1.plot(concentration, y_pred, color='#e74c3c', label='Linear Fit')
                    ax1.set_title("Calibration Curve")
                    ax1.set_xlabel("X (Concentration / Signal)")
                    ax1.set_ylabel("Y (Response / Target)")
                    ax1.legend()
                    ax1.grid(True, linestyle='--', alpha=0.5)
                    
                    ax2.scatter(concentration, y - y_pred, color='#2ecc71')
                    ax2.axhline(0, color='black', linestyle='--')
                    ax2.set_title("Residual Plot")
                    ax2.set_xlabel("X (Concentration / Signal)")
                    ax2.set_ylabel("Residuals")
                    ax2.grid(True, linestyle='--', alpha=0.5)
                    
                    st.pyplot(fig)

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_plot:
                        fig.savefig(tmp_plot.name, dpi=100, bbox_inches='tight')
                        plot_path = tmp_plot.name
                    
                    plt.close(fig)

                    st.session_state.results.append({
                        "name": column, 
                        "slope": slope, 
                        "intercept": intercept, 
                        "r2": r_value**2, 
                        "std_err": std_err,
                        "plot_path": plot_path
                    })
                    st.success(f"Successfully analyzed {column}")

    except Exception as e:
        st.error(f"Error processing file: {e}")

# --- 3. قسم تصدير التقرير ---
if "results" in st.session_state and st.session_state.results:
    st.divider()
    st.subheader("📊 Export Professional Report")
    
    col
