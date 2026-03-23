import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import linregress
from datetime import datetime

st.title("SciCalibrator")

st.write("Upload your calibration data (CSV or Excel)")

file = st.file_uploader("Upload file", type=["csv", "xlsx"])

if file is not None:

    if file.name.endswith(".csv"):
        data = pd.read_csv(file)
    else:
        data = pd.read_excel(file)

    st.subheader("Data Preview")
    st.dataframe(data)

    if st.button("Analyze"):

        st.subheader("Results")

        concentration = data.iloc[:,0]

        for column in data.columns[1:]:

            y = data[column]

            slope, intercept, r_value, p_value, std_err = linregress(concentration, y)

            y_pred = slope * concentration + intercept
            residuals = y - y_pred

            # Plot calibration curve
            fig1, ax1 = plt.subplots()
            ax1.scatter(concentration, y)
            ax1.plot(concentration, y_pred)
            ax1.set_title(f"Calibration Curve - {column}")
            ax1.set_xlabel("Concentration")
            ax1.set_ylabel("Response")
            st.pyplot(fig1)

            # Plot residuals
            fig2, ax2 = plt.subplots()
            ax2.scatter(concentration, residuals)
            ax2.axhline(0, linestyle='--')
            ax2.set_title(f"Residual Plot - {column}")
            st.pyplot(fig2)

            st.write(f"**{column}**")
            st.write(f"Slope: {slope:.4f}")
            st.write(f"Intercept: {intercept:.4f}")
            st.write(f"R²: {r_value**2:.4f}")
            st.write(f"Standard Error: {std_err:.4f}")
            # تنظيف البيانات: إزالة الفواصل وتحويل لأرقام
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna()