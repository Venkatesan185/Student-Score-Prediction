import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# =========================
# 1. Load Dataset
# =========================
df = pd.read_csv("student_dataset.csv")

# If your dataset uses ';' separator, uncomment this:
# df = pd.read_csv("student_dataset.csv", sep=";")

# =========================
# 2. Define Target
# =========================
TARGET = "Final_Exam_Score"

if TARGET not in df.columns:
    raise ValueError(f"Target column '{TARGET}' not found in dataset")

# =========================
# 3. Split Features/Target
# =========================
X = df.drop(columns=[TARGET])
y = df[TARGET]

# =========================
# 4. Identify Column Types
# =========================
categorical_cols = X.select_dtypes(include=["object"]).columns.tolist()
numerical_cols = X.select_dtypes(exclude=["object"]).columns.tolist()

# =========================
# 5. Preprocessing
# =========================
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numerical_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
    ]
)

# =========================
# 6. Model Pipeline
# =========================
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=None,
    random_state=42,
    n_jobs=-1
)

pipeline = Pipeline(steps=[
    ("preprocessing", preprocessor),
    ("model", model)
])

# =========================
# 7. Train/Test Split
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================
# 8. Train Model
# =========================
pipeline.fit(X_train, y_train)

# ========================= 
# 9. Evaluate
# =========================
y_pred = pipeline.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MSE: {mse:.2f}")
print(f"R2 Score: {r2:.4f}")

# =========================
# 10. Save Model
# =========================
joblib.dump(pipeline, "student_model.pkl")

print("Model saved as student_model.pkl")   