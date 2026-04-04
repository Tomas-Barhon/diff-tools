from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


def _load_results(path: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists() or not csv_path.is_file():
        raise FileNotFoundError(f"Results file not found: {csv_path}")
    return pd.read_csv(csv_path)


def _discover_results_files() -> list[str]:
    candidates: list[Path] = []
    search_roots = [Path.cwd(), Path.cwd() / "06"]
    for root in search_roots:
        if not root.exists() or not root.is_dir():
            continue
        candidates.extend(root.glob("results*.csv"))

    unique = sorted({str(path) for path in candidates})
    return unique


def _default_results_path() -> str:
    for candidate in [Path("results.csv"), Path("06/results.csv")]:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    discovered = _discover_results_files()
    if discovered:
        return discovered[0]
    return "results.csv"


def _detect_columns(df: pd.DataFrame) -> tuple[str, list[str]]:
    metric_column = df.columns[-1]
    param_columns = [column for column in df.columns if column != metric_column]
    return metric_column, param_columns


def _coerce_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def main() -> None:
    st.set_page_config(page_title="Hyperparameter Results Dashboard", layout="wide")
    st.title("Hyperparameter Results Dashboard")

    st.sidebar.header("Data Source")
    default_path = _default_results_path()
    discovered_files = _discover_results_files()
    if discovered_files:
        selected_file = st.sidebar.selectbox(
            "Discovered results files",
            options=discovered_files,
            index=discovered_files.index(default_path)
            if default_path in discovered_files
            else 0,
        )
        results_path = st.sidebar.text_input("Results CSV path", value=selected_file)
    else:
        results_path = st.sidebar.text_input("Results CSV path", value=default_path)

    try:
        df = _load_results(results_path)
    except Exception as error:
        st.error(str(error))
        st.info("Set a valid CSV path in the sidebar to start exploring results.")
        if discovered_files:
            st.info("Discovered files: " + ", ".join(discovered_files))
        return

    if df.empty:
        st.warning("The selected CSV is empty.")
        return

    default_metric, all_param_columns = _detect_columns(df)
    metric_column = st.sidebar.selectbox(
        "Metric column",
        options=list(df.columns),
        index=list(df.columns).index(default_metric),
    )
    param_columns = [column for column in df.columns if column != metric_column]

    if not param_columns:
        st.warning("No parameter columns found (only metric column present).")
        return

    working_df = df.copy()
    working_df[metric_column] = _coerce_numeric(working_df[metric_column])
    valid_df = working_df[working_df[metric_column].notna()].copy()

    st.sidebar.header("Ranking")
    metric_mode = st.sidebar.selectbox(
        "Metric direction",
        options=["max", "min"],
        index=0,
        help="Affects Top-K display only; all rows remain in analysis.",
    )
    top_k = st.sidebar.slider("Top-K", min_value=1, max_value=50, value=5)

    st.sidebar.header("Filter")
    selected_rows = valid_df
    for column in param_columns:
        unique_values = selected_rows[column].dropna().unique().tolist()
        if not unique_values or len(unique_values) > 20:
            continue
        selected_values = st.sidebar.multiselect(
            f"{column}", options=sorted(unique_values), default=sorted(unique_values)
        )
        if selected_values:
            selected_rows = selected_rows[selected_rows[column].isin(selected_values)]

    total_runs = len(df)
    valid_runs = len(valid_df)
    filtered_runs = len(selected_rows)
    failed_runs = total_runs - valid_runs

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total rows", total_runs)
    col2.metric("Valid metric rows", valid_runs)
    col3.metric("Failed/non-numeric", failed_runs)
    col4.metric("Filtered rows", filtered_runs)

    if selected_rows.empty:
        st.warning("No rows match the selected filters.")
        return

    st.subheader("Top Configurations")
    ascending = metric_mode == "min"
    top_df = selected_rows.sort_values(metric_column, ascending=ascending).head(top_k)
    st.dataframe(top_df, use_container_width=True)

    st.subheader("Single Parameter Effect")
    single_param = st.selectbox("Parameter", options=param_columns)
    agg_func = st.selectbox("Aggregation", options=["mean", "median"], index=0)

    grouped = (
        selected_rows.groupby(single_param, as_index=False)[metric_column]
        .agg([agg_func, "count", "std"])
        .reset_index()
    )
    grouped = grouped.rename(columns={agg_func: "aggregate"})

    fig_single = px.bar(
        grouped,
        x=single_param,
        y="aggregate",
        hover_data=["count", "std"],
        title=f"{agg_func.title()} {metric_column} by {single_param}",
    )
    st.plotly_chart(fig_single, use_container_width=True)

    st.subheader("Two-Parameter Interaction")
    c1, c2 = st.columns(2)
    with c1:
        x_param = st.selectbox("X parameter", options=param_columns, index=0)
    with c2:
        y_param = st.selectbox(
            "Y parameter",
            options=param_columns,
            index=1 if len(param_columns) > 1 else 0,
        )

    if x_param == y_param:
        st.info("Choose two different parameters to show interaction heatmap.")
    else:
        pivot = selected_rows.pivot_table(
            index=y_param,
            columns=x_param,
            values=metric_column,
            aggfunc=agg_func,
        )
        fig_heatmap = px.imshow(
            pivot,
            aspect="auto",
            title=f"{agg_func.title()} {metric_column} for {x_param} x {y_param}",
            labels={"x": x_param, "y": y_param, "color": metric_column},
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    st.subheader("Metric Distribution")
    fig_hist = px.histogram(
        selected_rows,
        x=metric_column,
        nbins=min(30, max(10, len(selected_rows) // 2)),
        title=f"Distribution of {metric_column}",
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.subheader("Raw Data")
    st.dataframe(selected_rows, use_container_width=True)

    st.caption(
        "Next improvements: partial dependence curves, Optuna importance charts, and repeat-seed aggregation."
    )


if __name__ == "__main__":
    main()
