import pandas as pd

df = pd.read_csv("data/synthetic_leads.csv")
print("count:", len(df))                       # must be > 200
print(df["need"].str.len().describe())         # varied text lengths
print(df["budget_band"].value_counts())        # spread across bands
print(df.head(10))                             # eyeball the styles