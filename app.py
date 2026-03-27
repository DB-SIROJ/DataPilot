import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Data Wrangler App", layout="wide")

# -----------------------
# SESSION STATE INIT
# -----------------------
if "df" not in st.session_state:
    st.session_state["df"] = None

if "log" not in st.session_state:
    st.session_state["log"] = []

# -----------------------
# SIDEBAR
# -----------------------
page = st.sidebar.selectbox("Choose Page", [
    "Upload & Overview",
    "Cleaning Studio",
    "Visualization",
    "Export & Report"
])

# -----------------------
# PAGE A — Upload
# -----------------------
if page == "Upload & Overview":

    st.title("📊 Upload & Overview")

    file = st.file_uploader("Upload CSV, Excel, or JSON", type=["csv", "xlsx", "json"])

    if file is not None:

        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        elif file.name.endswith(".json"):
            df = pd.read_json(file)

        st.session_state["df"] = df
        st.session_state["log"] = []  # reset log

        st.success("File uploaded!")

        col1, col2 = st.columns(2)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])

        st.subheader("Column Types")
        st.dataframe(df.dtypes)

        st.subheader("Preview")
        st.dataframe(df.head())

        st.subheader("Missing Values")
        st.dataframe(df.isnull().sum())

        st.subheader("Duplicates")
        st.write(df.duplicated().sum())

# -----------------------
# PAGE B — Cleaning
# -----------------------
elif page == "Cleaning Studio":

    st.title("🧹 Cleaning Studio")

    if st.session_state["df"] is None:
        st.warning("Upload data first")
    else:
        df = st.session_state["df"]

        st.dataframe(df.head())

        # -------- Missing --------
        st.subheader("Missing Values")

        col = st.selectbox("Column", df.columns)
        action = st.selectbox("Action", [
            "Do nothing",
            "Drop rows",
            "Fill mean",
            "Fill median",
            "Fill value"
        ])

        value = None
        if action == "Fill value":
            value = st.text_input("Enter value")

        if st.button("Apply Missing Handling"):
            if action == "Drop rows":
                df = df.dropna(subset=[col])
                st.session_state["log"].append(f"Dropped rows with missing in {col}")
            elif action == "Fill mean":
                df[col] = df[col].fillna(df[col].mean())
                st.session_state["log"].append(f"Filled missing in {col} with mean")
            elif action == "Fill median":
                df[col] = df[col].fillna(df[col].median())
                st.session_state["log"].append(f"Filled missing in {col} with median")
            elif action == "Fill value":
                df[col] = df[col].fillna(value)
                st.session_state["log"].append(f"Filled missing in {col} with {value}")

            st.session_state["df"] = df
            st.success("Done")

        # -------- Duplicates --------
        st.subheader("Duplicates")

        if st.button("Remove Duplicates"):
            df = df.drop_duplicates()
            st.session_state["df"] = df
            st.session_state["log"].append("Removed duplicate rows")
            st.success("Removed")

        # -------- Outliers --------
        st.subheader("Outliers")

        num_cols = df.select_dtypes(include=["number"]).columns

        if len(num_cols) > 0:
            col = st.selectbox("Numeric column", num_cols)

            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            low = Q1 - 1.5 * IQR
            high = Q3 + 1.5 * IQR

            if st.button("Remove Outliers"):
                df = df[(df[col] >= low) & (df[col] <= high)]
                st.session_state["df"] = df
                st.session_state["log"].append(f"Removed outliers in {col}")
                st.success("Outliers removed")

        # -------- Scaling --------
        st.subheader("Scaling")

        if len(num_cols) > 0:
            col = st.selectbox("Scale column", num_cols)
            method = st.selectbox("Method", ["MinMax", "Z-score"])

            if st.button("Apply Scaling"):
                if method == "MinMax":
                    df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
                else:
                    df[col] = (df[col] - df[col].mean()) / df[col].std()

                st.session_state["df"] = df
                st.session_state["log"].append(f"Applied {method} scaling on {col}")
                st.success("Scaled")

        # -------- Categorical --------
        st.subheader("Categorical Cleaning")

        cat_cols = df.select_dtypes(include=["object"]).columns

        if len(cat_cols) > 0:
            col = st.selectbox("Categorical column", cat_cols)

            option = st.selectbox("Standardize", [
                "None", "Lower", "Upper", "Title", "Trim"
            ])

            if st.button("Apply Standardize"):
                if option == "Lower":
                    df[col] = df[col].str.lower()
                elif option == "Upper":
                    df[col] = df[col].str.upper()
                elif option == "Title":
                    df[col] = df[col].str.title()
                elif option == "Trim":
                    df[col] = df[col].str.strip()

                st.session_state["df"] = df
                st.session_state["log"].append(f"Standardized {col} using {option}")
                st.success("Done")

            old = st.text_input("Old value")
            new = st.text_input("New value")

            if st.button("Apply Mapping"):
                df[col] = df[col].replace(old, new)
                st.session_state["df"] = df
                st.session_state["log"].append(f"Mapped {old} to {new} in {col}")
                st.success("Mapped")

        # -------- Column Ops --------
        st.subheader("Column Operations")

        col = st.selectbox("Rename column", df.columns)
        new_name = st.text_input("New name")

        if st.button("Rename"):
            df = df.rename(columns={col: new_name})
            st.session_state["df"] = df
            st.session_state["log"].append(f"Renamed column {col} to {new_name}")
            st.success("Renamed")

        drop_col = st.selectbox("Drop column", df.columns)

        if st.button("Drop"):
            df = df.drop(columns=[drop_col])
            st.session_state["df"] = df
            st.session_state["log"].append(f"Dropped column {drop_col}")
            st.success("Dropped")

