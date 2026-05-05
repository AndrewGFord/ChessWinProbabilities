import streamlit as st
import pickle
import numpy as np
import sklearn

st.title('Chess Win Probability Calculator')
st.write('Enter an evaluation and average Elo to predict the probability of winning.')
NO_ZERO_EVALS = True

if NO_ZERO_EVALS:
    st.warning('This model was trained with zero evals removed from non-forced mate data, which may improve accuracy by excluding potential stalemate positions.')
    filename = 'logistic_regression_model_remove_zeroes.pkl'
else:
    filename = 'logistic_regression_model.pkl'  # default model file name


# Load the model
try:
    with open(filename, 'rb') as f:
        data = pickle.load(f)
except FileNotFoundError:
    st.error('Model file not found. Please run BuildRegression.py first.')
    st.stop()

# Determine model type and configure inputs
if isinstance(data, dict):
    # Elo-split models
    model_type = 'split'
    st.write('Using elo-split regression models.')
else:
    # Single combined model
    model_type = 'single'
    st.write('Using combined regression model with avg_elo feature.')

# User inputs
color = st.radio('You play as', ['White', 'Black'])
eval_value = st.number_input('Evaluation (centipawns)', min_value=-10.0, max_value=10.0, value=0.0, step=0.1)

if model_type == 'split':
    # For split models, select elo range
    elo_ranges = list(data.keys())
    elo_options = [f'{elo_min}-{elo_max}' for elo_min, elo_max in elo_ranges]
    selected_elo_range = st.selectbox('Average Elo Range', elo_options)
    
    # Find the matching model
    elo_min, elo_max = map(int, selected_elo_range.split('-'))
    model = data[(elo_min, elo_max)]
    
    # Calculate probability (classes: 0=loss, 1=draw, 2=white win)
    proba = model.predict_proba([[eval_value]])
    loss_prob = proba[0][0]
    draw_prob = proba[0][1]
    win_prob = proba[0][2]
    
    st.write(f'**Selected Elo Range:** {selected_elo_range}')
    #st.write(f'**Model Coefficients:** {model.coef_.flatten()}')
    #st.write(f'**Model Intercepts:** {model.intercept_}')
else:
    # For single model, use exact elo input
    elo_value = st.number_input('Average Elo', min_value=800, max_value=2200, value=1500, step=50)
    
    model = data
    
    # Calculate probability (classes: 0=loss, 1=draw, 2=white win)
    features = np.array([[eval_value, elo_value]])
    proba = model.predict_proba(features)
    loss_prob = proba[0][0]
    draw_prob = proba[0][1]
    win_prob = proba[0][2]
    
    st.write(f'**Eval Coefficients:** {model.coef_[:, 0]}')
    st.write(f'**Avg Elo Coefficients:** {model.coef_[:, 1]}')
    st.write(f'**Intercepts:** {model.intercept_}')

# Reverse probabilities if playing as Black
if color == 'Black':
    win_prob, loss_prob = loss_prob, win_prob

# Display results
st.divider()
st.metric('Win Probability', f'{win_prob:.1%}')
st.metric('Draw Probability', f'{draw_prob:.1%}')
st.metric('Loss Probability', f'{loss_prob:.1%}')

# Convert to -1 to 1 scale (win=1, draw=0, loss=-1)
predicted_result = win_prob - loss_prob
st.metric('Predicted Result (-1 to 1)', f'{predicted_result:.3f}')