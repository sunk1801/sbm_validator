import streamlit as st
import pandas as pd
import os
import tempfile
import traceback
from pathlib import Path
from collections import Counter

from validator_core import MasterData, validate_file


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SBM Data Preparation Tool",
    page_icon="📋",
    layout="wide"
)

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MASTER_FILE = BASE_DIR / "master" / "SBM-Master-Lists.xlsx"

MAX_ROWS_PER_FILE = 500

# ============================================================
# CONSTANTS
# ============================================================

MAX_ROWS_PER_FILE = 500


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📋 SBM Data Preparation Tool")
st.caption("Sewa Badge Management — Data Validation & Preparation")

st.divider()

# ============================================================
# MASTER DATA STATUS
# ============================================================

st.header("1️⃣ SBM Master Data")

if not MASTER_FILE.exists():

    st.error(
        "❌ SBM Master Lists not found."
    )

    st.code(
        str(MASTER_FILE)
    )

    st.info(
        "Please place SBM-Master-Lists.xlsx inside the "
        "'master' folder."
    )

    st.stop()

else:

    st.success(
        "✅ SBM Master Lists loaded"
    )

    st.caption(
        f"Master file: {MASTER_FILE.name}"
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("⚙️ Configuration")

    st.info(
        "Upload the SBM Master Lists Excel file and one or more "
        "sewadar data Excel files."
    )

    st.markdown("### Validation Rules")

    st.write("✔ Maximum 500 records per sheet")
    st.write("✔ Mandatory field validation")
    st.write("✔ Mobile validation")
    st.write("✔ Aadhaar validation")
    st.write("✔ Date validation")
    st.write("✔ 20-year initiation rule")
    st.write("✔ Satsang Centre validation")
    st.write("✔ State validation")
    st.write("✔ Skills validation")
    st.write("✔ Qualification validation")
    st.write("✔ Profession validation")

    st.divider()

    st.caption("SBM Data Preparation Tool")

# ============================================================
# SEWADAR DATA
# ============================================================

st.header("2️⃣ Sewadar Data")

uploaded_files = st.file_uploader(
    "Upload one or more Sewadar Excel files",
    type=["xlsx"],
    accept_multiple_files=True,
    key="sewadar_files"
)


# ============================================================
# VALIDATE BUTTON
# ============================================================

st.divider()

start_validation = st.button(
    "🚀 Start Validation",
    type="primary",
    use_container_width=True
)


# ============================================================
# VALIDATION
# ============================================================

if start_validation:

    if not uploaded_files:
        st.error("❌ Please upload at least one Sewadar Excel file.")
        st.stop()

    st.header("3️⃣ Validation Progress")

    temp_dir = tempfile.mkdtemp(prefix="sbm_")

    master_path = str(MASTER_FILE)


    # --------------------------------------------------------
    # Load master
    # --------------------------------------------------------
    status = st.status(
        "🔄 Loading SBM Master Lists...",
        expanded=True
    )

    try:

        master = MasterData(master_path)
        master.load()

        status.update(
            label="✅ SBM Master Lists loaded successfully",
            state="complete"
        )

    except Exception as e:

        status.update(
            label="❌ Failed to load Master Lists",
            state="error"
        )

        st.error(str(e))

        with st.expander("Technical Details"):
            st.code(traceback.format_exc())

        st.stop()

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    progress_bar = st.progress(0)

    progress_text = st.empty()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_files = len(uploaded_files)

    processed_files = 0
    total_records = 0
    total_errors = 0

    all_errors = []

    # --------------------------------------------------------
    # Process each file
    # --------------------------------------------------------

    for file_index, uploaded_file in enumerate(uploaded_files, start=1):

        filename = uploaded_file.name

        progress_text.info(
            f"🔍 Processing file {file_index}/{total_files}: "
            f"**{filename}**"
        )

        # ----------------------------------------------------
        # Save uploaded file
        # ----------------------------------------------------

        file_path = os.path.join(
            temp_dir,
            filename
        )

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # ----------------------------------------------------
        # Read workbook for statistics
        # ----------------------------------------------------

        try:

            excel = pd.ExcelFile(file_path)

            file_record_count = 0

            for sheet in excel.sheet_names:

                # Master files should not normally be uploaded here
                # but reading every sheet makes this safer.

                try:

                    df = pd.read_excel(
                        file_path,
                        sheet_name=sheet
                    )

                    file_record_count += len(df)

                except Exception:
                    pass

            total_records += file_record_count

        except Exception:

            file_record_count = 0

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        try:

            errors = validate_file(
                file_path,
                master
            )

            # ------------------------------------------------
            # Store errors
            # ------------------------------------------------

            for row_number, error_message in errors:

                all_errors.append(
                    {
                        "File": filename,
                        "Row": row_number,
                        "Error": error_message
                    }
                )

            total_errors += len(errors)

            # ------------------------------------------------
            # File result
            # ------------------------------------------------

            if errors:

                st.error(
                    f"❌ {filename} — "
                    f"{len(errors)} issue(s)"
                )

            else:

                st.success(
                    f"✅ {filename} — CLEAN"
                )

        except Exception as e:

            error_message = str(e)

            all_errors.append(
                {
                    "File": filename,
                    "Row": "N/A",
                    "Error": f"Processing Error: {error_message}"
                }
            )

            total_errors += 1

            st.error(
                f"❌ {filename} — Validation failed"
            )

            with st.expander(
                f"Technical details — {filename}"
            ):
                st.code(
                    traceback.format_exc()
                )

        processed_files += 1

        progress_bar.progress(
            processed_files / total_files
        )

    # ========================================================
    # COMPLETE
    # ========================================================

    progress_text.success(
        "🎉 Validation completed successfully!"
    )

    st.divider()

    # ========================================================
    # DASHBOARD
    # ========================================================

    st.header("📊 Validation Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Files Processed",
            processed_files
        )

    with col2:
        st.metric(
            "Records",
            f"{total_records:,}"
        )

    with col3:
        st.metric(
            "Total Errors",
            f"{total_errors:,}"
        )

    with col4:

        clean_files = 0

        # Determine clean files from error list
        error_files = set(
            item["File"]
            for item in all_errors
        )

        clean_files = total_files - len(error_files)

        st.metric(
            "Clean Files",
            clean_files
        )

    # ========================================================
    # RESULTS
    # ========================================================

    if not all_errors:

        st.success(
            "🎉 ALL FILES ARE CLEAN — READY FOR SBM UPLOAD"
        )

        st.balloons()

    else:

        st.warning(
            f"⚠️ {total_errors:,} validation issues found."
        )

        # ----------------------------------------------------
        # Error dataframe
        # ----------------------------------------------------

        error_df = pd.DataFrame(
            all_errors
        )

        # ----------------------------------------------------
        # Error summary
        # ----------------------------------------------------

        st.subheader("📌 Error Summary")

        error_summary = (
            error_df
            .groupby("Error")
            .size()
            .reset_index(name="Count")
            .sort_values(
                "Count",
                ascending=False
            )
        )

        st.dataframe(
            error_summary,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # Detailed errors
        # ----------------------------------------------------

        st.subheader("🔎 Detailed Errors")

        st.dataframe(
            error_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )

        # ----------------------------------------------------
        # Excel report
        # ----------------------------------------------------

        report_path = os.path.join(
            temp_dir,
            "SBM_Validation_Report.xlsx"
        )

        with pd.ExcelWriter(
            report_path,
            engine="openpyxl"
        ) as writer:

            error_df.to_excel(
                writer,
                sheet_name="Detailed Errors",
                index=False
            )

            error_summary.to_excel(
                writer,
                sheet_name="Summary",
                index=False
            )

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        with open(report_path, "rb") as f:

            report_bytes = f.read()

        st.download_button(
            label="⬇️ Download Excel Error Report",
            data=report_bytes,
            file_name="SBM_Validation_Report.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True
        )

        st.divider()

        st.info(
            "💡 Fix the errors in the original Excel files and "
            "run the validation again. The validator does not "
            "modify your uploaded source files."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SBM Data Preparation Tool • "
    "Validation is performed against the uploaded SBM Master Lists."
)