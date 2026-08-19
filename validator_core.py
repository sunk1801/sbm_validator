import pandas as pd
import re
import unicodedata
from datetime import datetime
from difflib import get_close_matches

# ---------- LOG ---------- #
def log(msg):
    print(f"[VALIDATOR] {msg}")

# ---------- CLEANERS ---------- #
def clean_value(val):
    if pd.isna(val):
        return ""
    val = str(val).strip()
    if val.lower() in ["nan", "none", ""]:
        return ""
    return val

def normalize_text(val):
    val = str(val)
    val = unicodedata.normalize("NFKC", val)
    val = val.strip().upper()
    val = " ".join(val.split())
    return val

# ---------- BASIC VALIDATORS ---------- #
def validate_gender(val):
    return val in ["Male", "Female", "M", "F"]

def normalize_mobile(num):
    if pd.isna(num):
        return ""

    num = str(num).strip()

    # 🔥 FIX: handle float-like strings
    if re.fullmatch(r"\d+\.0", num):
        num = num[:-2]  # remove .0 safely

    # 🔥 handle scientific notation
    elif "E" in num or "e" in num:
        try:
            num = str(int(float(num)))
        except:
            return ""

    # remove non-digits
    num = re.sub(r"\D", "", num)

    # remove country code
    if num.startswith("91") and len(num) == 12:
        num = num[2:]

    return num


def is_valid_mobile(num):
    num = normalize_mobile(num)

    return len(num) == 10 and num[0] in "6789"


# ---------- DATE HANDLING ---------- #
def parse_date(val):
    import pandas as pd
    from datetime import datetime

    if pd.isna(val):
        return None

    # Case 1: Already datetime
    if isinstance(val, (datetime, pd.Timestamp)):
        return val

    val = str(val).strip()

    # Try multiple formats
    formats = [
        "%d-%b-%y",   # 18-Jan-92
        "%d-%b-%Y",   # 18-Jan-1992
        "%Y-%m-%d",   # 1992-01-18
    ]

    for fmt in formats:
        try:
            return datetime.strptime(val, fmt)
        except:
            continue

    # Final fallback (very important)
    try:
        return pd.to_datetime(val, errors="coerce")
    except:
        return None


def validate_dates(dob_raw, init_raw):
    errors = []

    dob = parse_date(dob_raw)
    init = parse_date(init_raw)

    reference_date = datetime(2026, 12, 31)

    if dob is None or pd.isna(dob):
        errors.append("Invalid Birth Date format (expected dd-MMM-yy)")
        return errors

    # Validate initiation format
    if pd.notna(init):
        try:
            pd.to_datetime(init, format="%d-%b-%y")
        except ValueError:
            errors.append("Invalid Initiation Date format (expected dd-MMM-yy)")

    if dob >= datetime.today():
        errors.append("Birth Date cannot be in future")

    # 🔥 AGE CHECK AS OF 31-DEC-2026
    age_on_ref = int((reference_date - dob).days / 365.25)

    if age_on_ref < 18:
        errors.append(f"Age is {age_on_ref} as of 31-Dec-2026 (must be 18+)")
    elif age_on_ref >= 70:
        errors.append(f"Age is {age_on_ref} as of 31-Dec-2026 (must be < 70)")

    # 🔥 20 YEAR RULE
    try:
        min_init = dob.replace(year=dob.year + 22)
    except:
        min_init = dob

    age_at_init = None
    try:
        age_at_init = int((init - dob).days / 365.25)
    except:
        pass

    if init < min_init:
        if age_at_init is not None:
            errors.append(f"Initiation too early (Age: {age_at_init}, required: 22+)")
        else:
            errors.append("Initiation Date must be at least 22 years after Birth Date")

    return errors


# ---------- AADHAAR (VERHOEFF) ---------- #
d_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0]
]

p_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8]
]

def verhoeff_check(num):
    c = 0
    num = list(map(int, reversed(num)))
    for i, digit in enumerate(num):
        c = d_table[c][p_table[i % 8][digit]]
    return c == 0


def is_valid_aadhaar(num):
    num = str(num).strip()

    # Full Aadhaar: 12 digits + Verhoeff
    if re.fullmatch(r"\d{12}", num):
        return verhoeff_check(num)

    # Masked Aadhaar: exactly 4 visible digits
    # Leading zeros are valid, e.g. 0123, 0012, 0001
    if re.fullmatch(r"\d{4}", num):
        return True

    # Masked formats: XXXXXXXX1234 / ********1234
    # Last 4 digits may include leading zeros
    if re.fullmatch(r"(?:X{8}|\*{8})\d{4}", num, re.IGNORECASE):
        return True

    return False


# ---------- OTHER VALIDATIONS ---------- #
def is_valid_name(name, mandatory=True, words=None, min_words=None, max_words=None):
    name = clean_value(name)

    if not name:
        return not mandatory

    parts = name.split()

    # Exact word count
    if words is not None:
        if len(parts) != words:
            return False

    # Minimum word count
    if min_words is not None and len(parts) < min_words:
        return False

    # Maximum word count
    if max_words is not None and len(parts) > max_words:
        return False

    pattern = r"^[A-Z][a-zA-Z'-]*$"

    return all(re.fullmatch(pattern, part) for part in parts)

def is_valid_photo(photo):
    photo = clean_value(photo)

    if photo == "":
        return False

    return photo.lower().endswith(".jpg")


def is_valid_email(email):
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))


VALID_BLOOD = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


