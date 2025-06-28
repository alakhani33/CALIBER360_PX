

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import plotly.express as px

# ✅ Streamlit page config
st.set_page_config(page_title="CALIBER360 AI - Real-Time Healthcare Intelligence", layout="wide")

# ✅ Killer hero header
st.title("🚀 CALIBER360 Healthcare AI: Real-Time Healthcare Intelligence Platform")

st.markdown("""
**Welcome to CALIBER360 AI** — an innovative solution that distills complex patient feedback from (H)CAHPS surveys, clinical notes, and social sentiment data into clear, actionable insights.
Gain instant visibility into **What**, **Why**, **Who**, **When**, and **Where**, monitor **real-time patient sentiment**, and uncover critical **themes driving patient experience and reputation**.

---
""")


# Config
# st.set_page_config(page_title="5Ws Distiller", layout="wide")
st.title("🔍 Distilling Complex Text (Patient Feedback, Doctors' Notes, etc.) into 5Ws: What, Why, Who, When, Where")

# Load data
# df = pd.read_csv("Sutter_Sample10_5Ws.csv")
# ✅ Example: cache for 5Ws data
@st.cache_data
def load_5ws_data():
    df = pd.read_csv("Sutter_Sample10_5Ws.csv")
    df.columns = [c.strip() for c in df.columns]
    df.reset_index(drop=True, inplace=True)
    return df

# df.columns = [c.strip() for c in df.columns]

# # Drop index: AgGrid won’t show it anyway by default.
# # Just ensure your DF doesn’t have an unwanted index column.
# df.reset_index(drop=True, inplace=True)
df_5ws = load_5ws_data()

# Build AgGrid config
gb = GridOptionsBuilder.from_dataframe(df_5ws)

# Auto height & wrap
gb.configure_default_column(wrapText=True, autoHeight=True)

# Add custom cell styles for 5Ws
# (Use your actual column names)
five_ws = ["What", "Why", "Who", "When", "Where"]
colors = ["#e8f5e9", "#fff3e0", "#e3f2fd", "#f3e5f5", "#fce4ec"]

for col, color in zip(five_ws, colors):
    js = JsCode(f"""
    function(params) {{
        return {{
            'backgroundColor': '{color}',
            'whiteSpace': 'normal',
        }}
    }}
    """)
    gb.configure_column(col, cellStyle=js)

# Build final grid
grid_options = gb.build()

# Show it
AgGrid(
    df_5ws,
    gridOptions=grid_options,
    height=600,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True
)

st.caption("✅ **Powered by CALIBER360 AI** — distilling complexity into clarity instantaneously.")


# Part 2: Real-Time Sentiment Chart
# -------------------------------

st.header("📊 Real-Time Patient Feedback from Social Media")

# Load your sentiment dataset
# df = pd.read_csv("Combined1000_NLPed.csv")
# ✅ Example: cache for social sentiment
@st.cache_data
def load_sentiment_data():
    df = pd.read_csv("Combined1000_NLPed.csv")
    df['Facility'] = df['Facility'].replace(
        to_replace=r'(?i)kaiser.*',
        value='Health System Alpha',
        regex=True
    )
    df['date'] = pd.to_datetime(df['date'])
    df['Org'] = df['Facility'].apply(lambda x: 'Health System Alpha' if 'Health System Alpha' in x else 'Competition')
    df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
    return df

# df['Facility'] = df['Facility'].replace(
#     to_replace=r'(?i)kaiser.*',
#     value='Health System Alpha',
#     regex=True
# )

# df['date'] = pd.to_datetime(df['date'])
# df['Org'] = df['Facility'].apply(lambda x: 'Health System Alpha' if 'Health System Alpha' in x else 'Competition')
# df['week'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)

df = load_sentiment_data()

# Weekly sentiment
df_weekly = (
    df.groupby(['week', 'Org', 'source'], as_index=False)
    .agg({'sentiment': 'mean'})
)

# Alerts logic
df_pivot = df_weekly.pivot(index=['week', 'source'], columns='Org', values='sentiment').reset_index()
df_pivot['Alert'] = (df_pivot['Competition'] > 0) & (df_pivot['Health System Alpha'] < -0.25)

