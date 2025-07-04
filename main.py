from collections import Counter
import streamlit as st
import pandas as pd
import numpy as np
import math

# Page Configuration
st.set_page_config(page_title="Teacher Shortage Recommender", layout="wide", page_icon="🏫")

# Custom CSS Styling
st.markdown("""
<style>
    .main {background-color: #f5f7fb;}
    .header {color: white; padding: 2rem; background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);}
    .metric-box {padding: 1.5rem; border-radius: 10px; background: #e3f2fd; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .highlight {color: #0d47a1; font-weight: 700;}
    .recommendation {padding: 1.5rem; background: #e3f2fd; border-radius: 10px; margin-top: 1.5rem;}
    .teacher-detail {padding: 1rem; background: #f8f9fa; border-radius: 8px; margin: 0.5rem 0;}
</style>
""", unsafe_allow_html=True)

# Data Loading and Processing
@st.cache_data
def load_and_process_data():
    # Load data
    csv_url = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/SchoolsSecondary_11.csv"
    df = pd.read_csv(csv_url)
    
    # Preprocessing - handle list-like values
    for col in ['MajorSubject', 'MinorSubject']:
        df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)
    
    for col in ['TotalEnrolment', 'TOD', 'CBE', 'CountyName', 'Role']:
        df[col] = df[col].apply(lambda x: x[0] if isinstance(x, list) else x)
    
    # Group by institution while keeping subjects as lists
    agg_funcs = {
        'MajorSubject': list,
        'MinorSubject': list,
        'TotalEnrolment': 'first',
        'TOD': 'first', 
        'CBE': 'first',
        'CountyName': 'first',
        'Role': list,
    }
    
    df = df.groupby('Institution_Name').agg(agg_funcs).reset_index()
    return df

# Constants and Configuration
subject_lessons = {
    'English': 5,
    'Kiswahili/kenya sign language': 4,
    'Mathematic': 5,
    'Religious Education': 4,
    'Social Studies (including Life Skills Education)': 4,
    'Intergrated Science (including Health Education)': 5,
    'Pre-Technical Studies': 4,
    'Agriculture and Nutrition': 4,
    'Creative Arts and Sports': 5
}

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

# Enhanced subject mapping from the second code
subject_mapping = {
    'ENGLISH': 'English',
    'KISWAHILI/ KSL': 'Kiswahili/kenya sign language',
    'MATHEMATICS': 'Mathematic',
    'BIOLOGY': 'Intergrated Science (including Health Education)',
    'CHEMISTRY': 'Intergrated Science (including Health Education)',
    'PHYSICS': 'Intergrated Science (including Health Education)',
    'CHRISTIAN RELIGIOUS': 'Religious Education',
    'ISLAMIC RELIGIOUS': 'Religious Education',
    'HINDU RELIGIOUS': 'Religious Education',
    'HISTORY & GOVERNMENT': 'Social Studies (including Life Skills Education)',
    'GEOGRAPHY': 'Social Studies (including Life Skills Education)',
    'CIVICS': 'Social Studies (including Life Skills Education)',
    'SOCIOLOGY': 'Social Studies (including Life Skills Education)',
    'AGRICULTURE': 'Pre-Technical Studies',
    'BUSINESS EDUCATION': 'Pre-Technical Studies',
    'HOME SCIENCE': 'Pre-Technical Studies',
    'INDUSTRIAL ARTS': 'Pre-Technical Studies',
    'MUSIC': 'Creative Arts and Sports',
    'ART & DESIGN': 'Creative Arts and Sports',
    'PHYSICAL EDUCATION': 'Creative Arts and Sports',
    'DRAMA': 'Creative Arts and Sports',
    'DANCE': 'Creative Arts and Sports',
    'SPORTS SCIENCE': 'Creative Arts and Sports',
    'BUSINESS STUDIES': 'Pre-Technical Studies',
    'ENG. LITERATURE': 'English',
}

