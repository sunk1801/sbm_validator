# SBM Data Preparation Tool

A Python + Streamlit application for preparing, validating, correcting, and splitting Sewadar data for upload into the Sewa Badge Management (SBM) system.

The tool is designed for State and Area IT Teams and is intended to reduce manual Excel checking, identify validation errors early, and make large-volume SBM data preparation manageable.

---

## 1. Purpose

Beas HQ requires Sewadar data to be prepared in a specific Excel format before it can be uploaded into SBM.

This project provides an automated workflow around the SBM data-preparation process.

The application is designed to help with:

- Excel structure validation
- Mandatory-field validation
- Name validation
- Gender validation
- Birth Date validation
- Initiation Date validation
- Minimum 20-year age-at-initiation validation
- Aadhaar validation
- Mobile number validation
- Satsang Centre validation
- State validation
- Optional master-list validation
- Address length validation
- Email validation
- PIN-code validation
- Photo filename validation
- Photo-file validation where implemented
- Large-file splitting
- Automatic corrections where a correction is unambiguous
- Excel error reporting
- Streamlit-based user interface

---

# 2. Project Structure

Recommended project structure:

```text
SBM Project/
│
├── app.py
├── validator_core.py
├── corrector.py
├── corrector_core.py
├── splitter.py
├── splitter_core.py
│
├── SBM-Master-Lists.xlsx
├── requirements.txt
├── README.md
│
├── input_files/
├── output_files/
├── split_files/
└── reports/
```

Not every deployment needs every folder. The important point is that the validation rules should remain in the core modules and the Streamlit application should act as the user interface.

---

# 3. Main Components

## 3.1 `app.py`

This is the Streamlit user interface.

It allows the user to:

1. Upload the SBM Master Lists workbook.
2. Upload one or more Sewadar Excel files.
3. Start validation.
4. View processing progress.
5. View file-level results.
6. View total records and errors.
7. View an error summary.
8. View detailed row-level errors.
9. Download the consolidated Excel error report.

Run it using:

```bash
streamlit run app.py
```

---

## 3.2 `validator_core.py`

This contains the actual SBM validation rules.

The Streamlit application should call this module rather than duplicating validation logic inside `app.py`.

Typical structure:

```text
MasterData
    ↓
load master Excel
    ↓
normalize master values
    ↓
validate_file()
    ↓
validate_row()
    ↓
individual validation functions
```

This separation is important.

If an SBM rule changes, update the validation core rather than rewriting the Streamlit application.

---

## 3.3 `corrector.py` / `corrector_core.py`

The Corrector is intended to automatically fix only those problems where the correct action is unambiguous.

Examples of safe corrections include:

- Removing leading/trailing spaces
- Normalizing repeated spaces
- Converting obvious Excel `.0` numeric representations
- Normalizing certain text casing
- Normalizing mobile number formatting when the underlying number is unambiguous
- Standardizing clearly recognizable date representations
- Cleaning empty/NaN values

The corrector must NOT silently guess values for:

- Aadhaar
- Names
- Satsang Centre
- State
- District
- City
- Qualification
- Profession
- Skills
- Any other identity/master-data field where multiple possible corrections exist

If a value is ambiguous, it should be reported to the user rather than guessed.

---

## 3.4 `splitter.py` / `splitter_core.py`

The splitter is intended for large datasets.

SBM allows a maximum of 500 data rows per sheet.

For example:

```text
50,000 records
       ↓
500 records/file
       ↓
100 Excel files
```

The splitter should:

- Preserve the Excel header
- Keep each output file within the configured maximum
- Preserve all columns
- Avoid blank rows
- Maintain the correct S No sequence within each output file if that is the required submission convention
- Produce clearly numbered output files

Recommended naming:

```text
chunk_001.xlsx
chunk_002.xlsx
chunk_003.xlsx
...
```

---

# 4. SBM Master Lists

The project uses:

```text
SBM-Master-Lists.xlsx
```

The workbook contains separate sheets for master data.

Known sheets include:

```text
Skills
Qualification
Profession
Satsang Centres
```

## Important Satsang Centre rule

The `Satsang Centres` sheet contains fields such as:

- Centre
- State
- Area
- Centre Type

For centre validation, **Area and Centre Type are not used to determine whether the centre exists**.

The centre must be matched against the actual Centre value.

The State must then be checked against the State associated with that Centre.

For example:

```text
404    INDORE    MADHYA PRADESH    INDORE    MAJOR CENTRE
```

