import streamlit as st
import pandas as pd
import logging
import os
import io
from datetime import datetime

# -------------------------------
# Streamlit Page Config
# -------------------------------
st.set_page_config(
    page_title="MI Data Quality Tool",
    layout="centered"
)

st.title("📊 MI Data Quality & Reporting Tool")
st.write("Upload stock data Excel file and generate MI report with process log.")

# -------------------------------
# In-memory Log Buffer (Cloud-safe)
# -------------------------------
log_buffer = io.StringIO()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(log_buffer)]
)

# -------------------------------
# File uploader
# -------------------------------
uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

# -------------------------------
# Run Button
# -------------------------------
if uploaded_file and st.button("🚀 Run Report"):

    logging.info("===== PROCESS STARTED =====")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        # -------------------------------
        # Read Excel
        # -------------------------------
        df = pd.read_excel(uploaded_file)
        logging.info(f"Rows read: {len(df)}")

        # -------------------------------
        # Data Quality Checks
        # -------------------------------
        logging.info("Running data quality checks")
        logging.info(f"Null counts:\n{df.isnull().sum()}")

        # -------------------------------
        # Business Calculations
        # -------------------------------
        df["Investment_Value"] = df["Buy_Price"] * df["Quantity"]
        df["Current_Value"] = df["Current_Price"] * df["Quantity"]
        df["Profit_Loss"] = df["Current_Value"] - df["Investment_Value"]

        df["Status"] = df["Profit_Loss"].apply(
            lambda x: "Profit" if x > 0 else "Loss"
        )

        df["High_Risk_Flag"] = df["Risk_Level"].apply(
            lambda x: "Yes" if str(x).lower() == "high" else "No"
        )

        # -------------------------------
        # Summary Tables
        # -------------------------------
        portfolio_summary = pd.DataFrame({
            "Total_Investment": [df["Investment_Value"].sum()],
            "Total_Current_Value": [df["Current_Value"].sum()],
            "Net_Profit_Loss": [df["Profit_Loss"].sum()]
        })

        sector_summary = df.groupby("Sector", as_index=False)["Profit_Loss"].sum()

        # -------------------------------
        # Write Output Excel (in-memory)
        # -------------------------------
        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Detailed_Stock_Data", index=False)
            portfolio_summary.to_excel(writer, sheet_name="Portfolio_Summary", index=False)
            sector_summary.to_excel(writer, sheet_name="Sector_Summary", index=False)

        output_buffer.seek(0)
        logging.info("Output Excel generated successfully")
        logging.info("===== PROCESS COMPLETED =====")

        # -------------------------------
        # Success Message
        # -------------------------------
        st.success("✅ Report generated successfully!")

        # -------------------------------
        # Download Buttons
        # -------------------------------
        st.download_button(
            label="⬇️ Download MI Output Excel",
            data=output_buffer,
            file_name=f"stocks_mi_output_{timestamp}.xlsx"
        )

        st.download_button(
            label="⬇️ Download Process Log",
            data=log_buffer.getvalue(),
            file_name=f"data_process_{timestamp}.log"
        )

    except Exception as e:
        logging.error("Process failed", exc_info=True)
        st.error("❌ Processing failed. Please download and check the process log.")
