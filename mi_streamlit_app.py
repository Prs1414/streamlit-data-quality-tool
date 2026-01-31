import streamlit as st
import pandas as pd
import logging
from io import BytesIO

# ---------------------------------
# Page config
# ---------------------------------
st.set_page_config(
    page_title="Data Quality Tool",
    layout="wide"
)

st.title("📊 Data Quality Automation Tool")
st.write("Upload Excel file to process data quality checks and generate output.")

# ---------------------------------
# Logger configuration
# ---------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------------------------
# File uploader
# ---------------------------------
uploaded_file = st.file_uploader(
    "📤 Upload Excel file (.xlsx only)",
    type=["xlsx"]
)

# ---------------------------------
# Main processing
# ---------------------------------
if uploaded_file is not None:
    try:
        # ✅ Explicit engine to avoid cloud errors
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        st.subheader("📄 Uploaded Data Preview")
        st.dataframe(df.head())

        # ---------------------------------
        # Required columns check
        # ---------------------------------
        required_columns = [
            "Buy_Price",
            "Current_Price",
            "Quantity",
            "Risk_Level",
            "Sector"
        ]

        missing_columns = [c for c in required_columns if c not in df.columns]

        if missing_columns:
            st.error(f"❌ Missing required columns: {missing_columns}")
            st.stop()

        # ---------------------------------
        # Data type handling
        # ---------------------------------
        numeric_columns = ["Buy_Price", "Current_Price", "Quantity"]

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # ---------------------------------
        # Business calculations
        # ---------------------------------
        df["Investment_Value"] = df["Buy_Price"].fillna(0) * df["Quantity"].fillna(0)
        df["Current_Value"] = df["Current_Price"].fillna(0) * df["Quantity"].fillna(0)
        df["Profit_Loss"] = df["Current_Value"] - df["Investment_Value"]

        df["Status"] = df["Profit_Loss"].apply(
            lambda x: "Profit" if x > 0 else "Loss"
        )

        df["High_Risk_Flag"] = df["Risk_Level"].astype(str).str.lower().apply(
            lambda x: "Yes" if x == "high" else "No"
        )

        st.success("✅ File processed successfully")

        # ---------------------------------
        # Display processed data
        # ---------------------------------
        st.subheader("📈 Processed Data")
        st.dataframe(df)

        # ---------------------------------
        # Download output
        # ---------------------------------
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Processed_Data")

        output.seek(0)

        st.download_button(
            label="⬇️ Download Processed Excel",
            data=output,
            file_name="processed_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        logging.error("Processing failed", exc_info=True)
        st.error("❌ Processing failed. Error details below:")
        st.exception(e)
