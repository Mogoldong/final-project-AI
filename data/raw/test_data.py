import pandas as pd

CSV_PATH = "data/raw/SampleDataset.csv"

df = pd.read_csv(CSV_PATH)
print(df.head())