# Helper Functions
def get_policy_cbe_and_streams(enrollment):
    """Get policy CBE and streams based on enrollment"""
    for bracket in policy_brackets:
        if bracket['enr_min'] <= enrollment <= bracket['enr_max']:
            return bracket['cbe'], bracket['streams']
    # For enrollments above the highest bracket
    return 93 + 8 * (math.ceil(enrollment / 180) - 11), math.ceil(enrollment / 180)

def count_subject_occurrences(subjects_list, policy_subject):
    """Count how many subjects map to each policy category"""
    if not subjects_list:
        return 0
    
    count = 0
    for raw_subj in subjects_list:
        if pd.isna(raw_subj):
            continue
        mapped = subject_mapping.get(str(raw_subj).upper().strip())
        if mapped == policy_subject:
            count += 1
    return count

def create_teacher_details_df(major_subjects, minor_subjects):
    """Create a detailed dataframe of teachers by subject"""
    teacher_details = []
    
    # Process major subjects
    if major_subjects:
        for subject in major_subjects:
            if pd.notna(subject):
                mapped_subject = subject_mapping.get(str(subject).upper().strip(), str(subject))
                teacher_details.append({
                    'Teacher_Subject': str(subject),
                    'Policy_Category': mapped_subject,
                    'Specialization': 'Major'
                })
    
    # Process minor subjects
    if minor_subjects:
        for subject in minor_subjects:
            if pd.notna(subject):
                mapped_subject = subject_mapping.get(str(subject).upper().strip(), str(subject))
                teacher_details.append({
                    'Teacher_Subject': str(subject),
                    'Policy_Category': mapped_subject,
                    'Specialization': 'Minor'
                })
    
    return pd.DataFrame(teacher_details)

def calculate_enhanced_shortage_analysis(school_row):
    """Enhanced shortage calculation using improved methodology"""
    try:
        enrollment = school_row['TotalEnrolment']
        if pd.isna(enrollment):
            enrollment = 0
        
        # Get policy requirements
        policy_cbe, streams = get_policy_cbe_and_streams(enrollment)
        
        # Calculate weekly lesson demand per subject
        weekly_demand = {
            subj: lessons * streams
            for subj, lessons in subject_lessons.items()
        }
        
        # Calculate required teachers (27 lessons per teacher per week)
        required_teachers = {
            subj: math.ceil(weekly_demand[subj] / 27)
            for subj in weekly_demand
        }
        
        # Count actual teachers by policy category
        major_subjects = school_row['MajorSubject'] if isinstance(school_row['MajorSubject'], list) else [school_row['MajorSubject']]
        minor_subjects = school_row['MinorSubject'] if isinstance(school_row['MinorSubject'], list) else [school_row['MinorSubject']]
        
        actual_teachers = {
            subj: count_subject_occurrences(major_subjects, subj) + 
                  count_subject_occurrences(minor_subjects, subj)
            for subj in subject_lessons
        }
        
        # Calculate shortages
        subject_shortage = {
            subj: max(0, required_teachers[subj] - actual_teachers[subj])
            for subj in subject_lessons
        }
        
        # Generate recommendations
        recommendations = []
        for subject, shortage in subject_shortage.items():
            if shortage > 0:
                recommendations.append(f"{int(shortage)} {subject}")
        
        return {
            "Institution_Name": school_row["Institution_Name"],
            "County": school_row.get('CountyName', 'Unknown'),
            "Enrollment": int(enrollment),
            "TOD": int(school_row['TOD']) if not pd.isna(school_row['TOD']) else 0,
            "CBE_Actual": int(school_row['CBE']) if not pd.isna(school_row['CBE']) else 0,
            "PolicyCBE": int(policy_cbe),
            "PolicyStreams": int(streams),
            "RequiredTeachers": required_teachers,
            "ActualTeachers": actual_teachers,
            "SubjectShortages": subject_shortage,
            "TotalShortage": sum(subject_shortage.values()),
            "WeeklyDemand": weekly_demand,
            "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed",
            "MajorSubjects": major_subjects,
            "MinorSubjects": minor_subjects
        }
        
    except Exception as e:
        st.error(f"Error processing school data: {str(e)}")
        return None

