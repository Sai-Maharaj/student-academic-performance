"""Validated long-format academic data and explicit, illustrative grading rules."""
import csv
import io
import numpy as np
import pandas as pd

FIELDS = ['Student_ID','Student_Name','Department','Semester','Subject','Internal_Mark','External_Mark','Assignment_Mark','Attendance']
NUMERIC = ['Semester','Internal_Mark','External_Mark','Assignment_Mark','Attendance']
LIMITS = {'Semester':(1,8),'Internal_Mark':(0,25),'External_Mark':(0,60),'Assignment_Mark':(0,15),'Attendance':(0,100)}
MAX_BYTES, MAX_ROWS = 5*1024*1024, 20000

class ValidationError(ValueError):
    """An actionable input error safe to display to a user."""

def load_csv(content):
    """All-or-nothing validation; trim whitespace, never impute academic marks."""
    if isinstance(content,str):
        content=content.encode('utf-8')
    if len(content)>MAX_BYTES:
        raise ValidationError('CSV exceeds the 5 MB limit.')
    try:
        reader=csv.reader(io.StringIO(content.decode('utf-8-sig')),strict=True)
        if next(reader,None)!=FIELDS:
            raise ValidationError('Column names and order must exactly match the CSV template.')
        rows=[]
        for number,row in enumerate(reader,2):
            if len(row)!=len(FIELDS):
                raise ValidationError(f'Line {number}: expected {len(FIELDS)} fields; found {len(row)}.')
            rows.append([x.strip() for x in row])
            if len(rows)>MAX_ROWS:
                raise ValidationError(f'Maximum {MAX_ROWS:,} rows allowed.')
    except (UnicodeError,csv.Error) as exc:
        raise ValidationError('Use a valid UTF-8 CSV file: '+str(exc)) from None
    if not rows:
        raise ValidationError('The file contains no records.')
    frame=pd.DataFrame(rows,columns=FIELDS)
    if (frame=='').any().any():
        raise ValidationError('Missing values are not allowed. Fill all fields and try again.')
    for col in ['Student_ID','Student_Name','Department','Subject']:
        if frame[col].map(lambda x: len(x)>80 or any(ord(c)<32 for c in x)).any():
            raise ValidationError(f'{col} must contain 1–80 printable characters.')
    for col in NUMERIC:
        frame[col]=pd.to_numeric(frame[col],errors='coerce')
        low,high=LIMITS[col]
        bad=~np.isfinite(frame[col]) | ~frame[col].between(low,high)
        if bad.any():
            line=int(np.flatnonzero(bad.to_numpy())[0])+2
            raise ValidationError(f'Line {line}: {col} must be a finite number between {low} and {high}.')
    if (frame.Semester%1!=0).any():
        raise ValidationError('Semester must be a whole number from 1 to 8.')
    frame.Semester=frame.Semester.astype(int)
    if frame.duplicated(['Student_ID','Semester','Subject']).any():
        raise ValidationError('Duplicate Student_ID + Semester + Subject records are not allowed.')
    if frame.groupby('Student_ID')[['Student_Name','Department']].nunique().gt(1).any().any():
        raise ValidationError('Each Student_ID must have one consistent name and department.')
    return enrich(frame)

def enrich(frame):
    frame=frame.copy()
    frame['Total_Mark']=frame[['Internal_Mark','External_Mark','Assignment_Mark']].sum(axis=1).round(6)
    frame['Result']=np.where(frame.Total_Mark>=40,'Pass','Fail')
    frame['Grade']=np.select([frame.Total_Mark>=90,frame.Total_Mark>=80,frame.Total_Mark>=70,frame.Total_Mark>=60,frame.Total_Mark>=50,frame.Total_Mark>=40],['A+','A','B','C','D','E'],default='F')
    frame['Support_Reason']=frame.apply(lambda r:'; '.join(reason for flag,reason in [(r.Total_Mark<40,'Subject mark below 40'),(r.Attendance<75,'Attendance below 75%')] if flag),axis=1)
    frame['Support_Needed']=frame.Support_Reason!=''
    return frame

def filter_data(frame,department='All',semester='All',subject='All',query='',support_only=False):
    mask=pd.Series(True,index=frame.index)
    for col,value in [('Department',department),('Semester',semester),('Subject',subject)]:
        if value!='All':
            mask &= frame[col]==value
    if query.strip():
        mask &= (frame.Student_ID+' '+frame.Student_Name).str.contains(query.strip(),case=False,regex=False)
    if support_only:
        mask &= frame.Support_Needed
    return frame.loc[mask].copy()

def summary(frame):
    if frame.empty:
        return dict(records=0,students=0,average=None,median=None,std_dev=None,pass_rate=None,attendance=None,support_students=0)
    return dict(records=len(frame),students=int(frame.Student_ID.nunique()),average=round(float(frame.Total_Mark.mean()),2),median=round(float(frame.Total_Mark.median()),2),std_dev=round(float(frame.Total_Mark.std(ddof=0)),2),pass_rate=round(float(frame.Result.eq('Pass').mean()*100),2),attendance=round(float(frame.Attendance.mean()),2),support_students=int(frame.loc[frame.Support_Needed,'Student_ID'].nunique()))

def student_summary(frame):
    if frame.empty:
        return pd.DataFrame(columns=['Student_ID','Student_Name','Department','Semester','Average_Mark','Attendance','Subjects','Failed_Subjects','Support_Needed','Semester_Result'])
    result=frame.groupby(['Student_ID','Student_Name','Department','Semester'],as_index=False).agg(Average_Mark=('Total_Mark','mean'),Attendance=('Attendance','mean'),Subjects=('Subject','count'),Failed_Subjects=('Result',lambda x:int(x.eq('Fail').sum())),Support_Needed=('Support_Needed','any'))
    result['Semester_Result']=np.where(result.Failed_Subjects==0,'Pass','Fail')
    return result.sort_values(['Average_Mark','Student_ID'],ascending=[False,True]).reset_index(drop=True)

def correlation(frame):
    return frame[['Internal_Mark','External_Mark','Assignment_Mark','Attendance','Total_Mark']].corr().round(3)

def export_csv(frame):
    safe=frame.copy()
    for col in safe.select_dtypes(include=['object','str']).columns:
        safe[col]=safe[col].map(lambda v: "'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v)
    return safe.to_csv(index=False).encode('utf-8-sig')
