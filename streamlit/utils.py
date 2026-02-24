"""Shared data loading and preprocessing utilities."""
import pathlib
import pandas as pd
import streamlit as st

DATA_DIR = pathlib.Path(__file__).parent

@st.cache_data
def load_res_input() -> pd.DataFrame:
    """Load and clean res_input.csv (Hamada's personal records)."""
    df = pd.read_csv(
        DATA_DIR / "res_input.csv",
        header=0,
        names=["num", "date", "match", "ForS", "member", "rank", "score", "pm", "_empty", "cumsum"],
        dtype=str,
    )
    # Drop empty/NA rows
    df = df[df["date"].notna() & (df["date"] != "")].copy()
    df = df[df["pm"] != "#N/A"].copy()

    # Type conversions
    df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d")
    df["num"] = pd.to_numeric(df["num"], errors="coerce")
    df["match"] = pd.to_numeric(df["match"], errors="coerce")
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["pm"] = pd.to_numeric(df["pm"], errors="coerce")
    df["cumsum"] = pd.to_numeric(df["cumsum"], errors="coerce")

    df = df.drop(columns=["_empty"])
    df = df.sort_values("num").reset_index(drop=True)
    return df


@st.cache_data
def load_set_res() -> pd.DataFrame:
    """Load and clean set_res.csv, convert wide -> long format per player."""
    df = pd.read_csv(DATA_DIR / "set_res.csv")
    # Drop completely empty rows
    df = df.dropna(how="all")
    df = df[df["date"].notna() & (df["date"] != "")].copy()
    df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d")
    df["match"] = pd.to_numeric(df["match"], errors="coerce")
    df = df.sort_values(["date", "match"]).reset_index(drop=True)
    return df


def set_res_to_long(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert set_res wide format to long format with columns:
    date, member, match, rule, player, score, rank
    """
    records = []
    rank_cols = [("1st_name", "1st_score", 1),
                 ("2nd_name", "2nd_score", 2),
                 ("3rd_name", "3rd_score", 3),
                 ("4th_name", "4th_score", 4)]
    for _, row in df.iterrows():
        for name_col, score_col, rank in rank_cols:
            player = row.get(name_col, "")
            score = row.get(score_col, None)
            if pd.notna(player) and player != "":
                records.append({
                    "date": row["date"],
                    "member": row["member"],
                    "match": row["match"],
                    "rule": row.get("rule", ""),
                    "player": str(player).strip(),
                    "score": pd.to_numeric(score, errors="coerce"),
                    "rank": rank,
                })
    long_df = pd.DataFrame(records)
    # Normalize player name casing (e.g. "hamada" -> "Hamada")
    long_df["player"] = long_df["player"].str.capitalize()
    return long_df
