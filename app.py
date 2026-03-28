import io
import json
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI-Assisted Data Wrangler & Visualizer", layout="wide")


# =====================================================
# SESSION STATE
# =====================================================
def init_state():
    if "df" not in st.session_state:
        st.session_state["df"] = None
    if "original_df" not in st.session_state:
        st.session_state["original_df"] = None
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "log" not in st.session_state:
        st.session_state["log"] = []
    if "file_name" not in st.session_state:
        st.session_state["file_name"] = None


def reset_session():
    st.session_state["df"] = None
    st.session_state["original_df"] = None
    st.session_state["history"] = []
    st.session_state["log"] = []
    st.session_state["file_name"] = None


def save_history():
    if st.session_state["df"] is not None:
        st.session_state["history"].append(st.session_state["df"].copy())


def undo_last_step():
    if st.sidebar.button("Undo last step"):
    if st.session_state["history"]:
        undo_last_step()
        st.sidebar.success("Last step undone.")
        st.rerun()
    else:
        st.sidebar.warning("Nothing to undo.")


def add_log(action, details="", columns=None):
    st.session_state["log"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details,
        "columns": columns if columns else []
    })


# =====================================================
# HELPERS
# =====================================================
@st.cache_data
def load_data(file_name, file_bytes):
    file_name = file_name.lower()
    buffer = io.BytesIO(file_bytes)

    if file_name.endswith(".csv"):
        return pd.read_csv(buffer)
    elif file_name.endswith(".xlsx"):
        return pd.read_excel(buffer)
    elif file_name.endswith(".json"):
        return pd.read_json(buffer)
    else:
        raise ValueError("Unsupported file type")


def numeric_columns(df):
    return df.select_dtypes(include=["number"]).columns.tolist()


def make_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="cleaned_data")
    return output.getvalue()


# =====================================================
# MAIN
# =====================================================
def main():
    init_state()

    st.sidebar.markdown("### Choose Page")

    page = st.sidebar.radio(
        "",
        ["Upload & Overview", "Cleaning Studio", "Visualization", "Export & Report"],
        label_visibility="collapsed"
    )

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    st.sidebar.markdown("## Session Controls")

    if st.sidebar.button("Reset session"):
        reset_session()
        st.sidebar.success("Session reset.")
        st.rerun()

    if st.session_state["history"]:
        if st.sidebar.button("Undo last step"):
            undo_last_step()
            st.sidebar.success("Last step undone.")
            st.rerun()

    st.sidebar.markdown("---")
    if st.session_state["df"] is not None:
        st.sidebar.info(
            f"Rows: {st.session_state['df'].shape[0]}\n\nColumns: {st.session_state['df'].shape[1]}"
        )
    else:
        st.sidebar.warning("No dataset loaded.")

    if page == "Upload & Overview":
        page_upload_overview()
    elif page == "Cleaning Studio":
        page_cleaning()
    elif page == "Visualization":
        page_visualization()
    elif page == "Export & Report":
        page_export()


# =====================================================
# PAGE A
# =====================================================
def page_upload_overview():
    st.title("📊 Upload & Overview")

    uploaded_file = st.file_uploader("Upload CSV, Excel, or JSON", type=["csv", "xlsx", "json"])

    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file.name, uploaded_file.getvalue())
            st.session_state["df"] = df.copy()
            st.session_state["original_df"] = df.copy()
            st.session_state["history"] = []
            st.session_state["log"] = []
            st.session_state["file_name"] = uploaded_file.name
            add_log("Load file", uploaded_file.name, list(df.columns))
            st.success("File uploaded successfully.")
        except Exception as e:
            st.error(f"Error loading file: {e}")

    if st.session_state["df"] is None:
        st.info("Please upload a dataset to begin.")
        return

    df = st.session_state["df"]
    total_missing = int(df.isnull().sum().sum())

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing Values", total_missing)

    st.subheader("Column Types")
    dtype_df = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str)
    })
    st.dataframe(dtype_df, use_container_width=True)

    st.subheader("Preview")
    st.dataframe(df.head(10), use_container_width=True)

    st.subheader("Missing Values by Column")
    missing_df = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": df.isnull().sum().values,
        "Missing Percentage": (df.isnull().mean() * 100).round(2).values
    })
    st.dataframe(missing_df, use_container_width=True)

    st.subheader("Numeric Summary")
    num_df = df.select_dtypes(include="number")
    if not num_df.empty:
        st.dataframe(num_df.describe(), use_container_width=True)
    else:
        st.info("No numeric columns found.")