def validate_address(addr):
    errors = []
    if len(addr) > 75:
        errors.append("Address exceeds 75 characters")

    if re.search(r"\d{6}", addr):
        errors.append("Address should not contain PIN")

    return errors


def is_valid_pin(pin):

    if pin == "":
        return True

    pin_str = str(pin)
    if re.fullmatch(r"\d{6}", pin_str):
        return True
    else:
        return False


# ---------- MASTER LOADER ---------- #
class MasterData:
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        print("[MASTER LOAD] Loading master...")

        xls = pd.ExcelFile(self.file_path)

        skills_df = pd.read_excel(xls, "Skills")
        self.skills = set(
            skills_df["Skill Name"].astype(str).str.strip().str.upper()
        )

        qual_df = pd.read_excel(xls, "Qualification")
        self.qualifications = set(
            qual_df["Qualification Name"].astype(str).str.strip().str.upper()
        )

        prof_df = pd.read_excel(xls, "Profession")
        self.professions = set(
            prof_df["Profession Name"].astype(str).str.strip().str.upper()
        )

        centres_df = pd.read_excel(xls, "Satsang Centres")

        # 🔴 STRICT COLUMN NAMES (ADJUST ONLY IF NEEDED)
        centre_col = "Centre Name"
        state_col = "State"

        if centre_col not in centres_df.columns:
            raise Exception("❌ 'Centre Name' column missing in master")

        centres_df["CENTRE"] = centres_df[centre_col].apply(normalize_text)
        centres_df["STATE"] = centres_df[state_col].apply(normalize_text)

        self.centres = set(centres_df["CENTRE"])
        self.centre_state_map = dict(zip(centres_df["CENTRE"], centres_df["STATE"]))

        print(f"[MASTER LOAD] Centres loaded: {len(self.centres)}")


# ---------- ROW VALIDATION ---------- #
def validate_row(row, master, row_num):
    errors = []

    def val(col): return clean_value(row.get(col, ""))

    # Names
    # First Name (Mandatory, 1 word)
    if not is_valid_name(val("First Name"), mandatory=True, words=1):
        errors.append("Invalid First Name")

    # Last Name (Optional, 1 word)
    if not is_valid_name(val("Last Name"), mandatory=False, words=1):
        errors.append("Invalid Last Name")

    # Father Name (Mandatory, 2–3 words)
    if not is_valid_name(val("Father Name"), mandatory=True, min_words=1, max_words=3):
        errors.append("Invalid Father Name")

    # Spouse Name (Optional, 2 words)
    if not is_valid_name(
        val("Spouse Name"),
        mandatory=False,
        min_words=1,
        max_words=3
    ):
        errors.append("Invalid Spouse Name")

    if not is_valid_photo(val("Photo File Name")):
        errors.append("Invalid Photo File Name")

    # Gender
    if not validate_gender(val("Gender")):
        errors.append("Invalid Gender")

    # Aadhaar
    if not is_valid_aadhaar(val("Aadhaar No")):
        errors.append("Invalid Aadhaar")

    # Mobile
    if not is_valid_mobile(val("Mobile No")):
        errors.append("Invalid Mobile")

    # Dates
    errors.extend(validate_dates(val("Birth Date"), val("Initiation Date")))

    # Centre
    centre = normalize_text(val("Satsang Centre"))
    state = normalize_text(val("State"))

    if centre not in master.centres:
        errors.append(f"Invalid Centre: {centre}")
    elif state != master.centre_state_map.get(centre):
        errors.append("State mismatch with centre")

    # Address
    errors.extend(validate_address(val("Address Line 1")))
    if val("Address Line 2"):
        errors.extend(validate_address(val("Address Line 2")))

    # Pin
    raw_pin = val("Pin Code")

    # Normalize
    if raw_pin is not None:
        pin_str = str(raw_pin).strip()
        
        # Remove Excel float artifact like '462003.0'
        if pin_str.endswith(".0"):
            pin_str = pin_str[:-2]
    else:
        pin_str = ""

    # Validate
    if not is_valid_pin(pin_str):
        errors.append(f"Invalid Pin Code: {raw_pin}")

    # Email
    if val("Email Id") and not is_valid_email(val("Email Id")):
        errors.append("Invalid Email")

    # Blood
    blood = val("Blood Group").upper()
    if blood and blood not in VALID_BLOOD:
        errors.append("Invalid Blood Group")

    # Skills
    for col in ["Skills - 1", "Skills 2"]:
        skill = normalize_text(val(col))
        if skill and skill not in master.skills:
            errors.append(f"{col} invalid")

    # Qualification
    qual = normalize_text(val("Educational Qualification"))
    if qual and qual not in master.qualifications:
        errors.append("Invalid Qualification")

    # Profession
    prof = normalize_text(val("Profession"))
    if prof and prof not in master.professions:
        errors.append("Invalid Profession")

    return errors


# ---------- FILE VALIDATION ---------- #
def validate_file(file_path, master):
    df = pd.read_excel(file_path)

    errors = []

    # Hard stop
    if df.isnull().all(axis=1).any():
        return [("STRUCTURE", "Blank row found — SBM will cut data")]

    # S No
    if list(df["S No"]) != list(range(1, len(df) + 1)):
        errors.append(("STRUCTURE", "S No not sequential"))

    # Duplicate Aadhaar
    if df["Aadhaar No"].duplicated().any():
        errors.append(("STRUCTURE", "Duplicate Aadhaar found"))

    for idx, row in df.iterrows():
        row_errors = validate_row(row, master, idx + 2)
        for err in row_errors:
            errors.append((idx + 2, err))

    return errors