# Main App
def main():
    # Header
    st.markdown('<div class="header"><h1>📚 Teacher Shortage Dashboard</h1><p>Advanced Analysis with Subject Mapping & Teacher Details</p></div>', unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading school data..."):
        df = load_and_process_data()
    
    if df.empty:
        st.error("No data loaded. Please check the data source.")
        return
    
    # School Selection
    st.markdown("### 🏫 School Selection")
    selected_school = st.selectbox(
        "Choose School for Analysis", 
        df['Institution_Name'].tolist(),
        help="Select an institution to view detailed staffing analysis"
    )
    
    # Get school data
    school_row = df[df['Institution_Name'] == selected_school].iloc[0]
    analysis = calculate_enhanced_shortage_analysis(school_row)
    
    if not analysis:
        st.error("Could not analyze selected school.")
        return
    
    st.markdown("---")
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><h3>📊 Enrollment</h3><p class="highlight">{analysis["Enrollment"]:,}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><h3>📌 Policy CBE</h3><p class="highlight">{analysis["PolicyCBE"]}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><h3>🏫 Policy Streams</h3><p class="highlight">{analysis["PolicyStreams"]}</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><h3>⚠️ Total Shortage</h3><p class="highlight">{int(analysis["TotalShortage"])}</p></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main Analysis Section
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📋 Teacher Requirements vs Actual")
        
        # Create comparison dataframe
        comparison_data = []
        for subject in subject_lessons.keys():
            comparison_data.append({
                'Subject': subject,
                'Required': analysis['RequiredTeachers'][subject],
                'Actual': analysis['ActualTeachers'][subject],
                'Shortage': analysis['SubjectShortages'][subject],
                'Weekly_Lessons': analysis['WeeklyDemand'][subject]
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Style the dataframe
        def highlight_shortage(val):
            if val > 0:
                return 'background-color: #ffcdd2'
            return ''
        
        styled_df = comparison_df.style.applymap(highlight_shortage, subset=['Shortage'])
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    with col_right:
        st.subheader("👨🏫 Teacher Details by Subject")
        
        # Create teacher details dataframe
        teacher_details_df = create_teacher_details_df(
            analysis['MajorSubjects'], 
            analysis['MinorSubjects']
        )
        
        if not teacher_details_df.empty:
            # Add teacher count by policy category
            teacher_summary = teacher_details_df.groupby(['Policy_Category', 'Specialization']).size().reset_index(name='Count')
            
            st.dataframe(teacher_details_df, use_container_width=True, height=200)
            
            st.markdown("**Summary by Policy Category:**")
            summary_pivot = teacher_summary.pivot(index='Policy_Category', columns='Specialization', values='Count').fillna(0)
            summary_pivot['Total'] = summary_pivot.sum(axis=1)
            st.dataframe(summary_pivot, use_container_width=True)
        else:
            st.info("No teacher subject data available for this school.")
    
    # Detailed Teacher Information Section
    st.markdown("---")
    st.subheader("📊 Detailed Subject Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Subject Breakdown", "Weekly Demand", "School Info"])
    
    with tab1:
        # Subject shortage visualization
        shortage_data = [(k, v) for k, v in analysis['SubjectShortages'].items() if v > 0]
        if shortage_data:
            shortage_df = pd.DataFrame(shortage_data, columns=['Subject', 'Shortage'])
            st.bar_chart(shortage_df.set_index('Subject'))
        else:
            st.success("🎉 No teacher shortages identified!")
    
    with tab2:
        # Weekly lesson demand
        demand_df = pd.DataFrame.from_dict(analysis['WeeklyDemand'], orient='index', columns=['Weekly Lessons'])
        demand_df['Required Teachers'] = [analysis['RequiredTeachers'][idx] for idx in demand_df.index]
        st.dataframe(demand_df, use_container_width=True)
    
    with tab3:
        # School information
        st.markdown(f"**County:** {analysis['County']}")
        st.markdown(f"**Current CBE:** {analysis['CBE_Actual']}")
        st.markdown(f"**TOD:** {analysis['TOD']}")
        
        # Raw subject lists
        if analysis['MajorSubjects']:
            st.markdown("**Major Subjects:**")
            st.write(", ".join([str(s) for s in analysis['MajorSubjects'] if pd.notna(s)]))
        
        if analysis['MinorSubjects']:
            st.markdown("**Minor Subjects:**")
            st.write(", ".join([str(s) for s in analysis['MinorSubjects'] if pd.notna(s)]))
    
    # Recommendation Section
    st.markdown("---")
    st.markdown(f'<div class="recommendation"><h3>📋 Staffing Recommendation</h3><p>{analysis["Recommendation"]}</p></div>', unsafe_allow_html=True)
    
    # County-wide Analysis Option
    def county_wide_analysis(df, analysis):
    st.markdown("---")
    if st.button("🗺️ View County-wide Analysis"):
        county_name = analysis['County']
        county_schools = df[df['CountyName'] == county_name]

        if len(county_schools) > 1:
            st.subheader(f"Schools in {county_name} County")

            county_analysis = []
            for _, school in county_schools.iterrows():
                school_analysis = calculate_enhanced_shortage_analysis(school)
                if school_analysis:
                    county_analysis.append({
                        'School': school_analysis['Institution_Name'],
                        'Enrollment': school_analysis['Enrollment'],
                        'Total_Shortage': school_analysis['TotalShortage'],
                        'Policy_CBE': school_analysis['PolicyCBE']
                    })

            if county_analysis:
                county_df = pd.DataFrame(county_analysis)
                st.dataframe(county_df, use_container_width=True)

                # 🔽 School selection
                school_list = county_df['School'].tolist()
                selected_school = st.selectbox("📌 Select a School to View Detailed Info", school_list)

                if selected_school:
                    selected_school_row = county_schools[county_schools['Institution_Name'] == selected_school]
                    if not selected_school_row.empty:
                        st.markdown("---")
                        st.subheader(f"📊 Dashboard for {selected_school}")

                        # Run same detailed analysis function
                        detailed_info = calculate_enhanced_shortage_analysis(selected_school_row.iloc[0])

                        if detailed_info:
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.markdown(f'<div class="metric-box"><h3>📊 Enrollment</h3><p class="highlight">{detailed_info["Enrollment"]:,}</p></div>', unsafe_allow_html=True)
                            with col2:
                                st.markdown(f'<div class="metric-box"><h3>📌 Policy CBE</h3><p class="highlight">{detailed_info["PolicyCBE"]}</p></div>', unsafe_allow_html=True)
                            with col3:
                                st.markdown(f'<div class="metric-box"><h3>🏫 Policy Streams</h3><p class="highlight">{detailed_info["PolicyStreams"]}</p></div>', unsafe_allow_html=True)
                            with col4:
                                st.markdown(f'<div class="metric-box"><h3>⚠️ Total Shortage</h3><p class="highlight">{int(detailed_info["TotalShortage"])}</p></div>', unsafe_allow_html=True)

                            st.markdown("---")

                            st.subheader("🏷️ Select Role in School")
                            roles = selected_school_row.iloc[0]['Role']
                            if isinstance(roles, list):
                                selected_role = st.selectbox("Available Roles", roles)
                                st.info(f"Selected Role: {selected_role}")
                            else:
                                st.info(f"Available Role: {roles}")
                    else:
                        st.warning("Selected school not found in data.")
        else:
            st.info("Only one school found in this county.")

if __name__ == "__main__":
    main()
