import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Generate synthetic data
num_samples = 5000  # Change this to increase dataset size

data = {
    "BloodSugar": np.random.randint(70, 200, num_samples),
    "Cholesterol": np.random.randint(150, 300, num_samples),
    "LiverEnzyme": np.random.randint(10, 80, num_samples),
    "KidneyFunction": np.random.uniform(0.5, 2.5, num_samples),
    "ThyroidLevel": np.random.uniform(2.0, 5.0, num_samples),
}

# Generate disease labels based on threshold values
data["Diabetes"] = (data["BloodSugar"] > 120).astype(int)
data["HeartDisease"] = (data["Cholesterol"] > 220).astype(int)
data["LiverDisease"] = (data["LiverEnzyme"] > 50).astype(int)
data["KidneyDisease"] = (data["KidneyFunction"] > 1.5).astype(int)
data["ThyroidDisease"] = ((data["ThyroidLevel"] < 2.5) | (data["ThyroidLevel"] > 4.5)).astype(int)

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
df.to_csv("dataset.csv", index=False)

print("Dataset generated and saved as dataset.csv!")
