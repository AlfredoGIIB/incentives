from pathlib import Path
import os

import pandas as pd
import streamlit as st


LOCAL_DATA_PATH = Path("data/incentives.csv")
CSV_SOURCE = os.getenv("INCENTIVES_CSV_URL") or str(LOCAL_DATA_PATH)


st.set_page_config(
    page_title="Incentives Report",
    page_icon="🏟️",
    layout="wide",
)


@st.cache_data
def load_csv(source: str) -> pd.DataFrame:
    try:
        return pd.read_csv(source, header=None, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(source, header=None, encoding="latin1")


def parse_incentives(raw: pd.DataFrame):
    rate_row = raw.iloc[2]
    header_row = raw.iloc[3].fillna("").astype(str).str.strip()
    category_row = raw.iloc[0].ffill().fillna("")
    cadence_row = raw.iloc[1].ffill().fillna("")

    df = raw.iloc[4:].copy()
    df.columns = header_row
    df = df.dropna(how="all")

    player_col = "Players"
    team_col = "Team"
    total_col = "$RD"
    item_cols = [
        col for col in df.columns if col and col not in {player_col, team_col, total_col}
    ]

    counts = df[item_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    rates = pd.to_numeric(rate_row.iloc[[list(header_row).index(col) for col in item_cols]], errors="coerce")
    rates.index = item_cols
    rates = rates.fillna(0)

    contributions = counts.mul(rates, axis=1)
    summary = pd.DataFrame(
        {
            "Player": df[player_col].astype(str),
            "Team": df[team_col].astype(str),
            "Total $RD": pd.to_numeric(df[total_col], errors="coerce").fillna(contributions.sum(axis=1)),
            "Calculated $RD": contributions.sum(axis=1),
        }
    )
    summary["Difference"] = summary["Total $RD"] - summary["Calculated $RD"]

    meta = {}
    for item in item_cols:
        idx = list(header_row).index(item)
        meta[item] = {
            "Category": str(category_row.iloc[idx]).title(),
            "Frequency": str(cadence_row.iloc[idx]).title(),
            "Rate": rates[item],
        }

    long_rows = []
    for item in item_cols:
        item_frame = pd.DataFrame(
            {
                "Player": summary["Player"],
                "Team": summary["Team"],
                "Item": item,
                "Category": meta[item]["Category"],
                "Frequency": meta[item]["Frequency"],
                "Rate": meta[item]["Rate"],
                "Count": counts[item].values,
                "Amount $RD": contributions[item].values,
            }
        )
        long_rows.append(item_frame)

    detail = pd.concat(long_rows, ignore_index=True)
    detail = detail[detail["Count"] != 0].copy()
    return summary, detail, rates


def money(value):
    return f"RD${value:,.0f}"


raw_data = load_csv(CSV_SOURCE)
summary, detail, rates = parse_incentives(raw_data)

st.title("Incentives Report")
st.caption("Ranking de jugadores, desglose por item y contribuciones calculadas desde el CSV.")

with st.sidebar:
    st.header("Filtros")
    teams = ["All"] + sorted(summary["Team"].dropna().unique().tolist())
    selected_team = st.selectbox("Team", teams)
    top_n = st.slider("Top jugadores", min_value=5, max_value=30, value=10, step=1)
    amount_view = st.radio(
        "Items a mostrar",
        ["Solo ganancias", "Ganancias y penalidades"],
        horizontal=False,
    )

filtered_summary = summary.copy()
filtered_detail = detail.copy()
if selected_team != "All":
    filtered_summary = filtered_summary[filtered_summary["Team"] == selected_team]
    filtered_detail = filtered_detail[filtered_detail["Team"] == selected_team]

if amount_view == "Solo ganancias":
    filtered_detail = filtered_detail[filtered_detail["Amount $RD"] > 0]

top_players = filtered_summary.sort_values("Total $RD", ascending=False).head(top_n)
item_totals = (
    filtered_detail.groupby(["Item", "Category"], as_index=False)["Amount $RD"]
    .sum()
    .sort_values("Amount $RD", ascending=False)
)

total_pool = filtered_summary["Total $RD"].sum()
avg_player = filtered_summary["Total $RD"].mean()
top_player_name = top_players.iloc[0]["Player"] if not top_players.empty else "-"
top_player_total = top_players.iloc[0]["Total $RD"] if not top_players.empty else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Jugadores", f"{len(filtered_summary):,}")
kpi2.metric("Total incentivos", money(total_pool))
kpi3.metric("Promedio jugador", money(avg_player))
kpi4.metric("Lider", top_player_name, money(top_player_total))

tab_summary, tab_players, tab_items, tab_data = st.tabs(
    ["Resumen", "Jugadores", "Items", "Datos"]
)

with tab_summary:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Mayores ganancias por jugador")
        chart_data = top_players.set_index("Player")["Total $RD"]
        st.bar_chart(chart_data)
    with right:
        st.subheader("Items con mayor aporte")
        st.dataframe(
            item_totals.head(10).assign(**{"Amount $RD": item_totals.head(10)["Amount $RD"].map(money)}),
            hide_index=True,
            use_container_width=True,
        )

with tab_players:
    st.subheader("Ranking y mejores items por jugador")
    selected_player = st.selectbox(
        "Jugador",
        top_players["Player"].tolist() if not top_players.empty else [],
    )

    st.dataframe(
        top_players.assign(
            **{
                "Total $RD": top_players["Total $RD"].map(money),
                "Calculated $RD": top_players["Calculated $RD"].map(money),
                "Difference": top_players["Difference"].map(money),
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    if selected_player:
        player_items = (
            filtered_detail[filtered_detail["Player"] == selected_player]
            .sort_values("Amount $RD", ascending=False)
            .copy()
        )
        st.markdown(f"**Detalle de {selected_player}**")
        st.dataframe(
            player_items.assign(
                **{
                    "Rate": player_items["Rate"].map(money),
                    "Amount $RD": player_items["Amount $RD"].map(money),
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

with tab_items:
    st.subheader("Aporte total por item")
    st.bar_chart(item_totals.set_index("Item")["Amount $RD"])
    st.dataframe(
        item_totals.assign(**{"Amount $RD": item_totals["Amount $RD"].map(money)}),
        hide_index=True,
        use_container_width=True,
    )

with tab_data:
    st.subheader("Datos calculados")
    st.dataframe(filtered_summary, hide_index=True, use_container_width=True)

    export = filtered_detail.merge(
        filtered_summary[["Player", "Total $RD"]],
        on="Player",
        how="left",
    )
    st.download_button(
        "Descargar detalle filtrado",
        data=export.to_csv(index=False).encode("utf-8"),
        file_name="incentives_report_detail.csv",
        mime="text/csv",
    )
