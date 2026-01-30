import streamlit as st
import pandas as pd
import logging
import os
from datetime import datetime

# ===============================
# Logger function (Streamlit-safe)
# ===============================
def get_logger(log_file):
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ===============================
# App UI
# ===============================
st.set_page_config(page_title="MI Data Quality Tool", layout="centered")

st.title("📊 MI Data Quality & Reporting Tool")
st.write("Upload stock data Excel file and generate MI report with process log.")

# ===============================
# Folder setup
# ===============================
base_folder = "app_output"
output_folder = os.path.join(base_folder, "output")
log_folder = os.path.join(base_folder, "logs")

os.makedirs(output_folder, exist_ok=True)
os.makedirs(log_folder, exist_ok=True)

# ===============================
# File uploader
# ===============================
uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

# ===============================
# Run process
# ===============================
if uploaded_file is not None and st.button("🚀 Run Report"):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = os.path.join(
        output_folder, f"stocks_mi_output_{timestamp}.xlsx"
    )
    log_file = os.path.join(
        log_folder, f"data_process_{timestamp}.log"
    )

    logger = get_logger(log_file)
    logger.info("===== PROCESS STARTED =====")

    try:
        # -------------------------------
        # Read Excel
        # -------------------------------
        df = pd.read_excel(uploaded_file)
        logger.info(f"Rows read from input file: {len(df)}")

        # -------------------------------
        # Data Quality Checks
        # -------------------------------
        logger.info("Running data quality checks")
        logger.info(f"Null value summary:\n{df.isnull().sum()}")

        # -------------------------------
        # Business Logic
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

        logger.info("Business calculations completed")

        # -------------------------------
        # Summary Tables
        # -------------------------------
        portfolio_summary = pd.DataFrame({
            "Total_Investment": [df["Investment_Value"].sum()],
            "Total_Current_Value": [df["Current_Value"].sum()],
            "Net_Profit_Loss": [df["Profit_Loss"].sum()]
        })

        sector_summary = (
            df.groupby("Sector", as_index=False)["Profit_Loss"].sum()
        )

        # -------------------------------
        # Write Output Excel
        # -------------------------------
        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Detailed_Stock_Data", index=False)
            portfolio_summary.to_excel(
                writer, sheet_name="Portfolio_Summary", index=False
            )
            sector_summary.to_excel(
                writer, sheet_name="Sector_Summary", index=False
            )

        logger.info("Output Excel file generated successfully")
        logger.info("===== PROCESS COMPLETED =====")

        # -------------------------------
        # UI Success
        # -------------------------------
        st.success("✅ Report and process log generated successfully!")

        with open(output_file, "rb") as f:
            st.download_button(
                "⬇️ Download MI Output Excel",
                f,
                file_name=os.path.basename(output_file)
            )

        with open(log_file, "rb") as f:
            st.download_button(
                "⬇️ Download Process Log",
                f,
                file_name=os.path.basename(log_file)
            )

    except Exception as e:
        logger.exception("Process failed due to error")
        st.error("❌ Processing failed. Please download and check the process log.")