# =====================================================
# PAGE B
# =====================================================
def page_cleaning():
    st.title("🧹 Cleaning Studio")

    if st.session_state["df"] is None:
        st.warning("Upload data first.")
        return

    df = st.session_state["df"].copy()
    all_cols = df.columns.tolist()
    num_cols = numeric_columns(df)

    st.dataframe(df.head(10), use_container_width=True)

    # 1. Missing Values
    st.subheader("1. Missing Values")

    select_all_mv = st.checkbox("Select all columns for missing value handling")

    mv_cols = st.multiselect(
        "Columns for missing values",
        all_cols,
        default=all_cols if select_all_mv else []
    )

    mv_action = st.selectbox(
        "Action",
        [
            "Do nothing",
            "Drop rows",
            "Fill mean",
            "Fill median",
            "Fill mode",
            "Fill value",
            "Forward fill",
            "Backward fill",
        ],
        key="mv_action"
    )

    fill_value = ""
    if mv_action == "Fill value":
        fill_value = st.text_input("Custom value", key="fill_value")

    if st.button("Apply Missing Handling"):
        if not mv_cols:
            st.warning("Please select at least one column.")
        else:
            save_history()

            before_rows = len(df)
            before_missing = int(df[mv_cols].isnull().sum().sum())

            if mv_action == "Drop rows":
                df = df.dropna(subset=mv_cols)

            elif mv_action == "Fill mean":
                for col in mv_cols:
                    if col in num_cols:
                        s = pd.to_numeric(df[col], errors="coerce")
                        df[col] = s.fillna(s.mean())

            elif mv_action == "Fill median":
                for col in mv_cols:
                    if col in num_cols:
                        s = pd.to_numeric(df[col], errors="coerce")
                        df[col] = s.fillna(s.median())

            elif mv_action == "Fill mode":
                for col in mv_cols:
                    mode_val = df[col].mode(dropna=True)
                    if not mode_val.empty:
                        df[col] = df[col].fillna(mode_val.iloc[0])

            elif mv_action == "Fill value":
                for col in mv_cols:
                    df[col] = df[col].fillna(fill_value)

            elif mv_action == "Forward fill":
                df[mv_cols] = df[mv_cols].ffill()

            elif mv_action == "Backward fill":
                df[mv_cols] = df[mv_cols].bfill()

            after_rows = len(df)
            after_missing = int(df[mv_cols].isnull().sum().sum())
            total_missing_now = int(df.isnull().sum().sum())

            st.session_state["df"] = df
            add_log("Missing value handling", mv_action, mv_cols)

            if mv_action == "Drop rows":
                st.success("Row drop applied successfully.")
            else:
                st.success("Missing value handling applied successfully.")

            st.info(f"Rows: {before_rows} → {after_rows}")
            st.info(f"Missing values: {before_missing} → {after_missing}")
            st.success(f"Total missing values now: {total_missing_now}")

    # 2. Duplicates
    st.subheader("2. Duplicates")

    dup_subset = st.multiselect(
        "Subset columns for duplicate check (optional)",
        all_cols,
        key="dup_subset"
    )

    if st.button("Remove Duplicates"):
        save_history()

        before_rows = len(df)
        before_duplicates = int(df.duplicated(subset=dup_subset if dup_subset else None).sum())

        if dup_subset:
            df = df.drop_duplicates(subset=dup_subset)
        else:
            df = df.drop_duplicates()

        after_rows = len(df)
        after_duplicates = int(df.duplicated(subset=dup_subset if dup_subset else None).sum())

        st.session_state["df"] = df
        add_log("Remove duplicates", f"Removed {before_rows - after_rows} rows", dup_subset)

        st.success("Duplicates removed successfully.")
        st.info(f"Rows: {before_rows} → {after_rows}")
        st.info(f"Duplicate rows: {before_duplicates} → {after_duplicates}")

    # 3. Data Type Conversion
    st.subheader("3. Data Type Conversion")

    type_col = st.selectbox("Column to convert", all_cols, key="type_col")
    target_type = st.selectbox(
        "Convert to",
        ["numeric", "category", "datetime", "string"],
        key="target_type"
    )

    if st.button("Convert Column Type"):
        save_history()
        try:
            if target_type == "numeric":
                df[type_col] = pd.to_numeric(df[type_col], errors="coerce")
            elif target_type == "category":
                df[type_col] = df[type_col].astype("category")
            elif target_type == "datetime":
                df[type_col] = pd.to_datetime(df[type_col], errors="coerce")
            elif target_type == "string":
                df[type_col] = df[type_col].astype(str)

            st.session_state["df"] = df
            add_log("Convert type", target_type, [type_col])
            st.success("Type conversion applied successfully.")
        except Exception as e:
            st.error(f"Conversion error: {e}")

    # 4. Column Operations
    st.subheader("4. Column Operations")

    rename_col = st.selectbox("Column to rename", all_cols, key="rename_col")
    new_name = st.text_input("New column name", key="new_name")
    drop_col = st.selectbox("Column to drop", all_cols, key="drop_col")

    if st.button("Rename Column"):
        if new_name.strip():
            save_history()
            df = df.rename(columns={rename_col: new_name.strip()})
            st.session_state["df"] = df
            add_log("Rename column", f"{rename_col} -> {new_name.strip()}", [rename_col])
            st.success("Column renamed successfully.")

    if st.button("Drop Column"):
        save_history()
        df = df.drop(columns=[drop_col])
        st.session_state["df"] = df
        add_log("Drop column", drop_col, [drop_col])
        st.success("Column dropped successfully.")


