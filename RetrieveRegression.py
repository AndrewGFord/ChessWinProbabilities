import pickle as pkl
import numpy as np
import matplotlib.pyplot as plt

model_file_name = 'logistic_regression_model.pkl'
data = pkl.load(open(model_file_name, 'rb'))

# Check if loaded data is a dictionary of models (SPLIT_BY_ELO=True) or single model
if isinstance(data, dict):
    # Multiple models from elo-split training
    models = data
    print('Loaded elo-split models:')
    for elo_range, model in models.items():
        print(f'  Elo range {elo_range}: coef={model.coef_[0][0]:.4f}, intercept={model.intercept_[0]:.4f}')
    
    # Plot all elo range models
    plt.figure(figsize=(10, 6))
    x_plot = np.linspace(-10, 10, 300)
    colors = plt.cm.viridis(np.linspace(0, 1, len(models)))
    
    for i, ((elo_min, elo_max), model_elo) in enumerate(models.items()):
        proba = model_elo.predict_proba(x_plot.reshape(-1, 1))
        positive_class_index = np.where(model_elo.classes_ == 1)[0][0]
        prob_pos = proba[:, positive_class_index]
        plt.plot(x_plot, prob_pos * 2 - 1, label=f'elo={elo_min}-{elo_max}', color=colors[i])
    
    plt.xlabel('Eval')
    plt.ylabel('Predicted Result (-1/1)')
    plt.title('Logistic Regression Curves by Elo Range')
    plt.legend()
    plt.grid(True)
    plt.show()
else:
    # Single model (SPLIT_BY_ELO=False)
    model = data
    print(model)
    print('Logistic regression coefficient (eval):', model.coef_[0][0])
    print('Logistic regression coefficient (avg_elo):', model.coef_[0][1])
    print('Logistic regression intercept:', model.intercept_[0])

    # Plot logistic regression curves for different average elo values
    elo_values = [900, 1200, 1500, 1800, 2100]
    max_magnitude_plot = 10  # range for eval plotting
    x_plot = np.linspace(-max_magnitude_plot, max_magnitude_plot, 300)

    plt.figure(figsize=(10, 6))
    for elo in elo_values:
        features = np.column_stack((x_plot, np.full(len(x_plot), elo)))
        proba = model.predict_proba(features)
        positive_class_index = np.where(model.classes_ == 1)[0][0]
        prob_pos = proba[:, positive_class_index]
        plt.plot(x_plot, prob_pos * 2 - 1, label=f'avg_elo={elo}')

    plt.xlabel('Eval')
    plt.ylabel('Predicted Result (-1/1)')
    plt.title('Logistic Regression Curves for Different Average Elo')
    plt.legend()
    plt.grid(True)
    plt.show()