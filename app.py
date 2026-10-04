"""Run with: python -m streamlit run app.py"""
from pathlib import Path
import json
import streamlit as st
from analysis import FIELDS, ValidationError, load_csv, filter_data, summary, student_summary, export_csv
from charts import figures, html_report

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='Academic Performance | Student Analytics',page_icon='📊',layout='wide')
st.markdown('''<style>.block-container{padding-top:4rem;max-width:1500px}h1{letter-spacing:-.035em}div[data-testid="stMetric"]{background:#f4f6fc;border:1px solid #e3e8f3;border-radius:12px;padding:18px}section[data-testid="stSidebar"]{background:#f5f7fc}</style>''',unsafe_allow_html=True)
st.caption('ACADEMIC INSIGHTS  /  AI & DATA SCIENCE MINI PROJECT')
st.title('Student Academic Performance')
st.write('Explore achievement, attendance and learning patterns across your academic data.')

with st.sidebar:
    st.header('Your workspace')
    mode=st.radio('Data source',['Synthetic sample','Upload CSV'],key='mode')
    raw=(ROOT/'data'/'sample_students.csv').read_bytes()
    source='Synthetic demonstration dataset · not real student results'
    if mode=='Upload CSV':
        upload=st.file_uploader('Academic records (.csv)',type=['csv'],help='UTF-8, up to 5 MB. Files are sent to the hosting server and processed in session memory. Use synthetic or anonymized data.')
        if upload is None:
            st.info('Choose a CSV to begin. Download the template below.')
            st.download_button('Download CSV template',(','.join(FIELDS)+'\n').encode(),file_name='student_template.csv',mime='text/csv')
            st.stop()
        raw=upload.getvalue()
        source='Uploaded academic dataset · source supplied by user'
    st.download_button('Download CSV template',(','.join(FIELDS)+'\n').encode(),file_name='student_template.csv',mime='text/csv')
    st.download_button('Download sample dataset',(ROOT/'data'/'sample_students.csv').read_bytes(),file_name='sample_students.csv',mime='text/csv')
try:
    data=load_csv(raw)
except ValidationError as exc:
    st.error(f'CSV validation failed: {exc}')
    st.info('No partial analysis was produced. Correct the file and upload it again.')
    st.stop()

with st.sidebar:
    st.divider()
    st.subheader('Filter records')
    department=st.selectbox('Department',['All']+sorted(data.Department.unique()),key='department')
    available=filter_data(data,department=department)
    semester=st.selectbox('Semester',['All']+sorted(available.Semester.unique().tolist()),key='semester')
    available=filter_data(available,semester=semester)
    subject=st.selectbox('Subject',['All']+sorted(available.Subject.unique()),key='subject')
    query=st.text_input('Find student',placeholder='Student ID or name',key='query')
    support=st.checkbox('Only records needing support',key='support')
    st.caption('Filters apply to every metric, chart, table and download.')
    st.divider()
    st.caption('Academic Performance Analysis · Educational demonstration')

view=filter_data(data,department,semester,subject,query,support)
st.caption(source)
if view.empty:
    st.warning('No records match these filters. Change the selections or clear the student search.')
    st.stop()
m=summary(view)
cols=st.columns(4)
for col,label,value in zip(cols,['Unique students','Mean mark / 100','Subject pass rate','Students needing support'],[str(m['students']),f"{m['average']:.2f}",f"{m['pass_rate']:.1f}%",str(m['support_students'])]):
    col.metric(label,value)
st.caption(f"{m['records']:,} subject records · Median {m['median']:.2f} · Population SD {m['std_dev']:.2f} · Mean attendance {m['attendance']:.1f}%")
tabs=st.tabs(['Overview & visualizations','Student records','Academic support','Methodology & downloads'])
with tabs[0]:
    for i,(name,fig) in enumerate(figures(view).items()):
        if i%2==0:
            chart_cols=st.columns(2)
        with chart_cols[i%2]:
            st.plotly_chart(fig,width='stretch',key=name,config={'displaylogo':False})
    st.caption('Pass/fail counts subject records. Semester means describe selected records; changing cohorts can affect trends. Blank correlation cells mean insufficient variation or data.')
    st.info('Marks contribute directly to the total, so their correlation with the total is partly mathematical. Associations in the synthetic sample do not demonstrate real-world effects.')
with tabs[1]:
    st.subheader('Student and semester summary')
    st.caption('A semester passes when every selected subject passes. A subject filter produces a partial-semester summary, not a complete semester result.')
    st.dataframe(student_summary(view).round(2),hide_index=True,width='stretch')
    st.subheader('Validated subject records')
    st.dataframe(view,hide_index=True,width='stretch')
with tabs[2]:
    st.subheader('Records for academic follow-up')
    st.write('A subject total below 40/100 or attendance below 75% triggers a transparent support flag. These are demonstration thresholds, not verified college regulations.')
    flagged=view.loc[view.Support_Needed,['Student_ID','Student_Name','Semester','Subject','Total_Mark','Attendance','Support_Reason']]
    if flagged.empty:
        st.success('No selected records meet the support criteria.')
    else:
        st.dataframe(flagged,hide_index=True,width='stretch')
    st.caption('Support flags guide human review. They are not an ML prediction or an automatic academic decision.')
with tabs[3]:
    st.subheader('Analysis rules')
    st.write('Total = Internal (0–25) + External (0–60) + Assignment (0–15). All subjects have equal weight. Subject pass: total ≥ 40. Grade bands: A+ ≥ 90, A ≥ 80, B ≥ 70, C ≥ 60, D ≥ 50, E ≥ 40, F < 40.')
    st.write('Rows represent one student in one subject in one semester. Missing, invalid, non-finite and duplicate-key records are rejected. Whitespace is trimmed. Correlation uses Pearson r; repeated student records are not independent observations. No inferential or causal claims are made.')
    st.write('Uploaded files are processed in memory on the hosting server for this session; this app does not write them to a database or local file. Reloading or restarting may clear them. Export the analysis before leaving. The bundled sample is always available.')
    desc=f'Department: {department}; Semester: {semester}; Subject: {subject}; Search: {query or "none"}; Support only: {support}'
    st.download_button('Download filtered analysis CSV',export_csv(view),file_name='academic_analysis.csv',mime='text/csv')
    st.download_button('Download student summary CSV',export_csv(student_summary(view)),file_name='student_summary.csv',mime='text/csv')
    st.download_button('Download summary JSON',json.dumps({'source':source,'filters':desc,**m},indent=2),file_name='summary.json',mime='application/json')
    st.download_button('Download interactive HTML report',html_report(view,source,desc),file_name='academic_visualizations.html',mime='text/html')