# =====================================================
# PAGE C
# =====================================================
# =====================================================
# PAGE C
# =====================================================
def page_visualization():
    st.title("📈 Visualization")

    if st.session_state["df"] is None:
        st.warning("Upload data first.")
        return

    df = st.session_state["df"].copy()
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    all_cols = df.columns.tolist()

    chart = st.selectbox(
        "Choose chart type",
        ["Histogram", "Box Plot", "Scatter Plot", "Line Chart", "Bar Chart", "Heatmap"]
    )

    fig, ax = plt.subplots(figsize=(9, 5))

    try:
        if chart == "Histogram":
            if not num_cols:
                st.warning("No numeric columns found.")
                return

            col = st.selectbox("Numeric column", num_cols)
            values = pd.to_numeric(df[col], errors="coerce").dropna()

            ax.hist(values, bins=20)
            ax.set_title(f"Histogram of {col}")
            ax.set_xlabel(col)
            ax.set_ylabel("Frequency")

        elif chart == "Box Plot":
            if not num_cols:
                st.warning("No numeric columns found.")
                return

            col = st.selectbox("Numeric column", num_cols, key="box_col")
            values = pd.to_numeric(df[col], errors="coerce").dropna()

            ax.boxplot(values)
            ax.set_title(f"Box Plot of {col}")
            ax.set_ylabel(col)

        elif chart == "Scatter Plot":
            if len(num_cols) < 2:
                st.warning("Need at least two numeric columns.")
                return

            x = st.selectbox("X column", num_cols, key="scatter_x")
            y = st.selectbox("Y column", num_cols, key="scatter_y")

            x_values = pd.to_numeric(df[x], errors="coerce")
            y_values = pd.to_numeric(df[y], errors="coerce")

            ax.scatter(x_values, y_values)
            ax.set_title(f"{y} vs {x}")
            ax.set_xlabel(x)
            ax.set_ylabel(y)

        elif chart == "Line Chart":
            if not num_cols:
                st.warning("No numeric columns found.")
                return

            x = st.selectbox("X column", all_cols, key="line_x")
            y = st.selectbox("Y column", num_cols, key="line_y")

            plot_df = df[[x, y]].dropna().copy()
            plot_df = plot_df.sort_values(by=x)

            ax.plot(plot_df[x], pd.to_numeric(plot_df[y], errors="coerce"), marker="o")
            ax.set_title(f"Line Chart of {y}")
            ax.set_xlabel(x)
            ax.set_ylabel(y)
            ax.tick_params(axis="x", rotation=45)

        elif chart == "Bar Chart":
            source_cols = cat_cols if cat_cols else all_cols
            col = st.selectbox("Category column", source_cols, key="bar_col")

            counts = df[col].astype(str).value_counts().head(10)

            ax.bar(counts.index, counts.values)
            ax.set_title(f"Bar Chart of {col}")
            ax.set_xlabel(col)
            ax.set_ylabel("Count")
            ax.tick_params(axis="x", rotation=45)

        elif chart == "Heatmap":
            if len(num_cols) < 2:
                st.warning("Need at least two numeric columns.")
                return

            corr = df[num_cols].corr(numeric_only=True)

            im = ax.imshow(corr, aspect="auto")
            ax.set_xticks(range(len(corr.columns)))
            ax.set_xticklabels(corr.columns, rotation=45, ha="right")
            ax.set_yticks(range(len(corr.index)))
            ax.set_yticklabels(corr.index)
            ax.set_title("Correlation Heatmap")
            fig.colorbar(im, ax=ax)

        st.pyplot(fig)

    except Exception as e:
        st.error(f"Visualization error: {e}")


# =====================================================
# PAGE D
# =====================================================
def page_export():
    st.title("📦 Export & Report")

    if st.session_state["df"] is None:
        st.warning("No dataset available.")
        return

    df = st.session_state["df"]

    st.subheader("Preview")
    st.dataframe(df.head(10), use_container_width=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    excel_data = make_excel(df)

    st.download_button("Download CSV", csv_data, "cleaned_data.csv", mime="text/csv")
    st.download_button(
        "Download Excel",
        excel_data,
        "cleaned_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("Transformation Log")
    if st.session_state["log"]:
        log_df = pd.DataFrame(st.session_state["log"])
        st.dataframe(log_df, use_container_width=True)

        report_text = json.dumps(st.session_state["log"], indent=2)
        st.download_button("Download Report", report_text, "report.json", mime="application/json")
    else:
        st.info("No transformations yet.")


if __name__ == "__main__":
    main()
