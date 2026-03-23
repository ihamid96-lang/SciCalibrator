import streamlit as st
import pandas as pd
from scipy.stats import linregress
from fpdf import FPDF
import tempfile

# دالة إنشاء ملف PDF
def create_pdf(results_list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SciCalibrator - Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    for res in results_list:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Analyte: {res['name']}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 8, txt=f"- Slope: {res['slope']:.4f}", ln=True)
        pdf.cell(200, 8, txt=f"- Intercept: {res['intercept']:.4f}", ln=True)
        pdf.cell(200, 8, txt=f"- R-squared: {res['r2']:.4f}", ln=True)
        pdf.cell(200, 8, txt=f"- Std Error: {res['std_err']:.4f}", ln=True)
        pdf.ln(5)
    
    # حفظ الملف في مسار مؤقت
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        return tmp.name

# --- واجهة التطبيق ---
st.title("SciCalibrator")

file = st.file_uploader("Upload calibration data", type=["csv", "xlsx"])

if file is not None:
    # معالجة البيانات
    data = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
    for col in data.columns:
        data[col] = pd.to_numeric(data[col].astype(str).str.replace(',', ''), errors='coerce')
    data = data.dropna()

    st.subheader("Data Preview")
    st.dataframe(data)

    if st.button("Analyze"):
        st.session_state.results = [] # تخزين النتائج للتقرير
        concentration = data.iloc[:, 0]

        for column in data.columns[1:]:
            y = data[column]
            slope, intercept, r_value, p_value, std_err = linregress(concentration, y)
            
            # عرض النتائج في التطبيق
            st.write(f"### {column}")
            st.info(f"R²: {r_value**2:.4f} | Slope: {slope:.4f}")
            
            # حفظ النتائج في القائمة لإدراجها في الـ PDF
            st.session_state.results.append({
                "name": column,
                "slope": slope,
                "intercept": intercept,
                "r2": r_value**2,
                "std_err": std_err
            })

    # --- قسم الخدمة المدفوعة (التحميل) ---
    if "results" in st.session_state:
        st.divider()
        st.subheader("💎 Premium Features")
        
        # هنا يمكنك إضافة بوابة دفع مستقبلاً، حالياً سنضع الزر مباشرة
        if st.checkbox("Unlock PDF Report (Paid Service)"):
            pdf_path = create_pdf(st.session_state.results)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF Report",
                    data=f,
                    file_name="Calibration_Report.pdf",
                    mime="application/pdf"
                )