The relevant centre is:

```text
INDORE
```

and the associated state is:

```text
MADHYA PRADESH
```

The application must not accidentally treat `Centre Type` as the centre name.

This distinction is important because using `Centre Type` would produce incorrect results such as:

```text
POINT
SUB CENTRE
CENTRE
MAJOR CENTRE
```

instead of actual centre names.

---

# 5. Excel Input Rules

## Maximum rows

Maximum:

```text
500 records per sheet
```

The header is not counted as a data record.

Therefore:

```text
Row 1     = Header
Rows 2-501 = Maximum 500 records
```

---

## Blank rows

Blank rows must not occur between data records.

Example of invalid structure:

```text
Row 2   Sewadar
Row 3   Sewadar
Row 4   BLANK
Row 5   Sewadar
```

SBM may stop reading at the blank row.

The validator therefore treats unexpected blank rows as a structural problem.

---

## Headers

Do not:

- Rename columns
- Delete columns
- Rearrange columns
- Add unrelated columns

The workbook should follow the SBM template.

---

# 6. Validation Rules

The validator should implement the following rules.

## A — S No

Rules:

- Mandatory
- Sequential
- Starts from 1
- No gaps
- No duplicate sequence numbers

Example:

```text
1
2
3
4
5
```

Invalid:

```text
1
2
4
5
```

---

## B — First Name

Rules:

- Mandatory
- Proper case
- One word
- No abbreviations
- Should correspond to the person's Aadhaar/name record

Example:

```text
Suraj
```

Invalid:

```text
suraj
Suraj Kumar
S.
```

---

## C — Middle Name

Optional.

If provided, it should follow the agreed name-format rules.

---

## D — Last Name

Optional depending on the current project rule.

If provided:

- Proper case
- One word

Example:

```text
Khurana
```

---

## E — Gender

Accepted values:

```text
Male
Female
M
F
```

Other values should be rejected.

Examples of invalid values:

```text
male
MALE
Man
Woman
Unknown
```

---

# 7. Birth Date

Required format:

```text
dd-MMM-yy
```

Examples:

```text
18-Jan-92
15-Mar-73
01-Jan-00
```

Excel may internally store a date as:

```text
1992-01-18 00:00:00
```

That does not necessarily mean the displayed Excel date is wrong.

The validator should inspect the underlying Excel date appropriately rather than falsely rejecting a valid Excel date merely because pandas displays it as:

```text
1992-01-18 00:00:00
```

The validator should also check:

- Valid calendar date
- No future DOB
- Applicable SBM age restrictions

---

# 8. Aadhaar Number

Rules:

- Exactly 12 digits
- No `+91`
- No spaces
- No alphabetic characters
- Duplicate Aadhaar numbers should be identified
- Aadhaar checksum should be validated using the Verhoeff algorithm if implemented in the current validator

Do not silently modify Aadhaar numbers.

An ambiguous Aadhaar value must be manually corrected.

---

# 9. Mobile Number

Rules:

- Exactly 10 digits
- Must start with:
  - 6
  - 7
  - 8
  - 9
- No `+91` in the final stored value

Valid:

```text
9826383089
8109180927
9111996198
9009077909
```

### Excel `.0` handling

Excel/pandas can sometimes represent:

```text
9826383089
```

as:

```text
9826383089.0
```

The application may safely remove the trailing `.0` when the underlying value is clearly an integer.

It must NOT perform dangerous transformations such as:

```text
9826383089.0
→ 98263830890
→ 8263830890
```

Never blindly take the last 10 digits.

If a mobile value is ambiguous, flag it instead of modifying it.

---

# 10. Satsang Centre

The centre must exactly match the appropriate centre master value after safe normalization such as:

- Trim whitespace
- Normalize repeated spaces
- Case normalization for comparison

The validator should not invent a centre.

Example:

```text
INDORE
```

must match the actual `INDORE` centre in the master.

The State associated with the centre should also be checked.

---

# 11. Address

## Address Line 1

Maximum:

```text
75 characters
```

It should not contain unnecessary:

- State
- City
- PIN code

## Address Line 2

Maximum:

```text
75 characters
```

If the address exceeds 75 characters, split it appropriately between Line 1 and Line 2.

Do not arbitrarily cut words.

---

# 12. State

State must match the SBM master.

Use full names.

Correct:

```text
Madhya Pradesh
```

Not:

```text
MP
M.P.
mp
```

Matching should be done safely after normalization, but the submitted value should follow the required SBM spelling.

---

