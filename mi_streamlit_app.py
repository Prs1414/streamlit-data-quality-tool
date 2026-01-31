import streamlit as st
import pandas as pd
import logging
from io import BytesIO, StringIO
from datetime import datetime

# ---------------------------------
# Page config
# ---------------------------------
st.set_page_config(
    page_title="MI Data Quality Tool",
    layout="wide"
)

st.title("📊 MI Data Quality & Reporting Tool")
st.write("Upload stock data Excel file and generate MI report with process log.")

# ---------------------------------
# In-memory log setup
# ---------------------------------
log_stream = StringIO()

logger = logging.getLogger("mi_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ---------------------------------
# File uploader
# ---------------------------------
uploaded_file = st.file_uploader(
    "📂 Upload Excel File (.xlsx)",
    type=["xlsx"]
)

# ---------------------------------
# Run report
# ---------------------------------
if uploaded_file is not None and st.button("🚀 Run Report"):

    try:
        logger.info("===== PROCESS STARTED =====")

        # -------------------------------
        # Read Excel
        # -------------------------------
        df = pd.read_excel(uploaded_file, engine="openpyxl")
        logger.info(f"Rows read: {len(df)}")

        # -------------------------------
        # Required column validation
        # -------------------------------
        required_columns = [
            "Buy_Price",
            "Current_Price",
            "Quantity",
            "Risk_Level",
            "Sector"
        ]

        missing_cols = [c for c in required_columns if c not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns: {missing_cols}")
            st.error(f"❌ Missing required columns: {missing_cols}")
            st.stop()

        # -------------------------------
        # Data type handling
        # -------------------------------
        for col in ["Buy_Price", "Current_Price", "Quantity"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        logger.info("Data type conversion completed")

        # -------------------------------
        # Business logic
        # -------------------------------
        df["Investment_Value"] = df["Buy_Price"].fillna(0) * df["Quantity"].fillna(0)
        df["Current_Value"] = df["Current_Price"].fillna(0) * df["Quantity"].fillna(0)
        df["Profit_Loss"] = df["Current_Value"] - df["Investment_Value"]

        df["Status"] = df["Profit_Loss"].apply(
            lambda x: "Profit" if x > 0 else "Loss"
        )

        df["High_Risk_Flag"] = df["Risk_Level"].astype(str).str.lower().apply(
            lambda x: "Yes" if x == "high" else "No"
        )

        logger.info("Business calculations completed")

        # -------------------------------
        # Summary tables
        # -------------------------------
        portfolio_summary = pd.DataFrame({
            "Total_Investment": [df["Investment_Value"].sum()],
            "Total_Current_Value": [df["Current_Value"].sum()],
            "Net_Profit_Loss": [df["Profit_Loss"].sum()]
        })

        sector_summary = df.groupby("Sector", as_index=False)["Profit_Loss"].sum()

        # -------------------------------
        # Create output Excel (IN MEMORY)
        # -------------------------------
        excel_buffer = BytesIO()

        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Detailed_Stock_Data", index=False)
            portfolio_summary.to_excel(writer, sheet_name="Portfolio_Summary", index=False)
            sector_summary.to_excel(writer, sheet_name="Sector_Summary", index=False)

        excel_buffer.seek(0)
        logger.info("Excel output generated")

        logger.info("===== PROCESS COMPLETED =====")

        # -------------------------------
        # UI output
        # -------------------------------
        st.success("✅ Report and process log generated successfully!")

        st.subheader("📈 Processed Data Preview")
        st.dataframe(df.head())

        st.download_button(
            label="⬇️ Download MI Output Excel",
            data=excel_buffer,
            file_name=f"stocks_mi_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="⬇️ Download Process Log",
            data=log_stream.getvalue(),
            file_name="data_process.log",
            mime="text/plain"
        )

    except Exception as e:
        logger.exception("Process failed due to error")
        st.error("❌ Processing failed. See error details below.")
        st.exception(e)
