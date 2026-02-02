import streamlit as st
import pandas as pd
import logging
import os
from datetime import datetime

# ---------------------------------
# App UI
# ---------------------------------
st.set_page_config(
    page_title="MI Data Quality Tool",
    layout="centered"
)

st.title("📊 MI Data Quality & Reporting Tool")
st.write("Upload stock data Excel file and generate MI report with process log.")

# ---------------------------------
# Folder setup
# ---------------------------------
base_folder = "app_output"
output_folder = os.path.join(base_folder, "output")
log_folder = os.path.join(base_folder, "logs")

os.makedirs(output_folder, exist_ok=True)
os.makedirs(log_folder, exist_ok=True)

# ---------------------------------
# File uploader
# ---------------------------------
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# ---------------------------------
# Run button
# ---------------------------------
if uploaded_file and st.button("🚀 Run Report"):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = os.path.join(
        output_folder,
        f"stocks_mi_output_{timestamp}.xlsx"
    )

    log_file = os.path.join(
        log_folder,
        f"data_process_{timestamp}.log"
    )

    # ---------------------------------
    # Custom Logger (Streamlit Cloud Safe)
    # ---------------------------------
    logger = logging.getLogger("mi_logger")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.info("===== PROCESS STARTED =====")

    try:
        # ---------------------------------
        # Read Excel
        # ---------------------------------
        df = pd.read_excel(uploaded_file)
        logger.info(f"Rows read: {len(df)}")

        # ---------------------------------
        # Column validation
        # ---------------------------------
        required_columns = [
            "Buy_Price",
            "Quantity",
            "Current_Price",
            "Risk_Level",
            "Sector"
        ]

        missing_cols = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            st.error(f"❌ Missing columns: {missing_cols}")
            st.stop()

        # ---------------------------------
        # Data Quality Checks
        # ---------------------------------
        logger.info("Running data quality checks")
        logger.info(f"Null counts:\n{df.isnull().sum()}")

        # ---------------------------------
        # Business Calculations
        # ---------------------------------
        df["Investment_Value"] = df["Buy_Price"] * df["Quantity"]
        df["Current_Value"] = df["Current_Price"] * df["Quantity"]
        df["Profit_Loss"] = (
            df["Current_Value"] - df["Investment_Value"]
        )

        df["Status"] = df["Profit_Loss"].apply(
            lambda x: "Profit" if x > 0 else "Loss"
        )

        df["High_Risk_Flag"] = df["Risk_Level"].apply(
            lambda x: "Yes"
            if str(x).lower() == "high"
            else "No"
        )

        logger.info("Business calculations completed")

        # ---------------------------------
        # Summary Tables
        # ---------------------------------
        portfolio_summary = pd.DataFrame({
            "Total_Investment": [
                df["Investment_Value"].sum()
            ],
            "Total_Current_Value": [
                df["Current_Value"].sum()
            ],
            "Net_Profit_Loss": [
                df["Profit_Loss"].sum()
            ]
        })

        sector_summary = (
            df.groupby("Sector", as_index=False)
              ["Profit_Loss"].sum()
        )

        logger.info("Summary tables created")

        # ---------------------------------
        # Write Output Excel
        # ---------------------------------
        with pd.ExcelWriter(
            output_file,
            engine="xlsxwriter"
        ) as writer:
            df.to_excel(
                writer,
                sheet_name="Detailed_Stock_Data",
                index=False
            )
            portfolio_summary.to_excel(
                writer,
                sheet_name="Portfolio_Summary",
                index=False
            )
            sector_summary.to_excel(
                writer,
                sheet_name="Sector_Summary",
                index=False
            )

        logger.info("Output Excel generated successfully")
        logger.info("===== PROCESS COMPLETED =====")

        # ---------------------------------
        # Flush & Close Logger (CRITICAL)
        # ---------------------------------
        for handler in logger.handlers:
            handler.flush()
            handler.close()

        st.success("✅ Report generated successfully!")

        # ---------------------------------
        # Log Preview in UI
        # ---------------------------------
        with open(log_file, "r") as f:
            log_text = f.read()

        st.subheader("📄 Process Log Preview")
        st.text_area(
            "Log details",
            log_text,
            height=300
        )

        # ---------------------------------
        # Download Buttons
        # ---------------------------------
        with open(output_file, "rb") as f:
            st.download_button(
                label="⬇️ Download MI Output Excel",
                data=f,
                file_name=os.path.basename(output_file)
            )

        with open(log_file, "rb") as f:
            st.download_button(
                label="⬇️ Download Process Log",
                data=f,
                file_name=os.path.basename(log_file)
            )

    except Exception as e:
        logger.error(
            "Process failed",
            exc_info=True
        )

        for handler in logger.handlers:
            hand