# 13. District and City

Where these fields are required by the SBM master/version being used:

```text
State → District → City
```

must form a valid combination.

The validator should not assume that a master workbook contains District and City if the current SBM master does not contain them.

For the current Satsang Centre master, the known fields are Centre, State, Area and Centre Type. Area and Centre Type should not be incorrectly used as District or City.

---

# 14. PIN Code

Rules:

- Exactly 6 digits
- Should correspond to the applicable State/District/City master where such a master is available
- If the team cannot verify the PIN, leaving it blank may be preferable to entering an incorrect value if permitted by the SBM template

Do not manufacture a PIN.

---

# 15. Initiation Date

Required format:

```text
dd-MMM-yy
```

Example:

```text
15-Mar-93
```

The initiation date must be valid.

## Minimum age rule

The Sewadar must have completed at least 20 years by the initiation date.

Example:

```text
DOB:              18-Jan-1992
Initiation Date:  17-Jan-2012
```

Age is still less than 20, therefore invalid.

If:

```text
DOB:              18-Jan-1992
Initiation Date:  18-Jan-2012
```

the person has completed 20 years.

### Error message

The validator should provide useful context.

Example:

```text
Initiation too early (Age: 19, required: 20+)
```

This is preferable to simply saying:

```text
Invalid Initiation Date
```

---

# 16. Father Name

Father Name is expected to be a full name.

Where the current project validation rule requires exactly two words:

```text
First Last
```

the validator should enforce that rule.

---

# 17. Spouse Name

Optional.

If provided and the current project rule requires two words, validate accordingly.

---

# 18. Skills

Columns:

```text
Skills - 1
Skills - 2
```

Values must come from:

```text
Skills
```

sheet of the master workbook.

If a Sewadar's skill is not available in the master:

```text
Leave blank
```

Do not invent a new skill.

---

# 19. Email

If populated:

- Must have a valid basic email structure
- Must not contain obvious spaces or malformed addresses

Example:

```text
user@example.com
```

Invalid:

```text
user
user@
@example.com
user @example.com
```

---

# 20. Educational Qualification

Must match:

```text
Qualification
```

sheet.

If no matching value exists:

```text
Leave blank
```

Do not enter a custom value.

---

# 21. Profession

Must match:

```text
Profession
```

sheet.

If no matching value exists:

```text
Leave blank
```

---

# 22. Designation

Designation must match the applicable SBM master where available.

If the correct designation is unknown:

```text
Leave blank
```

Do not guess.

---

# 23. Sewa Department

Columns:

```text
Sewa Dept - Local
Sewa Dept - Major Centre
```

Use recognized department names.

Examples:

```text
ADMINISTRATION
CANTEEN
```

The application should avoid automatically changing an ambiguous department.

---

# 24. Blood Group

Accepted values:

```text
A+
A-
B+
B-
AB+
AB-
O+
O
```

Any other value should be reported.

---

# 25. Remarks

Free text.

Keep it brief.

The validator should generally not reject legitimate remarks unless the SBM specification introduces a specific restriction.

---

# 26. Photo File Name

Example:

```text
3.jpg
```

Rules:

- JPG only
- Filename should correspond to the Excel record
- File should actually exist when photo-folder validation is enabled
- Maximum photo size should be checked where photo validation is implemented

---

# 27. Photo Requirements

Expected:

```text
JPG
Maximum 100 KB per photo
```

For scanned physical photographs:

```text
100–150 DPI
```

Recommended naming:

```text
1.jpg
2.jpg
3.jpg
...
```

Maximum:

```text
200 photos per folder
```

---

# 28. Validation Workflow

Recommended workflow:

```text
Raw Excel
   ↓
Corrector
   ↓
Splitter
   ↓
Validator
   ↓
Error Report
   ↓
Manual Correction
   ↓
Validator Again
   ↓
Clean Excel
   ↓
SBM Submission
```

For very large datasets:

```text
50,000 records
       ↓
Split into 500-record files
       ↓
Validate all files
       ↓
Consolidated error report
       ↓
Correct affected records
       ↓
Validate again
       ↓
Submit
```

---

# 29. Streamlit Workflow

Launch:

```bash
streamlit run app.py
```

The browser application provides:

### Step 1

Upload:

```text
SBM-Master-Lists.xlsx
```

### Step 2

Upload one or more Sewadar Excel files.

### Step 3

Click:

```text
Start Validation
```

### Step 4

The application:

