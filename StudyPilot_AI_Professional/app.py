
import sqlite3
from datetime import date, timedelta
from urllib.parse import quote_plus
import pandas as pd
import plotly.express as px
import streamlit as st

DB = "study_planner.db"
st.set_page_config(page_title="StudyPilot AI", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:#0b1020;color:#edf2ff}
[data-testid="stSidebar"]{background:#111a31;border-right:1px solid #2b3858}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.03em}
.hero{padding:1.5rem;border:1px solid #2e3d63;border-radius:22px;background:radial-gradient(circle at 90% 0%,rgba(91,108,255,.32),transparent 36%),linear-gradient(135deg,#192747,#11182b);margin-bottom:1rem}
.kicker{color:#a7b5ff;font-size:.75rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.herotitle{font-size:2.25rem;font-weight:700;color:#fff;margin:.4rem 0}
.sub{color:#bbc7e0}
.metric{padding:1rem;border:1px solid #2b3958;border-radius:16px;background:linear-gradient(145deg,#17233d,#11192b);min-height:110px}
.label{font-size:.83rem;color:#aab8d4}.value{font-size:1.8rem;font-weight:700;color:#fff}.foot{font-size:.75rem;color:#91a0bf}
</style>
""", unsafe_allow_html=True)

def db():
    c=sqlite3.connect(DB,check_same_thread=False)
    c.row_factory=sqlite3.Row
    return c
with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS subjects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,exam_date TEXT,difficulty INTEGER,total_topics INTEGER,completed_topics INTEGER)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,subject_id INTEGER,study_date TEXT,topic TEXT,hours REAL,completed INTEGER DEFAULT 0)""")

def subjects():
    with db() as c: return [dict(x) for x in c.execute("SELECT * FROM subjects ORDER BY exam_date").fetchall()]
def sessions():
    with db() as c:
        return [dict(x) for x in c.execute("""SELECT ss.*,s.name subject FROM sessions ss JOIN subjects s ON s.id=ss.subject_id ORDER BY study_date""").fetchall()]
def score(s,day=None):
    day=day or date.today()
    days=(date.fromisoformat(s["exam_date"])-day).days
    urgency=100 if days<=0 else max(5,100-min(days,60)*1.55)
    pending=max(0,s["total_topics"]-s["completed_topics"])
    pct=pending/max(1,s["total_topics"])*100
    return round(.5*urgency+.2*s["difficulty"]*20+.3*pct,1)
def yt(q): return "https://www.youtube.com/results?search_query="+quote_plus(q)
def make_plan(items,start,end,hours,revision):
    tasks=[]
    for s in items:
        for n in range(max(0,s["total_topics"]-s["completed_topics"])):
            tasks.append({"s":s,"topic":f"{s['name']} — Study block {n+1}","exam":date.fromisoformat(s["exam_date"]),"score":score(s,start)})
    plan=[]
    day=start
    while day<=end:
        budget=float(hours)
        ranked=sorted(tasks,key=lambda t:(t["exam"],-t["score"]))
        for t in ranked:
            if t.get("done") or budget<.5 or day>t["exam"]: continue
            rev=(t["exam"]-day).days<revision
            plan.append({"id":t["s"]["id"],"subject":t["s"]["name"],"date":day.isoformat(),
                         "task":("Revision: " if rev else "Learn: ")+t["topic"],"hours":min(1.0,budget),
                         "priority":score(t["s"],day)})
            t["done"]=True; budget-=min(1.0,budget)
        day+=timedelta(days=1)
    return plan

with st.sidebar:
    st.markdown("## 🎓 StudyPilot AI")
    st.caption("Your personal exam co-pilot")
    st.divider()
    daily=st.slider("Study hours per day",1,12,4)
    revision=st.slider("Revision days before exam",0,5,2)
    st.info("Priority engine: 50% exam urgency · 20% difficulty · 30% pending syllabus")

S=subjects(); SS=sessions(); today=date.today()
topics=sum(s["total_topics"] for s in S); done=sum(s["completed_topics"] for s in S)
nearest=min([(date.fromisoformat(s["exam_date"])-today).days for s in S if date.fromisoformat(s["exam_date"])>=today],default=None)
st.markdown("""<div class="hero"><div class="kicker">Your academic command centre</div>
<div class="herotitle">Study smarter. Walk into exams prepared.</div>
<div class="sub">Date-aware study plans, intelligent priorities, progress tracking and topic-based video discovery in one workspace.</div></div>""",unsafe_allow_html=True)
t=st.tabs(["🏠 Overview","🤖 AI Plan Bot","📚 Subjects","🗓️ My Schedule","🎬 Video Tutor","📈 Analytics"])

with t[0]:
    st.subheader("Your overview")
    cols=st.columns(4)
    metrics=[("Subjects",len(S),"In your workspace"),("Syllabus progress",f"{round(done/topics*100) if topics else 0}% ",f"{done} of {topics} topics done"),("Next exam",f"{nearest} days" if nearest is not None else "—","Nearest upcoming exam"),("Sessions done",sum(x["completed"] for x in SS),"Completed study blocks")]
    for col,(lab,val,foot) in zip(cols,metrics):
        col.markdown(f'<div class="metric"><div class="label">{lab}</div><div class="value">{val}</div><div class="foot">{foot}</div></div>',unsafe_allow_html=True)
    st.markdown("### 🎯 Focus recommendations")
    if S:
        for s in sorted(S,key=score,reverse=True)[:4]:
            st.markdown(f"**{s['name']}** · Priority **{score(s)}** · Exam {s['exam_date']} · {s['total_topics']-s['completed_topics']} blocks pending")
            st.progress(s["completed_topics"]/max(1,s["total_topics"]))
        st.dataframe(pd.DataFrame([{"Subject":s["name"],"Exam":s["exam_date"],"Days left":(date.fromisoformat(s["exam_date"])-today).days,"Priority":score(s)} for s in S]),use_container_width=True,hide_index=True)
    else: st.info("Add subjects in the Subjects tab or use AI Plan Bot to generate a study schedule.")

with t[1]:
    st.subheader("🤖 AI Plan Bot")
    st.write("Enter your subjects and exam dates. The planner generates dated study blocks and adds revision tasks near exams.")
    st.caption("Format: Subject | YYYY-MM-DD | difficulty 1–5 | total topics | completed topics")
    with st.form("bot"):
        raw=st.text_area("Your exam details",height=140,placeholder="DBMS | 2026-10-20 | 5 | 10 | 2\nOperating Systems | 2026-10-23 | 4 | 12 | 3\nAgile Software Development | 2026-10-25 | 3 | 8 | 1")
        c1,c2,c3=st.columns(3)
        start=c1.date_input("Plan starts",today)
        end=c2.date_input("Plan ends",today+timedelta(days=14))
        hrs=c3.slider("Hours/day",1,12,daily,key="bot_hours")
        go=st.form_submit_button("✨ Generate personalized plan",type="primary",use_container_width=True)
    if go:
        parsed=[]; errs=[]
        for i,line in enumerate(raw.strip().splitlines() if raw.strip() else [],1):
            p=[x.strip() for x in line.split("|")]
            try:
                if len(p)<2: raise ValueError("Use the format shown above.")
                d=date.fromisoformat(p[1])
                diff=max(1,min(5,int(''.join(x for x in p[2] if x.isdigit())))) if len(p)>2 else 3
                total=max(1,int(''.join(x for x in p[3] if x.isdigit()))) if len(p)>3 else 8
                comp=max(0,min(total,int(''.join(x for x in p[4] if x.isdigit())))) if len(p)>4 else 0
                parsed.append({"id":-i,"name":p[0],"exam_date":d.isoformat(),"difficulty":diff,"total_topics":total,"completed_topics":comp})
            except Exception as e: errs.append(f"Line {i}: {e}")
        if not raw.strip(): st.error("Enter at least one subject.")
        elif end<start: st.error("Plan end must be on or after the start date.")
        elif errs:
            for e in errs: st.error(e)
        else:
            st.session_state["bot_subjects"]=parsed
            st.session_state["bot_plan"]=make_plan(parsed,start,end,hrs,revision)
            st.session_state["bot_range"]=(start,end)
    if "bot_plan" in st.session_state:
        plan=st.session_state["bot_plan"]
        if not plan: st.warning("No blocks generated. Check pending topics and exam dates.")
        else:
            df=pd.DataFrame([{"Date":p["date"],"Subject":p["subject"],"Task":p["task"],"Hours":p["hours"],"Priority":p["priority"]} for p in plan])
            st.success(f"Generated {len(plan)} study blocks.")
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button("⬇ Download plan CSV",df.to_csv(index=False).encode(), "personalized_study_plan.csv","text/csv")
            st.markdown("#### 🎬 Learn with videos")
            for s in st.session_state["bot_subjects"]: st.markdown(f"- **{s['name']}** — [Find YouTube lessons ↗]({yt(s['name']+' tutorial for engineering students')})")
            if st.button("Save subjects and plan to My Schedule",type="primary"):
                with db() as c:
                    idmap={}
                    for s in st.session_state["bot_subjects"]:
                        row=c.execute("SELECT id FROM subjects WHERE name=?",(s["name"],)).fetchone()
                        if row: sid=row["id"]
                        else:
                            c.execute("INSERT INTO subjects(name,exam_date,difficulty,total_topics,completed_topics) VALUES(?,?,?,?,?)",(s["name"],s["exam_date"],s["difficulty"],s["total_topics"],s["completed_topics"]))
                            sid=c.execute("SELECT id FROM subjects WHERE name=?",(s["name"],)).fetchone()["id"]
                        idmap[s["name"]]=sid
                    for p in plan:
                        c.execute("INSERT INTO sessions(subject_id,study_date,topic,hours,completed) VALUES(?,?,?,?,0)",(idmap[p["subject"]],p["date"],p["task"],p["hours"]))
                st.success("Saved successfully. Open My Schedule to track sessions.")

with t[2]:
    st.subheader("📚 Subject workspace")
    with st.form("add"):
        a,b=st.columns(2)
        name=a.text_input("Subject name",placeholder="Database Management Systems")
        exam=b.date_input("Exam date",today+timedelta(days=14),min_value=today)
        diff=a.slider("Difficulty (1 easy – 5 hard)",1,5,3)
        total=b.number_input("Total topics / study blocks",1,200,10)
        completed=a.number_input("Topics completed",0,200,0)
        add=st.form_submit_button("＋ Save subject",type="primary",use_container_width=True)
        if add:
            if not name.strip(): st.error("Enter a subject name.")
            elif completed>total: st.error("Completed cannot exceed total.")
            else:
                try:
                    with db() as c: c.execute("INSERT INTO subjects(name,exam_date,difficulty,total_topics,completed_topics) VALUES(?,?,?,?,?)",(name.strip(),exam.isoformat(),diff,int(total),int(completed)))
                    st.success("Subject added."); st.rerun()
                except sqlite3.IntegrityError: st.error("That subject already exists.")
    S=subjects()
    if S:
        for s in S:
            with st.container(border=True):
                x,y,z=st.columns([3,1,1])
                x.markdown(f"### {s['name']}")
                x.caption(f"Exam {s['exam_date']} · difficulty {s['difficulty']}/5")
                y.metric("Priority",score(s)); z.metric("Pending",s["total_topics"]-s["completed_topics"])
                st.progress(s["completed_topics"]/max(1,s["total_topics"]))
                st.markdown(f"[Find YouTube lessons ↗]({yt(s['name']+' tutorial')})")
                if st.button(f"Delete {s['name']}",key=f"del{s['id']}"):
                    with db() as c: c.execute("DELETE FROM sessions WHERE subject_id=?",(s["id"],)); c.execute("DELETE FROM subjects WHERE id=?",(s["id"],))
                    st.rerun()
    else: st.info("No subjects yet. Add one above.")

with t[3]:
    st.subheader("🗓️ My Schedule")
    SS=sessions()
    if SS:
        df=pd.DataFrame([{"Date":x["study_date"],"Subject":x["subject"],"Task":x["topic"],"Hours":x["hours"],"Status":"Completed" if x["completed"] else "Pending"} for x in SS])
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Download schedule CSV",df.to_csv(index=False).encode(),"study_schedule.csv","text/csv")
        pend=[x for x in SS if not x["completed"]]
        if pend:
            opts={f"{x['study_date']} · {x['subject']} · {x['topic']}":x["id"] for x in pend}
            selected=st.selectbox("Select completed block",list(opts))
            if st.button("✓ Mark completed",type="primary"):
                sid=opts[selected]
                with db() as c:
                    row=c.execute("SELECT subject_id FROM sessions WHERE id=?",(sid,)).fetchone()
                    c.execute("UPDATE sessions SET completed=1 WHERE id=?",(sid,))
                    c.execute("UPDATE subjects SET completed_topics=MIN(total_topics,completed_topics+1) WHERE id=?",(row["subject_id"],))
                st.success("Progress updated."); st.rerun()
    else: st.info("Generate and save a plan using AI Plan Bot.")

with t[4]:
    st.subheader("🎬 Video Tutor")
    st.write("Find YouTube lessons for a subject or exact topic. This opens YouTube search results; it does not claim to verify individual videos.")
    subj=st.text_input("Subject",placeholder="DBMS")
    topic=st.text_input("Topic",placeholder="Normalization 1NF 2NF 3NF")
    style=st.selectbox("Learning style",["Beginner friendly","University exam preparation","Numerical examples","Full concept lecture"])
    if st.button("🔎 Find YouTube lessons",type="primary"):
        if not subj.strip() and not topic.strip(): st.warning("Enter a subject or topic.")
        else:
            st.success("Your topic search is ready.")
            st.markdown(f"### [▶ Open matching YouTube videos ↗]({yt(subj+' '+topic+' '+style+' tutorial')})")
    st.markdown("#### Quick searches")
    for label,q in [("DBMS normalization","DBMS normalization 1NF 2NF 3NF university lecture"),("OS scheduling","Operating System scheduling algorithms explained"),("Agile & Scrum","Agile software development Scrum sprints user stories"),("AI search algorithms","Artificial Intelligence BFS DFS A star explained")]:
        st.markdown(f"- [{label} ↗]({yt(q)})")

with t[5]:
    st.subheader("📈 Progress analytics")
    S=subjects(); SS=sessions()
    if S:
        df=pd.DataFrame([{"Subject":s["name"],"Completed":s["completed_topics"],"Pending":max(0,s["total_topics"]-s["completed_topics"]),"Progress (%)":round(s["completed_topics"]/max(1,s["total_topics"])*100,1)} for s in S])
        a,b=st.columns(2)
        with a:
            fig=px.bar(df,x="Subject",y="Progress (%)",range_y=[0,100],title="Syllabus completion",text="Progress (%)",color="Progress (%)",color_continuous_scale="Teal")
            fig.update_layout(paper_bgcolor="#111a2c",plot_bgcolor="#111a2c",font_color="#eaf0ff",coloraxis_showscale=False)
            st.plotly_chart(fig,use_container_width=True)
        with b:
            fig=px.bar(df,x="Subject",y=["Completed","Pending"],barmode="stack",title="Completed vs pending",color_discrete_sequence=["#48d6b5","#596b95"])
            fig.update_layout(paper_bgcolor="#111a2c",plot_bgcolor="#111a2c",font_color="#eaf0ff")
            st.plotly_chart(fig,use_container_width=True)
        st.dataframe(df,use_container_width=True,hide_index=True)
    else: st.info("Add subjects to view analytics.")
st.divider()
st.caption("StudyPilot AI · Rule-based intelligent scheduling · SQLite local storage · YouTube search integration")
