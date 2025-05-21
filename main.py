from collections import Counter
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import math

#retrieving data

csv_url = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/SchoolsSecondary_11.csv"
df = pd.read_csv(csv_url)


# If columns contain lists (e.g., from reading CSV with object dtype), flatten them
for col in ['MajorSubject', 'MinorSubject']:
    df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)

# Ensure numeric fields are scalar and not lists or repeated values
for col in ['TotalEnrolment', 'TOD', 'CBE', 'CountyName', 'Role']:
    df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)


# Keep  while keeping subjects as list
agg_funcs = {
    'MajorSubject': list,
    'MinorSubject': list,
    'TotalEnrolment': 'first',
    'TOD': 'first', 
    'CBE' : 'first',
    'CountyName': 'first',
    'Role': 'first',
}

df = df.groupby('Institution_Name').agg(agg_funcs).reset_index()
# Preprocessing by removing the nulls
df = df.dropna ()

policy_brackets = [
    {'streams': 1, 'enr_min': 0, 'enr_max': 180, 'cbe': 9},
    {'streams': 2, 'enr_min': 181, 'enr_max': 360, 'cbe': 19},
    {'streams': 3, 'enr_min': 361, 'enr_max': 540, 'cbe': 28},
    {'streams': 4, 'enr_min': 541, 'enr_max': 720, 'cbe': 38},
    {'streams': 5, 'enr_min': 721, 'enr_max': 900, 'cbe': 47},
    {'streams': 6, 'enr_min': 901, 'enr_max': 1080, 'cbe': 55},
    {'streams': 7, 'enr_min': 1081, 'enr_max': 1260, 'cbe': 63},
    {'streams': 8, 'enr_min': 1261, 'enr_max': 1440, 'cbe': 68},
    {'streams': 9, 'enr_min': 1441, 'enr_max': 1620, 'cbe': 76},
    {'streams': 10, 'enr_min': 1621, 'enr_max': 1800, 'cbe': 85},
    {'streams': 11, 'enr_min': 1801, 'enr_max': 1980, 'cbe': 93},
    {'streams': 12, 'enr_min': 1981, 'enr_max': 2160, 'cbe': 101},
]

# Helper functions
def get_policy_cbe(enrollment):
    for bracket in policy_brackets:
        if bracket['enr_min'] <= enrollment <= bracket['enr_max']:
            return bracket['cbe']
    return 93 + 8 * (math.ceil(enrollment / 180) - 11)

def calculate_likely_streams(cbe_actual):
    for bracket in policy_brackets:
        if cbe_actual <= bracket['cbe']:
            return bracket['streams']
    return math.ceil((cbe_actual - 93) / 8) + 11


subject_lessons = {
    'English'                                           : 5,
    'Kiswahili/kenya sign language'                     : 4,
    'Mathematic'                                        : 5,
    'Religious Education'                               : 4,
    'Social Studies (including Life Skills Education)'  : 4,
    'Intergrated Science (including Health Education)'  : 5,
    'Pre-Technical Studies'                             : 4,
    'Agriculture and Nutrition'                         : 4,
    'Creative Arts and Sports'                          : 5
}

TOTAL_WEEKLY_LESSONS_PER_CLASS = sum(subject_lessons.values()) + 1 #PPI

# Calculate the number of teachers required per subject per class (stream)
subject_teacher_per_class = {subject: lessons/27 for subject, lessons in subject_lessons.items()}



# calculating the number of streams
def calculate_streams(TotalEnrolment):
  return math.ceil(TotalEnrolment / 45)


#calculate the total number of lessons needed
def calculate_total_lessons(num_classes):
  return num_classes * TOTAL_WEEKLY_LESSONS_PER_CLASS


#administrators  policy provisions based on the number of classes
def get_admin_count (num_classes):
  if num_classes <= 7:
      return {'DeputyPrincipals':1, 'SeniorMaster':1}
  elif 8 <= num_classes <= 11:
      return {'DeputyPrincipals': 1, 'SeniorMasters': 2}
  elif 12 <= num_classes <= 15:
      return {'DeputyPrincipals': 1, 'SeniorMasters': 4}
  elif 16 <= num_classes <= 23:
      return {'DeputyPrincipals': 2, 'SeniorMasters': 5}
  elif 24 <= num_classes <= 31:
      return {'DeputyPrincipals': 2, 'SeniorMasters': 6}
  elif 32 <= num_classes <= 43:
      return {'DeputyPrincipals': 2, 'SeniorMasters': 7}
  elif 44 <= num_classes <= 47:
      return {'DeputyPrincipals': 2, 'SeniorMasters': 8}
  else:
      return {'DeputyPrincipals': 2, 'SeniorMasters': 9}


