import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Competitive Intelligence Tracker", layout="wide")

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path, encoding="utf-8")
    # type fixes
    if "backlink_count" in df.columns:
        df["backlink_count"] = pd.to_numeric(df["backlink_count"], errors="coerce").fillna(0).astype(int)
    if "impact" in df.columns:
        df["impact"] = pd.to_numeric(df["impact"], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df

# ==== Load ====
DATA_PATH = "ci_results_clean.csv"      # change if needed
df = load_data(DATA_PATH)

st.title("🔎 Competitive Intelligence Tracker")
st.caption("Auto-extracted changes + backlink strength, ranked by impact")

# ==== Sidebar filters ====
with st.sidebar:
    st.header("Filters")
    comps = sorted(df["competitor"].dropna().unique())
    comp_pick = st.multiselect("Competitor(s)", comps, default=comps)

    priorities = sorted(df["priority"].dropna().unique())
    prio_pick = st.multiselect("Priority", priorities, default=priorities)

    sigs = sorted(df["backlink_signal"].dropna().unique())
    sig_pick = st.multiselect("Backlink signal", sigs, default=sigs)

    min_backlinks = int(df["backlink_count"].max() if "backlink_count" in df else 0)
    min_bl = st.slider("Min backlinks", 0, min_backlinks, 0, step=max(1, min_backlinks//20 or 1))

# ==== Apply filters ====
mask = (
    df["competitor"].isin(comp_pick) &
    df["priority"].isin(prio_pick) &
    df["backlink_signal"].isin(sig_pick) &
    (df["backlink_count"] >= min_bl)
)
f = df[mask].copy()

# Sort by impact desc if present
if "impact" in f.columns:
    f = f.sort_values(["impact","backlink_count"], ascending=[False, False])

# ==== KPIs ====
col1, col2, col3, col4 = st.columns(4)
col1.metric("Items", len(f))
col2.metric("Total backlinks", int(f["backlink_count"].sum()) if "backlink_count" in f else 0)
col3.metric("Avg impact", round(f["impact"].mean(), 2) if "impact" in f and len(f) else 0)
top_comp = f.groupby("competitor")["impact"].sum().sort_values(ascending=False)

if len(top_comp):
    best_comp = top_comp.index[0]
    best_val  = float(top_comp.iloc[0])
    col4.metric("Top competitor by total impact", f"{best_comp}: {best_val:.1f}")
else:
    col4.metric("Top competitor by total impact", "—")


# ==== Table ====
show_cols = [c for c in ["date","competitor","source","what_changed","why_it_matters","priority",
                         "action","backlink_count","backlink_signal","impact"] if c in f.columns]
st.markdown("### Results")
st.dataframe(f[show_cols], use_container_width=True)

# ==== Chart: top items by impact ====
if "impact" in f.columns and len(f):
    st.markdown("### Top items by impact")
    top_n = st.slider("How many to chart?", 5, min(30, len(f)), 10)
    top = f.sort_values("impact", ascending=False).head(top_n)

    plt.figure(figsize=(10, 5))
    plt.barh(top["competitor"] + "  •  " + top["action"].str.slice(0, 40), top["impact"])
    plt.gca().invert_yaxis()
    plt.xlabel("Impact")
    plt.tight_layout()
    st.pyplot(plt.gcf())

# ==== Download ====
st.markdown("### Download filtered CSV")
st.download_button("Download CSV", data=f.to_csv(index=False).encode("utf-8"),
                   file_name="ci_filtered.csv", mime="text/csv")

st.caption("Tip: impact = priority_weight × log10(backlink_count + 1)")