# -----------------------
# PAGE C — Visualization
# -----------------------
elif page == "Visualization":

    st.title("📊 Visualization")

    if st.session_state["df"] is None:
        st.warning("Upload data first")
    else:
        df = st.session_state["df"]

        chart = st.selectbox("Chart", [
            "Histogram", "Box", "Scatter", "Line", "Bar", "Heatmap"
        ])

        num_cols = df.select_dtypes(include=["number"]).columns
        cat_cols = df.select_dtypes(include=["object"]).columns

        fig, ax = plt.subplots()

        if chart == "Histogram":
            col = st.selectbox("Column", num_cols)
            ax.hist(df[col])

        elif chart == "Box":
            col = st.selectbox("Column", num_cols)
            sns.boxplot(y=df[col], ax=ax)

        elif chart == "Scatter":
            x = st.selectbox("X", num_cols)
            y = st.selectbox("Y", num_cols)
            ax.scatter(df[x], df[y])

        elif chart == "Line":
            x = st.selectbox("X", df.columns)
            y = st.selectbox("Y", num_cols)
            ax.plot(df[x], df[y])

        elif chart == "Bar":
            col = st.selectbox("Category", cat_cols)
            df[col].value_counts().plot(kind="bar", ax=ax)

        elif chart == "Heatmap":
            sns.heatmap(df.corr(numeric_only=True), annot=True, ax=ax)

        st.pyplot(fig)

# -----------------------
# PAGE D — Export
# -----------------------
elif page == "Export & Report":

    st.title("📦 Export & Report")

    if st.session_state["df"] is None:
        st.warning("No dataset available")
    else:
        df = st.session_state["df"]

        st.subheader("Preview")
        st.dataframe(df.head())

        # CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "cleaned_data.csv")

        # Excel
        df.to_excel("temp.xlsx", index=False)
        with open("temp.xlsx", "rb") as f:
            st.download_button("Download Excel", f, "cleaned_data.xlsx")

        # Log
        st.subheader("Transformation Log")

        if st.session_state["log"]:
            for step in st.session_state["log"]:
                st.write("•", step)
        else:
            st.write("No transformations yet")

        log_text = "\n".join(st.session_state["log"])
        st.download_button("Download Report", log_text, "report.txt")
