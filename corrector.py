import pandas as pd
import re
from difflib import get_close_matches
from validator_core import MasterData, normalize_text, clean_value

MASTER_FILE = "SBM-Master-Lists.xlsx"


# ---------- LOG ---------- #
def log(msg):
    print(f"[CORRECTOR] {msg}")


# ---------- HELPERS ---------- #
def best_match(value, master_set):
    matches = get_close_matches(value, master_set, n=1, cutoff=0.7)
    return matches[0] if matches else None


def fix_gender(val):
    val = str(val).strip().upper()
    if val in ["M", "MALE"]:
        return "Male"
    if val in ["F", "FEMALE"]:
        return "Female"
    return val


def fix_mobile(val):
    val = re.sub(r"\D", "", str(val))
    if val.startswith("91") and len(val) == 12:
        val = val[2:]
    return val


def fix_email(val):
    return str(val).strip()


def fix_blood(val):
    val = str(val).strip().upper()
    return val


def fix_text(val):
    return str(val).strip()


# ---------- MAIN ---------- #
def main():
    print("\n🚀 SBM CORRECTOR STARTED\n")

    file_path = input("📂 Enter Excel file path: ").strip()

    log("Loading master...")
    master = MasterData(MASTER_FILE)
    master.load()

    log("Reading file...")
    df = pd.read_excel(file_path)

    changes = 0

    for idx, row in df.iterrows():
        row_num = idx + 2
        log(f"\n🔧 Processing Row {row_num}")

        # ---------- BASIC CLEAN ---------- #
        for col in df.columns:
            original = row[col]
            cleaned = clean_value(original)

            if str(original) != str(cleaned):
                df.at[idx, col] = cleaned
                changes += 1
                log(f"{col}: cleaned '{original}' → '{cleaned}'")

        # ---------- GENDER ---------- #
        g = fix_gender(row.get("Gender", ""))
        if g != row.get("Gender"):
            df.at[idx, "Gender"] = g
            changes += 1
            log(f"Gender fixed → {g}")

        # ---------- MOBILE ---------- #
        m = fix_mobile(row.get("Mobile No", ""))
        if m != str(row.get("Mobile No")):
            df.at[idx, "Mobile No"] = m
            changes += 1
            log(f"Mobile fixed → {m}")

        # ---------- EMAIL ---------- #
        email = fix_email(row.get("Email Id", ""))
        if email != row.get("Email Id"):
            df.at[idx, "Email Id"] = email
            changes += 1

        # ---------- BLOOD ---------- #
        blood = fix_blood(row.get("Blood Group", ""))
        if blood != row.get("Blood Group"):
            df.at[idx, "Blood Group"] = blood
            changes += 1

        # ---------- SKILLS ---------- #
        for col in ["Skills - 1", "Skills 2"]:
            val = normalize_text(row.get(col, ""))
            if not val:
                continue

            if val not in master.skills:
                suggestion = best_match(val, master.skills)
                if suggestion:
                    df.at[idx, col] = suggestion
                    changes += 1
                    log(f"{col}: '{val}' → '{suggestion}'")
                else:
                    log(f"{col}: No match for '{val}' (manual check needed)")

        # ---------- QUALIFICATION ---------- #
        qual = normalize_text(row.get("Educational Qualification", ""))
        if qual and qual not in master.qualifications:
            suggestion = best_match(qual, master.qualifications)
            if suggestion:
                df.at[idx, "Educational Qualification"] = suggestion
                changes += 1
                log(f"Qualification fixed → {suggestion}")

        # ---------- PROFESSION ---------- #
        prof = normalize_text(row.get("Profession", ""))
        if prof and prof not in master.professions:
            suggestion = best_match(prof, master.professions)
            if suggestion:
                df.at[idx, "Profession"] = suggestion
                changes += 1
                log(f"Profession fixed → {suggestion}")

        # ---------- CENTRE (NO AUTO CHANGE) ---------- #
        centre = normalize_text(row.get("Satsang Centre", ""))
        if centre not in master.centres:
            suggestion = best_match(centre, master.centres)
            log(f"⚠️ Centre '{centre}' invalid. Suggestion: {suggestion}")

    # ---------- SAVE ---------- #
    output_file = file_path.replace(".xlsx", "_corrected.xlsx")

    log(f"\n💾 Saving corrected file → {output_file}")
    df.to_excel(output_file, index=False)

    print(f"\n✅ DONE — {changes} corrections applied")
    print("👉 Re-run validator on corrected file\n")


if __name__ == "__main__":
    main()