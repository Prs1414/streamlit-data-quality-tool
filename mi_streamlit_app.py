import streamlit as st
import pandas as pd
import logging
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
# We create this outside the button logic so it's ready to catch logs
log_buffer = io.StringIO()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(log_buffer)],
    force=True # Ensures logs reset correctly on rerun
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
        # Note: requires 'openpyxl' in requirements.txt
        df = pd.read_excel(uploaded_file)
        logging.info(f"Rows read: {len(df)}")

        # -------------------------------
        # Data Quality Checks
        # -------------------------------
        logging.info("Running data quality checks")
        null_info = df.isnull().sum().to_string()
        logging.info(f"Null counts:\n{null_info}")

        # -------------------------------
        # Business Calculations
        # -------------------------------
        # Ensure columns exist before calculating to avoid KeyErrors
        required_cols = ["Buy_Price", "Quantity", "Current_Price", "Risk_Level", "Sector"]
        if all(col in df.columns for col in required_cols):
            
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
            # Success Message & Downloads
            # -------------------------------
            st.success("✅ Report generated successfully!")

            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="⬇️ Download MI Excel",
                    data=output_buffer,
                    file_name=f"stocks_mi_output_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col2:
                st.download_button(
                    label="⬇️ Download Process Log",
                    data=log_buffer.getvalue(),
                    file_name=f"data_process_{timestamp}.log",
                    mime="text/plain"
                )
        else:
            missing = [c for c in required_cols if c not in df.columns]
            st.error(f"Missing columns in Excel: {', '.join(missing)}")
            logging.error(f"Missing columns: {missing}")

    except Exception as e:
        logging.error("Process failed", exc_info=True)
        st.error("❌ Processing failed. Error details below:")
        st.exception(e)
