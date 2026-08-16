import os
import pandas as pd
from collections import defaultdict
from validator_core import MasterData, validate_file

MASTER_FILE = BASE_DIR / "master" / "SBM-Master-Lists.xlsx"
INPUT_FOLDER = "input_files"
OUTPUT_FILE = "validation_errors.xlsx"


def print_summary(errors):
    print("\n📊 ERROR SUMMARY:\n")

    summary = defaultdict(int)

    for _, err in errors:
        summary[err] += 1

    for k, v in sorted(summary.items(), key=lambda x: -x[1]):
        print(f"   {v} × {k}")


def main():
    print("\n🚀 SBM VALIDATION STARTED\n")

    master = MasterData(MASTER_FILE)
    master.load()

    print("\n📂 Scanning input folder...\n")

    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".xlsx")]

    if not files:
        print("❌ No Excel files found")
        return

    all_error_rows = []

    for file in files:
        print("\n" + "="*50)
        print(f"🔍 Validating: {file}")
        print("="*50)

        path = os.path.join(INPUT_FOLDER, file)

        errors = validate_file(path, master)

        # 🔴 HARD STOP
        if errors and errors[0][0] == "STRUCTURE":
            print("\n🚫 CRITICAL ERROR:")
            print(f"   {errors[0][1]}")
            print("   👉 Fix this FIRST\n")

            all_error_rows.append({
                "File": file,
                "Row": "N/A",
                "Error": errors[0][1]
            })
            continue

        if not errors:
            print("\n✅ File is CLEAN — Ready for SBM upload\n")
            continue

        print(f"\n❌ Found {len(errors)} issues\n")

        print("🔎 SAMPLE ERRORS:\n")
        for err in errors[:15]:
            print("   ", err)

        if len(errors) > 15:
            print(f"\n   ... {len(errors) - 15} more errors not shown")

        print_summary(errors)

        # 🔥 ADD TO EXCEL REPORT
        for row_num, err in errors:
            all_error_rows.append({
                "File": file,
                "Row": row_num,
                "Error": err
            })

        print("\n⚠️ ACTION:")
        print("   1. Fix STRUCTURE errors first")
        print("   2. Then fix Aadhaar / Dates")
        print("   3. Then fix master mismatches")
        print("   4. Re-run validation\n")

    # ---------- SAVE EXCEL ---------- #
    if all_error_rows:
        df = pd.DataFrame(all_error_rows)

        # Summary sheet
        summary = df.groupby("Error").size().reset_index(name="Count")

        with pd.ExcelWriter(OUTPUT_FILE) as writer:
            df.to_excel(writer, sheet_name="Detailed Errors", index=False)
            summary.to_excel(writer, sheet_name="Summary", index=False)

        print("\n📁 ERROR REPORT GENERATED:")
        print(f"   👉 {OUTPUT_FILE}\n")

    else:
        print("\n✅ No errors found across all files\n")

    print("\n✅ VALIDATION COMPLETE\n")


if __name__ == "__main__":
    main()