1. Loads the master
2. Reads each uploaded workbook
3. Runs validation
4. Tracks progress
5. Displays file-level results
6. Builds a consolidated error list

### Step 5

Download:

```text
SBM_Validation_Report.xlsx
```

---

# 30. Error Report

The generated report contains:

## Detailed Errors

Columns:

```text
File
Row
Error
```

Example:

```text
chunk_003.xlsx | 127 | Invalid Mobile
chunk_003.xlsx | 245 | Invalid Centre: INDORE
chunk_004.xlsx | 51  | Initiation too early (Age: 19, required: 20+)
```

## Summary

Example:

```text
Error                                      Count
------------------------------------------------
Invalid Mobile                              42
Invalid Qualification                       31
Invalid Profession                          18
Initiation too early                        7
Invalid Centre                              3
```

This allows the IT team to prioritize common problems.

---

# 31. Large Data / 50K+ Records

The system is intended to support large volumes.

However, Excel itself is not a database and opening thousands of workbooks simultaneously is inefficient.

For large datasets:

- Split data into manageable chunks
- Keep individual files at or below 500 records
- Avoid excessive terminal logging
- Use progress indicators
- Use controlled parallel processing if implemented
- Do not create one process per CPU core without testing
- Avoid loading the same large workbook repeatedly

A practical workflow for 50,000 records is:

```text
50,000
   ↓
100 × 500-record files
   ↓
Batch validation
   ↓
1 consolidated error report
```

---

# 32. Installation

## Requirement

Python 3.10+ is recommended.

Check:

```bash
python --version
```

or:

```bash
py --version
```

---

## Install dependencies

Create/update:

```text
requirements.txt
```

with:

```text
streamlit
pandas
openpyxl
```

Install:

```bash
pip install -r requirements.txt
```

If using a virtual environment:

### Windows

```bash
python -m venv .venv
```

Activate:

```bash
.venv\Scripts\activate
```

If PowerShell execution policy prevents activation, you can still run Python through the environment directly or use Command Prompt.

---

# 33. Running the Application

From the project directory:

```bash
streamlit run app.py
```

The application will normally open in a browser.

If it does not open automatically, Streamlit will display the local URL in the terminal.

---

# 34. Deployment

The application can be deployed on:

- Internal Windows machine
- Internal Linux server
- Cloud VM
- Streamlit-compatible hosting
- Internal organizational infrastructure

For SBM data, internal/private deployment is strongly preferred.

The data contains potentially sensitive personal information such as:

- Aadhaar
- Mobile number
- DOB
- Address
- Email
- Photograph

Therefore, do not expose the application publicly without appropriate authentication, network controls, access restrictions and organizational approval.

---

# 35. Security Guidelines

The application should:

- Avoid logging Aadhaar numbers
- Avoid logging full mobile numbers
- Avoid displaying unnecessary personal data
- Delete temporary uploaded files after processing where appropriate
- Restrict access to authorized IT users
- Avoid permanent storage of uploaded Excel files unless required
- Avoid storing uploaded photographs unnecessarily

Error reports should contain only the information necessary to correct the data.

---

# 36. Important Design Principle

The validator and corrector are different systems.

### Validator

Answers:

> Is this record acceptable?

### Corrector

Answers:

> Can this record be safely corrected without guessing?

The corrector should never convert an uncertain value into a seemingly valid value.

For example:

```text
9826383089.0
```

may safely become:

```text
9826383089
```

if it is clearly an Excel integer representation.

But:

```text
98263830890
```

should not automatically become:

```text
9826383089
```

by taking the last ten digits.

That would silently corrupt data.

---

# 37. Recommended Development Practices

When changing a validation rule:

1. Update `validator_core.py`
2. Add test cases
3. Run the validator against known-good data
4. Run against intentionally bad data
5. Confirm the error report
6. Only then deploy the updated application

Do not duplicate validation rules between:

```text
app.py
validator_core.py
corrector.py
```

The core module should remain the single source of truth.

---

# 38. Testing Strategy

Maintain a small test workbook containing examples of:

### Valid

- Valid names
- Valid dates
- Valid Aadhaar
- Valid mobile
- Valid centre
- Valid state
- Valid master values

### Invalid

- Blank mandatory field
- Wrong gender
- Invalid mobile
- `.0` mobile representation
- Invalid Aadhaar
- Duplicate Aadhaar
- Invalid centre
- Wrong state
- Invalid skill
- Invalid qualification
- Invalid profession
- Address >75 characters
- Invalid email
- Invalid blood group
- Initiation before 20 years
- Blank row
- Non-sequential S No