fig = px.line(
    df_weekly,
    x='week',
    y='sentiment',
    color='Org',
    facet_row='source',
    markers=True,
    color_discrete_map={'Health System Alpha': 'blue', 'Competition': 'orange'},
    title="Weekly Sentiment: Health System Alpha vs Competition"
)

fig.update_yaxes(range=[-0.75, 0.75])

facet_sources = df_weekly['source'].unique().tolist()
for i, src in enumerate(facet_sources):
    fig.update_xaxes(
        title_text="Week",
        showticklabels=True,
        matches=None,
        row=i + 1
    )

for i, src in enumerate(facet_sources):
    facet_alerts = df_pivot[(df_pivot['source'] == src) & df_pivot['Alert']]
    for _, row in facet_alerts.iterrows():
        fig.add_annotation(
            x=row['week'],
            y=row['Health System Alpha'],
            text="🚨 Alert",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowcolor="red",
            ax=0,
            ay=-40,
            font=dict(color="red", size=12),
            xref=f"x{i+1}",
            yref=f"y{i+1}"
        )

fig.add_annotation(
    text="Sentiment Scale: +1 = Very Positive, -1 = Very Negative",
    xref="paper",
    yref="paper",
    x=0,
    y=1.15,
    showarrow=False,
    font=dict(size=12)
)

fig.update_layout(
    height=1800,
    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    margin=dict(b=200)
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Part 3: Hierarchical Top Themes Treemap
# -------------------------------

st.header("🌳 Top Themes Hierarchy for Health System Alpha")

# Prepare Kaiser-only subset for theme extraction
df_kaiser = df[df['Facility'].str.contains('Health System Alpha', case=False)].copy()

master_keywords = [
    "Cleanliness", "Staff", "Emotional Support", "Safety", "Facilities", "Pain Management",
    "Other", "Billing", "Communication", "Nursing Staff", "Release", "Wait Time", "Food",
    "Referral", "Medication", "Coordination", "Equipment", "Bedside Manners", "Delivery Experience",
    "Treatment", "Roommates", "Discharge Process", "Preparation", "Diagnosis & Treatment",
    "Dietary Guidance", "Sharing", "Training", "Weight", "Navigation", "Corporatization",
    "Insurance", "Scheduling", "Knowledge", "Medical Records", "Parking", "Appointment Scheduling",
    "Privacy", "Schedule Management", "Technology", "Accessibility", "Appointment Access",
    "Appointment Management", "System", "Admin", "Interface", "Access", "Staffing",
    "Treatment Plan", "Initial Process", "Express Care", "Tech Support", "Diagnosis",
    "Online System", "Specimen Collection", "Location", "Efficient Use of Time"
]

def find_master_themes(raw_theme):
    tags = []
    theme_lc = raw_theme.lower().strip()
    for keyword in master_keywords:
        if keyword.lower().strip() in theme_lc:
            tags.append(keyword)
    return tags or ["Other"]

df_kaiser['master_theme'] = df_kaiser['theme'].apply(find_master_themes)
df_exploded = df_kaiser.explode('master_theme').copy()

theme_summary = (
    df_exploded.groupby('master_theme', as_index=False)
    .agg(
        count=('text', 'count'),
        avg_sentiment=('sentiment', 'mean')
    )
    .sort_values('count', ascending=False)
)

top10 = theme_summary.head(80)

fig2 = px.treemap(
    top10,
    path=['master_theme'],
    values='count',
    color='avg_sentiment',
    color_continuous_scale=['red', 'white', 'green'],
    range_color=[-1, 1],
    title="🔍 Top Themes (multi-matched) for Health System Alpha"
)
fig2.update_layout(margin=dict(t=50, l=25, r=25, b=25))

st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.markdown(
    """
    ### 🤝 Ready to Transform Patient Experience?

    **CALIBER360 AI** helps healthcare teams see what really matters — when it matters most.  
    Unlock deeper insights from clinical notes, patient reviews, and social sentiment — all in real time.

    📞 **Contact us today** for a personalized demonstration and see how CALIBER360 AI can work for **your organization**.
    """
)
