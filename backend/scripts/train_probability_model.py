import os
import random
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "app", "ml_models")
os.makedirs(MODELS_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODELS_DIR, "solve_prob_model.joblib")

def generate_synthetic_data(num_samples=10000):
    print(f"Generating {num_samples} synthetic rows for training...")
    data = []
    for _ in range(num_samples):
        # Generate realistic user profiles
        is_cold_start = random.random() < 0.1
        
        if is_cold_start:
            user_rating = 800
            user_max_rating = 800
            total_solved = random.randint(0, 9)
            contest_maturity = 0
            avg_max_index = 1.0 # Only solves A
        else:
            user_rating = random.randint(1000, 2400)
            user_max_rating = user_rating + random.randint(0, 300)
            total_solved = random.randint(50, 2000)
            contest_maturity = random.randint(5, 100)
            avg_max_index = max(1.0, min(6.0, (user_rating - 800) / 300))

        # Generate problem
        problem_rating = random.randint(800, 3000)
        # Randomly assign index based roughly on rating
        problem_index = max(1, min(6, int((problem_rating - 800) / 300) + random.randint(-1, 1)))
        
        # Calculate Features
        rating_difference = problem_rating - user_rating
        user_max_rating_diff = user_max_rating - user_rating
        index_gap = problem_index - avg_max_index
        
        # Calculate baseline Elo probability
        elo_prob = 1.0 / (1.0 + 10.0 ** (rating_difference / 400.0))
        
        # Adjust real probability based on grind/experience (simulated hidden factors)
        adjusted_prob = elo_prob
        
        if not is_cold_start:
            # High solved count gives a small grit bonus
            if total_solved > 1000:
                adjusted_prob += 0.05
            
            # Massive index gap punishes heavily (e.g. they usually solve A/B but attempt E)
            if index_gap >= 2.0:
                adjusted_prob -= 0.20
            elif index_gap <= -1.0:
                adjusted_prob += 0.10
        else:
            # Cold start on hard problems drops to 0 effectively
            if problem_rating > 1000:
                adjusted_prob -= 0.50

        # Clamp
        adjusted_prob = max(0.01, min(0.99, adjusted_prob))
        
        # Toss a coin to see if they solved it based on the adjusted probability
        is_solved = 1 if random.random() < adjusted_prob else 0
        
        data.append({
            "rating_difference": rating_difference,
            "user_max_rating_diff": user_max_rating_diff,
            "problem_index_encoded": problem_index,
            "total_solved_count": total_solved,
            "contest_maturity": contest_maturity,
            "index_gap": index_gap,
            "is_cold_start": 1 if is_cold_start else 0,
            "is_solved": is_solved
        })
        
    return pd.DataFrame(data)

from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss

def train_model():
    df = generate_synthetic_data(25000)
    
    features = [
        "rating_difference", 
        "user_max_rating_diff", 
        "problem_index_encoded", 
        "total_solved_count", 
        "contest_maturity", 
        "index_gap", 
        "is_cold_start"
    ]
    X = df[features]
    y = df["is_solved"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Neural Networks require feature scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save the scaler so the API can use it
    scaler_path = os.path.join(MODELS_DIR, "solve_prob_scaler.joblib")
    joblib.dump(scaler, scaler_path)
    print(f"Feature scaler saved to {scaler_path}")
    
    print("\nTraining Multi-Layer Perceptron (Deep Neural Network)...")
    print("Architecture: Input -> 64 -> 32 -> Output")
    print("Optimizer: Adam | Batch Size: Auto | Epochs: up to 100\n")
    
    model = MLPClassifier(
        hidden_layer_sizes=(64, 32), 
        activation='relu',
        solver='adam',
        max_iter=100, 
        random_state=42,
        verbose=True, # This enables the epoch logging!
        early_stopping=True,
        validation_fraction=0.1
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_preds = model.predict(X_train_scaled)
    test_preds = model.predict(X_test_scaled)
    test_proba = model.predict_proba(X_test_scaled)
    
    train_acc = accuracy_score(y_train, train_preds)
    test_acc = accuracy_score(y_test, test_preds)
    val_loss = log_loss(y_test, test_proba)
    
    print(f"\n--- Training Complete ---")
    print(f"Final Epochs Run: {model.n_iter_}")
    print(f"Training Accuracy: {train_acc:.4f}")
    print(f"Validation Accuracy: {test_acc:.4f}")
    print(f"Validation Log-Loss: {val_loss:.4f}")
    
    # Save Model
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
