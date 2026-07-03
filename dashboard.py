

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
from itertools import chain, combinations
import re
from pathlib import Path

# Page config 
st.set_page_config(
    page_title="Sri Lankan IT/Tech Job Market",
    page_icon="🇱🇰",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Custom CSS 
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #4C9BE8;
        margin-bottom: 8px;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
    .metric-label { font-size: 0.85rem; color: #666; margin-top: 2px; }
    .section-header {
        font-size: 1.2rem; font-weight: 600;
        color: #1a1a2e; margin: 16px 0 8px;
        border-bottom: 2px solid #4C9BE8;
        padding-bottom: 4px;
    }
    .insight-box {
        background: #e8f4fd;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.9rem;
        color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)

#  Skills taxonomy 
SKILLS = {
    "Python": [r"\bpython\b"], "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "Java": [r"\bjava\b(?!script)"], "PHP": [r"\bphp\b"],
    "SQL": [r"\bsql\b"], "HTML": [r"\bhtml\b"], "CSS": [r"\bcss\b"],
    "React": [r"\breact\b", r"\breactjs\b"], "Node.js": [r"\bnode\.?js\b"],
    "Laravel": [r"\blaravel\b"], "Django": [r"\bdjango\b"],
    "Excel": [r"\bexcel\b", r"\bms excel\b"],
    "Power BI": [r"\bpower\s?bi\b"], "Tableau": [r"\btableau\b"],
    "Google Analytics": [r"\bgoogle analytics\b"],
    "Machine Learning": [r"\bmachine learning\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Docker": [r"\bdocker\b"], "Git": [r"\bgit\b(?!hub)"],
    "GitHub": [r"\bgithub\b"], "Linux": [r"\blinux\b"],
    "MySQL": [r"\bmysql\b"], "PostgreSQL": [r"\bpostgresql\b"],
    "MongoDB": [r"\bmongodb\b"],
    "SEO": [r"\bseo\b"], "SEM": [r"\bsem\b"],
    "Social Media": [r"\bsocial media\b"],
    "Content Writing": [r"\bcontent writing\b", r"\bcontent creation\b"],
    "Email Marketing": [r"\bemail marketing\b"],
    "Facebook Ads": [r"\bfacebook ads\b", r"\bmeta ads\b"],
    "Google Ads": [r"\bgoogle ads\b"],
    "TikTok": [r"\btiktok\b"], "Instagram": [r"\binstagram\b"],
    "Canva": [r"\bcanva\b"],
    "Photoshop": [r"\bphotoshop\b"], "Illustrator": [r"\billustrator\b"],
    "Figma": [r"\bfigma\b"], "UI/UX": [r"\bui[/ ]?ux\b"],
    "Video Editing": [r"\bvideo edit\w*\b"],
    "AutoCAD": [r"\bautocad\b"], "Networking": [r"\bnetworking\b"],
    "Project Management": [r"\bproject management\b"],
    "Communication": [r"\bcommunication\b"],
    "Teamwork": [r"\bteamwork\b", r"\bteam player\b"],
    "Problem Solving": [r"\bproblem.?solv\w*\b"],
    "MS Office": [r"\bms office\b", r"\bmicrosoft office\b"],
}

SOFT_SKILLS = {"Communication", "Teamwork", "Problem Solving", "MS Office"}
DIGITAL_SKILLS = {
    "Social Media", "Instagram", "TikTok", "Facebook Ads", "Google Ads",
    "SEO", "SEM", "Email Marketing", "Content Writing", "Canva",
    "Photoshop", "Illustrator", "Figma", "UI/UX", "Video Editing",
}
TECH_SKILLS = set(SKILLS.keys()) - SOFT_SKILLS - DIGITAL_SKILLS


def extract_skills(text):
    if not isinstance(text, str):
        return []
    text_lower = text.lower()
    found = []
    for skill, patterns in SKILLS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(skill)
                break
    return found


#  Data loading 
@st.cache_data
def load_data():
    data_path = Path(__file__).resolve().parent / "data" / "ikman_jobs_clean.csv"
    df = pd.read_csv(data_path)

    # Re-extract skills from descriptions
    df["skills"] = df["description"].apply(extract_skills)
    df["skill_count"] = df["skills"].apply(len)

    # Recency buckets
    def recency_bucket(d):
        if pd.isna(d):     return "Unknown"
        if d <= 1:         return "Today/Yesterday"
        elif d <= 3:       return "2–3 Days"
        elif d <= 7:       return "This Week"
        elif d <= 14:      return "Last 2 Weeks"
        else:              return "Older"

    df["recency"] = df["days_ago"].apply(recency_bucket)
    return df


df = load_data()

#  Sidebar 
st.sidebar.title(" Filters")
st.sidebar.markdown("---")

all_categories = sorted(df["category"].unique())
selected_cats = st.sidebar.multiselect(
    "Category", all_categories, default=all_categories
)

all_locations = sorted(df["location"].dropna().unique())
selected_locs = st.sidebar.multiselect(
    "Location", all_locations, default=all_locations
)



# Apply filters
filtered = df[
    df["category"].isin(selected_cats) &
    (df["location"].isin(selected_locs) | df["location"].isna())
].copy()

#  Page navigation 
page = st.sidebar.radio(
    " Navigation",
    [" Overview", " EDA", " NLP Skills", " Salary"],
    index=0,
)

# ══════════════════════════════════════════════════════════════════════════
# PAGE 1: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════
if page == " Overview":
    st.title("🇱🇰 Sri Lankan IT/Tech Job Market Analysis")
    st.markdown("*Data collected via web scraping from ikman.lk — Sri Lanka's largest classifieds platform*")
    st.markdown("---")

    # KPI cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Listings", len(filtered))
    with col2:
        st.metric("Categories", filtered["category"].nunique())
    with col3:
        st.metric("Cities Covered", filtered["location"].nunique())
    with col4:
        pct_sal = f"{filtered['salary_mid'].notna().mean()*100:.0f}%"
        st.metric("With Salary Data", pct_sal)
    with col5:
        all_skills = list(chain.from_iterable(filtered["skills"]))
        st.metric("Unique Skills Found", len(set(all_skills)))

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown('<p class="section-header">Listings by Category</p>', unsafe_allow_html=True)
        cat_counts = filtered["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.bar(
            cat_counts, x="count", y="category", orientation="h",
            color="category", text="count",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="Listings",
                          height=320, margin=dict(l=0, r=20, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<p class="section-header">Category Share</p>', unsafe_allow_html=True)
        fig2 = px.pie(
            cat_counts, values="count", names="category",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4,
        )
        fig2.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                           legend=dict(orientation="v", x=1, y=0.5))
        fig2.update_traces(textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    col_loc, col_rec = st.columns(2)

    with col_loc:
        st.markdown('<p class="section-header">Top 10 Locations</p>', unsafe_allow_html=True)
        loc_counts = filtered["location"].value_counts().head(10).reset_index()
        loc_counts.columns = ["location", "count"]
        fig3 = px.bar(
            loc_counts, x="count", y="location", orientation="h",
            color="count", text="count",
            color_continuous_scale="Blues",
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(showlegend=False, yaxis_title="", xaxis_title="Listings",
                           height=340, margin=dict(l=0, r=20, t=10, b=0),
                           coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col_rec:
        st.markdown('<p class="section-header">Posting Recency</p>', unsafe_allow_html=True)
        bucket_order = ["Today/Yesterday", "2–3 Days", "This Week", "Last 2 Weeks", "Older", "Unknown"]
        rec_counts = filtered["recency"].value_counts().reindex(bucket_order).fillna(0).reset_index()
        rec_counts.columns = ["recency", "count"]
        fig4 = px.bar(
            rec_counts, x="recency", y="count",
            color="recency", text="count",
            color_discrete_sequence=px.colors.sequential.YlOrRd[::-1][:6],
        )
        fig4.update_traces(textposition="outside")
        fig4.update_layout(showlegend=False, xaxis_title="", yaxis_title="Listings",
                           height=340, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig4, use_container_width=True)

    # Insight box
    top_cat = filtered["category"].value_counts().index[0] if len(filtered) else "—"
    top_loc = filtered["location"].value_counts().index[0] if len(filtered) else "—"
    st.markdown(f"""
    <div class="insight-box">
     <b>Key Takeaways:</b> The most active category is <b>{top_cat}</b> and the dominant hiring city is
    <b>{top_loc}</b>. {filtered['salary_mid'].notna().mean()*100:.0f}% of listings disclose salary -
    typical for classifieds-style job boards where employers prefer to negotiate.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE 2: EDA
# ══════════════════════════════════════════════════════════════════════════
elif page == " EDA":
    st.title(" Exploratory Data Analysis")
    st.markdown(f"*Showing **{len(filtered)}** listings based on current filters*")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<p class="section-header">Job Count by Category</p>', unsafe_allow_html=True)
        cat_counts = filtered["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.bar(cat_counts, x="category", y="count",
                     color="category", text="count",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, xaxis_title="", height=340,
                          margin=dict(t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-header">Location × Category Breakdown</p>', unsafe_allow_html=True)
        top5_locs = filtered["location"].value_counts().head(5).index
        df_top = filtered[filtered["location"].isin(top5_locs)]
        loc_cat = df_top.groupby(["location", "category"]).size().reset_index(name="count")
        fig2 = px.bar(loc_cat, x="location", y="count", color="category",
                      barmode="group",
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(xaxis_title="", height=340,
                           legend=dict(orientation="h", y=-0.25),
                           margin=dict(t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown('<p class="section-header">Top Job Titles</p>', unsafe_allow_html=True)
        stopwords = {"and", "or", "for", "the", "a", "in", "of", "to", "with",
                     "senior", "junior", "assistant", "manager", "executive",
                     "officer", "specialist", "intern", "trainee", "pvt", "ltd"}
        title_words = []
        for title in filtered["title"].dropna():
            words = [w.lower().strip("()/-") for w in title.split()
                     if w.lower().strip("()/-") not in stopwords and len(w) > 2]
            title_words.extend(words)
        word_freq = Counter(title_words).most_common(15)
        word_df = pd.DataFrame(word_freq, columns=["word", "count"])
        fig3 = px.bar(word_df, x="count", y="word", orientation="h",
                      color="count", color_continuous_scale="Viridis", text="count")
        fig3.update_traces(textposition="outside")
        fig3.update_layout(coloraxis_showscale=False, yaxis_title="",
                           height=420, margin=dict(l=0, r=20, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown('<p class="section-header">Days Since Posted Distribution</p>', unsafe_allow_html=True)
        df_days = filtered.dropna(subset=["days_ago"])
        fig4 = px.histogram(df_days, x="days_ago", nbins=20,
                            color_discrete_sequence=["#4C9BE8"],
                            labels={"days_ago": "Days Ago"})
        fig4.update_layout(yaxis_title="Listings", height=200,
                           margin=dict(t=10, b=0))
        st.plotly_chart(fig4, use_container_width=True)

        st.markdown('<p class="section-header">Skills per Listing Distribution</p>', unsafe_allow_html=True)
        fig5 = px.histogram(filtered, x="skill_count", nbins=15,
                            color_discrete_sequence=["#2ECC71"],
                            labels={"skill_count": "Skills Mentioned"})
        fig5.update_layout(yaxis_title="Listings", height=200,
                           margin=dict(t=10, b=0))
        st.plotly_chart(fig5, use_container_width=True)

    # Raw data explorer
    st.markdown("---")
    st.markdown('<p class="section-header">🔎 Raw Data Explorer</p>', unsafe_allow_html=True)
    show_cols = ["category", "title", "company", "location",
                 "salary_mid", "days_ago", "skill_count"]
    st.dataframe(
        filtered[show_cols].sort_values("days_ago").reset_index(drop=True),
        use_container_width=True, height=300
    )


# ══════════════════════════════════════════════════════════════════════════
# PAGE 3: NLP SKILLS
# ══════════════════════════════════════════════════════════════════════════
elif page == " NLP Skills":
    st.title(" NLP Skill Extraction")
    st.markdown(f"*Dictionary-based skill extraction from {len(filtered)} job descriptions*")
    st.markdown("---")

    all_skills = list(chain.from_iterable(filtered["skills"]))
    skill_counts = Counter(all_skills)

    tech_counts   = Counter({k: v for k, v in skill_counts.items() if k in TECH_SKILLS})
    digital_counts = Counter({k: v for k, v in skill_counts.items() if k in DIGITAL_SKILLS})
    soft_counts   = Counter({k: v for k, v in skill_counts.items() if k in SOFT_SKILLS})

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Skill Mentions", sum(skill_counts.values()))
    col2.metric("Unique Skills Detected", len(skill_counts))
    col3.metric("Listings with Skills", (filtered["skill_count"] > 0).sum())
    col4.metric("Avg Skills / Listing", f"{filtered['skill_count'].mean():.1f}")

    st.markdown("---")

    # Three skill category charts
    tab1, tab2, tab3 = st.tabs([" Technical", " Digital Marketing & Design", " Soft Skills"])

    with tab1:
        tech_df = pd.DataFrame(tech_counts.most_common(15), columns=["skill", "count"])
        if not tech_df.empty:
            tech_df["pct"] = (tech_df["count"] / len(filtered) * 100).round(1)
            fig = px.bar(tech_df, x="count", y="skill", orientation="h",
                         color="count", text="count",
                         color_continuous_scale="Viridis",
                         hover_data={"pct": True, "count": True})
            fig.update_traces(textposition="outside")
            fig.update_layout(coloraxis_showscale=False, yaxis_title="",
                              xaxis_title="Number of Listings",
                              height=450, margin=dict(l=0, r=30, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No technical skills detected in filtered data.")

    with tab2:
        dm_df = pd.DataFrame(digital_counts.most_common(15), columns=["skill", "count"])
        if not dm_df.empty:
            dm_df["pct"] = (dm_df["count"] / len(filtered) * 100).round(1)
            fig2 = px.bar(dm_df, x="count", y="skill", orientation="h",
                          color="count", text="count",
                          color_continuous_scale="Plasma",
                          hover_data={"pct": True, "count": True})
            fig2.update_traces(textposition="outside")
            fig2.update_layout(coloraxis_showscale=False, yaxis_title="",
                               xaxis_title="Number of Listings",
                               height=450, margin=dict(l=0, r=30, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No digital marketing/design skills detected in filtered data.")

    with tab3:
        soft_df = pd.DataFrame(soft_counts.most_common(), columns=["skill", "count"])
        if not soft_df.empty:
            fig3 = px.bar(soft_df, x="count", y="skill", orientation="h",
                          color="count", text="count",
                          color_continuous_scale="Greens")
            fig3.update_traces(textposition="outside")
            fig3.update_layout(coloraxis_showscale=False, yaxis_title="",
                               xaxis_title="Number of Listings",
                               height=280, margin=dict(l=0, r=30, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    col_heat, col_pair = st.columns(2)

    with col_heat:
        st.markdown('<p class="section-header">Skills × Category Heatmap</p>', unsafe_allow_html=True)
        top15 = [s for s, _ in skill_counts.most_common(15)]
        cats = filtered["category"].unique()
        cat_skill = {}
        for cat in cats:
            cat_df = filtered[filtered["category"] == cat]
            cat_all = list(chain.from_iterable(cat_df["skills"]))
            cat_skill[cat] = Counter(cat_all)
        heatmap_data = pd.DataFrame(
            {cat: [cat_skill[cat].get(s, 0) for s in top15] for cat in cats},
            index=top15
        )
        fig_heat = px.imshow(
            heatmap_data, text_auto=True,
            color_continuous_scale="YlOrRd",
            aspect="auto",
            labels=dict(color="Listings"),
        )
        fig_heat.update_layout(height=430, margin=dict(t=10, b=0))
        st.plotly_chart(fig_heat, use_container_width=True)

    with col_pair:
        st.markdown('<p class="section-header">Top Skill Co-occurrences</p>', unsafe_allow_html=True)
        pair_counts = Counter()
        for skill_list in filtered["skills"]:
            for pair in combinations(sorted(set(skill_list)), 2):
                pair_counts[pair] += 1
        top_pairs = pd.DataFrame(
            [(f"{a} + {b}", c) for (a, b), c in pair_counts.most_common(12)],
            columns=["pair", "count"]
        )
        if not top_pairs.empty:
            fig_pair = px.bar(top_pairs, x="count", y="pair", orientation="h",
                              color="count", text="count",
                              color_continuous_scale="Teal")
            fig_pair.update_traces(textposition="outside")
            fig_pair.update_layout(coloraxis_showscale=False, yaxis_title="",
                                   xaxis_title="Co-occurrences",
                                   height=430, margin=dict(l=0, r=30, t=10, b=0))
            st.plotly_chart(fig_pair, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE 4: SALARY
# ══════════════════════════════════════════════════════════════════════════
elif page == " Salary":
    st.title(" Salary Analysis")
    st.markdown(f"*Based on {filtered['salary_mid'].notna().sum()} listings with disclosed salary*")
    st.markdown("> Only ~42% of listings disclose salary - common on classifieds platforms where employers prefer to negotiate.")
    st.markdown("---")

    df_sal = filtered.dropna(subset=["salary_mid"]).copy()

    if len(df_sal) == 0:
        st.warning("No salary data available for the selected filters.")
    else:
        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Listings with Salary", len(df_sal))
        col2.metric("Median Salary", f"LKR {df_sal['salary_mid'].median():,.0f}")
        col3.metric("Highest Salary", f"LKR {df_sal['salary_max'].max():,.0f}")
        col4.metric("Lowest Salary", f"LKR {df_sal['salary_min'].min():,.0f}")

        st.markdown("---")
        col_dist, col_cat = st.columns(2)

        with col_dist:
            st.markdown('<p class="section-header">Salary Distribution</p>', unsafe_allow_html=True)
            fig = px.histogram(df_sal, x="salary_mid", nbins=20,
                               color_discrete_sequence=["#4C9BE8"],
                               labels={"salary_mid": "Salary (LKR)"},
                               marginal="box")
            fig.update_layout(yaxis_title="Listings", height=340,
                              margin=dict(t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col_cat:
            st.markdown('<p class="section-header">Average Salary by Category</p>', unsafe_allow_html=True)
            avg_cat = (df_sal.groupby("category")["salary_mid"]
                       .mean().reset_index()
                       .sort_values("salary_mid", ascending=True))
            avg_cat["label"] = avg_cat["salary_mid"].apply(lambda x: f"LKR {x:,.0f}")
            fig2 = px.bar(avg_cat, x="salary_mid", y="category", orientation="h",
                          color="salary_mid", text="label",
                          color_continuous_scale="Blues")
            fig2.update_traces(textposition="outside")
            fig2.update_layout(coloraxis_showscale=False, yaxis_title="",
                               xaxis_title="Average Salary (LKR)",
                               height=340, margin=dict(l=0, r=120, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

        col_title, col_skill = st.columns(2)

        with col_title:
            st.markdown('<p class="section-header">Average Salary by Job Title (Top 10)</p>', unsafe_allow_html=True)
            top_titles = df_sal["title"].value_counts().head(10).index
            avg_title = (df_sal[df_sal["title"].isin(top_titles)]
                         .groupby("title")["salary_mid"]
                         .mean().reset_index()
                         .sort_values("salary_mid", ascending=True))
            avg_title["label"] = avg_title["salary_mid"].apply(lambda x: f"LKR {x:,.0f}")
            fig3 = px.bar(avg_title, x="salary_mid", y="title", orientation="h",
                          color="salary_mid", text="label",
                          color_continuous_scale="Greens")
            fig3.update_traces(textposition="outside")
            fig3.update_layout(coloraxis_showscale=False, yaxis_title="",
                               xaxis_title="Average Salary (LKR)",
                               height=380, margin=dict(l=0, r=120, t=10, b=0))
            st.plotly_chart(fig3, use_container_width=True)

        with col_skill:
            st.markdown('<p class="section-header">Highest Paying Skills</p>', unsafe_allow_html=True)
            skill_salary = {}
            for _, row in df_sal.iterrows():
                for skill in row["skills"]:
                    skill_salary.setdefault(skill, []).append(row["salary_mid"])
            skill_avg = {k: np.mean(v) for k, v in skill_salary.items() if len(v) >= 2}
            if skill_avg:
                sal_skill_df = (pd.DataFrame(list(skill_avg.items()),
                                             columns=["skill", "avg_salary"])
                                .sort_values("avg_salary", ascending=True)
                                .tail(10))
                sal_skill_df["label"] = sal_skill_df["avg_salary"].apply(
                    lambda x: f"LKR {x:,.0f}")
                fig4 = px.bar(sal_skill_df, x="avg_salary", y="skill", orientation="h",
                              color="avg_salary", text="label",
                              color_continuous_scale="Oranges")
                fig4.update_traces(textposition="outside")
                fig4.update_layout(coloraxis_showscale=False, yaxis_title="",
                                   xaxis_title="Average Salary (LKR)",
                                   height=380, margin=dict(l=0, r=120, t=10, b=0))
                st.plotly_chart(fig4, use_container_width=True)

        # Scatter: skill count vs salary
        st.markdown("---")
        st.markdown('<p class="section-header">Does Mentioning More Skills = Higher Salary?</p>',
                    unsafe_allow_html=True)
        fig5 = px.scatter(
            df_sal, x="skill_count", y="salary_mid",
            color="category", size="salary_mid",
            hover_data=["title", "company", "location"],
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"skill_count": "Skills Mentioned", "salary_mid": "Salary (LKR)"},
        )

        # Add a simple least-squares trend line without requiring statsmodels.
        trend_data = df_sal[["skill_count", "salary_mid"]].dropna()
        if len(trend_data) >= 2:
            slope, intercept = np.polyfit(trend_data["skill_count"], trend_data["salary_mid"], 1)
            x_values = np.linspace(trend_data["skill_count"].min(), trend_data["skill_count"].max(), 100)
            y_values = slope * x_values + intercept
            fig5.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="lines",
                    name="Trend",
                    line=dict(color="#111111", width=2),
                    hoverinfo="skip",
                    showlegend=True,
                )
            )
        fig5.update_layout(height=400, margin=dict(t=10, b=0),
                           legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig5, use_container_width=True)

        corr = df_sal["skill_count"].corr(df_sal["salary_mid"])
        st.markdown(f"""
        <div class="insight-box">
         <b>Correlation between skill count and salary: r = {corr:.2f}</b> :
        {"a moderate positive relationship suggesting listings that mention more skills tend to offer higher salaries."
          if corr > 0.3 else
         "a weak relationship, suggesting salary in Sri Lankan IT/tech roles is not strongly tied to the number of skills listed in the job ad."}
        </div>
        """, unsafe_allow_html=True)