# Calculating the shortfall  from admin load
def calculate_admin_shortfall(num_admins, lessons_allocated_per_admin, expected_load_per_admin = 27):
  total_expected  = num_admins * expected_load_per_admin
  shortfall       = (total_expected - lessons_allocated_per_admin) /  27
  return shortfall


def calculate_total_teachers(enrollment):
    streams = calculate_likely_streams(enrollment)
    total_lessons = calculate_total_lessons(streams)

    admins = get_admin_count(streams)
    num_admins = 1 + admins['DeputyPrincipals'] + admins['SeniorMasters']  # +1 for Principal

    # Admin lesson allocations (estimated):
    principal_lessons = 10
    deputy_lessons = 15
    senior_master_lessons = 18

    admin_lessons = (
        principal_lessons +
        (admins['DeputyPrincipals'] * deputy_lessons) +
        (admins['SeniorMasters'] * senior_master_lessons)
    )

    # Calculate the admin shortfall in teaching
    admin_shortfall = calculate_admin_shortfall(num_admins, admin_lessons)

    # Final teacher requirement
    teachers_required = (total_lessons + (admin_shortfall * 27)) / 27

    return math.ceil(teachers_required), streams

def calculate_subject_shortage_full_output(school_row, debug=False):
    try:
        # Debugging line to see the row data (only if debug is True)
        if debug:
            st.write("Processing row:", school_row)

        # Safely extract enrollment
        enrollment = school_row['TotalEnrolment']
        
        # Fallback in case of missing/NaN
        if pd.isna(enrollment):
            enrollment = 0

        # Estimate streams
        streams = math.ceil(enrollment / 45)

        # Policy required teachers per subject
        required_teachers = {
            subject: math.ceil(streams * load)
            for subject, load in subject_teacher_per_class.items()
        }

        # Flatten major/minor subjects
        major_subjects = school_row['MajorSubject']
        minor_subjects = school_row['MinorSubject']

        # Ensure major_subjects and minor_subjects are lists
        if isinstance(major_subjects, str):
            major_subjects = [major_subjects]
        if isinstance(minor_subjects, str):
            minor_subjects = [minor_subjects]

        # Count occurrences of major and minor subjects
        major_counts = Counter(major_subjects)
        minor_counts = Counter(minor_subjects)
        all_subjects = major_counts + minor_counts
        actual_counts = dict(Counter(all_subjects))

        # Calculate shortages and prepare a recommendation
        shortages = {}
        recommendations = []

        for subject, required in required_teachers.items():
            actual = actual_counts.get(subject, 0)
            shortage = math.ceil(required - actual)
            if shortage > 0:
                recommendations.append(f"{int(shortage)} {subject}")
            shortages[subject] = shortage

        # Assemble full output
        output = {
            "Institution_Name": school_row["Institution_Name"],
            "Enrollment": enrollment,
            "TOD": int(school_row['TOD']) if not pd.isna(school_row['TOD']) else 0,
            "PolicyCBE": get_policy_cbe(enrollment),
            "LikelyStreams": calculate_likely_streams(get_policy_cbe(enrollment)),
            "ActualTeachers": actual_counts,
            "SubjectShortages": shortages,
            "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed"
        }

        return pd.Series(output)

    except Exception as e:
        st.write(f"Error processing row: {school_row}")
        st.write(e)
        return pd.Series()  # Return an empty Series or handle as needed


subject_shortages_df = df.apply(calculate_subject_shortage_full_output, axis=1)
subject_shortages_df['Institution_Name'] = df['Institution_Name']

# Reorganize
subject_shortages_df = subject_shortages_df.set_index('Institution_Name')


# dashboard UI

st.set_page_config(page_title="Teacher Shortage Recommender", layout="wide", page_icon="🏫")

# Custom CSS Styling
st.markdown("""
<style>
    .main {background-color: #f5f7fb;}
    .header {color: white; padding: 2rem; background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);}
    .metric-box {padding: 1.5rem; border-radius: 10px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .highlight {color: #4b6cb7; font-weight: 700;}
    .recommendation {padding: 1.5rem; background: #e8f0fe; border-radius: 10px; margin-top: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<div class="header"><h1>📚 Teacher Shortage Dashboard</h1></div>', unsafe_allow_html=True)
# School Selection
selected_school = st.selectbox(
    "🏫 Select School", 
    subject_shortages_df.index,
    help="Choose an institution to view detailed staffing analysis"
)
school_data = subject_shortages_df.loc[selected_school]