Every major validator change should be tested against this workbook.

---

# 39. Troubleshooting

## `ModuleNotFoundError`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Streamlit command not found

Use:

```bash
python -m streamlit run app.py
```

---

## Master Centre validation fails unexpectedly

Check the master log.

The loader should identify the actual centre column and should not load:

```text
POINT
SUB CENTRE
CENTRE
MAJOR CENTRE
```

as centre names.

If it does, the master-column detection is wrong.

---

## Dates appear as `1992-01-18 00:00:00`

This may simply be pandas' representation of an Excel date.

Do not automatically treat that representation as proof that the Excel display format is wrong.

The validator should validate the underlying date value appropriately.

---

## Mobile appears as `.0`

Example:

```text
9826383089.0
```

This can occur when Excel/pandas interprets a numeric mobile value as a floating-point number.

The safe normalization is:

```text
9826383089.0
        ↓
9826383089
```

Never blindly remove or truncate digits.

---

# 40. Future Enhancements

Recommended future improvements:

1. Corrector tab in Streamlit
2. Splitter tab in Streamlit
3. ZIP download containing all split files
4. Photo-folder validation
5. Cell-level error highlighting
6. Error cells highlighted directly in a copy of the original workbook
7. Automatic safe corrections
8. Audit log of every correction
9. Before/after values in correction report
10. Duplicate detection across multiple uploaded files
11. Cross-file Aadhaar duplicate detection
12. Cross-file mobile duplicate detection
13. Dashboard showing error trends
14. Controlled parallel processing
15. User authentication
16. Role-based access
17. Processing history
18. Automated final ZIP generation
19. Automated re-validation after correction
20. Final "SBM Ready" certification report

---

# 41. Recommended Production Workflow

For the State IT Team:

```text
                    ┌───────────────────┐
                    │ Raw Sewadar Data  │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │ Safe Correction   │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │ Split ≤ 500 rows  │
                    └─────────┬─────────┘
                              ↓
                    ┌───────────────────┐
                    │ SBM Validation    │
                    └─────────┬─────────┘
                              ↓
                 ┌────────────┴────────────┐
                 ↓                         ↓
          Errors Found                No Errors
                 ↓                         ↓
        Excel Error Report          SBM Ready Files
                 ↓
          Manual Correction
                 ↓
             Revalidate
                 ↓
          SBM Ready Files
```

---

# 42. Final Checklist Before SBM Submission

Before submission confirm:

- [ ] Correct SBM Excel template used
- [ ] Header unchanged
- [ ] No hidden sheets
- [ ] No hidden columns
- [ ] No blank rows
- [ ] Maximum 500 records per sheet
- [ ] S No sequential
- [ ] All mandatory fields populated
- [ ] Names correctly formatted
- [ ] Gender valid
- [ ] DOB valid
- [ ] Aadhaar valid
- [ ] No duplicate Aadhaar
- [ ] Mobile exactly 10 digits
- [ ] Mobile starts with 6/7/8/9
- [ ] Centre matches SBM master
- [ ] State matches SBM master
- [ ] Address lines ≤75 characters
- [ ] PIN valid where applicable
- [ ] Initiation date valid
- [ ] Initiation age ≥20 years
- [ ] Skills match master or are blank
- [ ] Qualification matches master or is blank
- [ ] Profession matches master or is blank
- [ ] Email valid where populated
- [ ] Blood group valid
- [ ] Photo filenames correct
- [ ] Photos are JPG
- [ ] Photos are within allowed size
- [ ] Final validation completed successfully
- [ ] Error report reviewed
- [ ] Final Excel files saved as `.xlsx`

---

# 43. Ownership of Rules

The SBM rules in this project are based on the current data-preparation requirements supplied to the development team.

If Beas HQ changes the SBM template, master lists, accepted values, field requirements, date rules, photo requirements or submission process, update the validation rules before processing new data.

The application should never be considered the authority over SBM itself. SBM/Beas HQ requirements remain the final authority.

---

## Quick Start

```bash
pip install -r requirements.txt
```

Then:

```bash
streamlit run app.py
```

Upload:

```text
1. SBM-Master-Lists.xlsx
2. Sewadar Excel file(s)
```

Click:

```text
🚀 Start Validation
```

Review the results and download:

```text
SBM_Validation_Report.xlsx
```

Fix the reported errors and run validation again until all files show:

```text
✅ CLEAN — READY FOR SBM UPLOAD
```
