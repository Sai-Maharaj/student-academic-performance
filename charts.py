"""Shared Plotly figures for the Streamlit app and offline HTML report."""
import html
import plotly.express as px
import plotly.graph_objects as go
from analysis import correlation, summary

BLUE,TEAL,RED='#3157D5','#178879','#C95056'

def figures(frame):
    if frame.empty:
        return {}
    subject=frame.groupby('Subject',as_index=False).Total_Mark.mean().sort_values('Total_Mark')
    trend=frame.groupby('Semester',as_index=False).agg(Average_Mark=('Total_Mark','mean'),Records=('Total_Mark','size'))
    counts=frame.Result.value_counts().reindex(['Pass','Fail'],fill_value=0).rename_axis('Result').reset_index(name='Count')
    corr=correlation(frame)
    result={
        'Subject performance':px.bar(subject,x='Total_Mark',y='Subject',orientation='h',text_auto='.1f',labels={'Total_Mark':'Mean total mark / 100'},color_discrete_sequence=[BLUE]),
        'Semester trend':px.line(trend,x='Semester',y='Average_Mark',markers=True,hover_data=['Records'],labels={'Average_Mark':'Mean total mark / 100'},color_discrete_sequence=[BLUE]),
        'Pass and fail':px.pie(counts,names='Result',values='Count',hole=.68,color='Result',color_discrete_map={'Pass':TEAL,'Fail':RED}),
        'Marks distribution':go.Figure(go.Histogram(x=frame.Total_Mark,xbins=dict(start=0,end=100.00001,size=10),marker_color=BLUE)),
        'Attendance and performance':px.scatter(frame,x='Attendance',y='Total_Mark',color='Result',hover_data=['Student_ID','Subject','Semester'],color_discrete_map={'Pass':TEAL,'Fail':RED},opacity=.55,render_mode='svg',labels={'Total_Mark':'Total mark / 100','Attendance':'Attendance (%)'}),
        'Correlation analysis':go.Figure(go.Heatmap(z=corr.to_numpy(),x=['Internal','External','Assignment','Attendance','Total'],y=['Internal','External','Assignment','Attendance','Total'],zmin=-1,zmax=1,colorscale='RdBu',text=corr.to_numpy(),texttemplate='%{text:.2f}',hoverongaps=False,colorbar=dict(title='Pearson r')))
    }
    for title,fig in result.items():
        fig.update_layout(title=title,template='plotly_white',font=dict(family='Arial',size=13,color='#25324A'),height=390,margin=dict(l=30,r=20,t=55,b=45),paper_bgcolor='white',plot_bgcolor='white')
    result['Subject performance'].update_xaxes(range=[0,105])
    result['Semester trend'].update_xaxes(dtick=1)
    result['Semester trend'].update_yaxes(range=[0,100])
    result['Marks distribution'].update_layout(xaxis_title='Total mark / 100 (10-mark bins)',yaxis_title='Subject records',bargap=.08)
    result['Marks distribution'].update_xaxes(range=[0,100])
    result['Attendance and performance'].update_xaxes(range=[0,100])
    result['Attendance and performance'].update_yaxes(range=[0,100])
    result['Pass and fail'].update_traces(textinfo='percent+label')
    return result

def html_report(frame,source='Dataset',filters='All records'):
    m=summary(frame)
    intro=f'<h1>Student Academic Performance Analysis</h1><p>{html.escape(source)} | {html.escape(filters)}</p><p>{m["students"]} students · {m["records"]} subject records · Mean {m["average"]}/100 · Subject pass rate {m["pass_rate"]}%</p><p>Descriptive results only. Pass: total ≥ 40. Support: total &lt; 40 or attendance &lt; 75%. Correlation does not establish causation.</p>'
    parts=[]
    for i,fig in enumerate(figures(frame).values()):
        parts.append('<section>'+fig.to_html(full_html=False,include_plotlyjs=True if i==0 else False)+'</section>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Academic analysis</title><style>body{font:16px Arial;margin:32px auto;max-width:1100px;color:#25324a;background:#f5f7fb}h1,p{padding:0 20px}section{background:white;margin:20px;border-radius:12px;padding:16px}</style>'+intro+''.join(parts)+'</html>'
