import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

input_file_names = ['games_with_evals.txt'] # can add more to list later if helpful
#input_file_names = ['games_with_evals_from_first_100_games.txt']
input_file_directory = '/Users/andrewford/Documents/DataSets/Lichess-Data/FilteredGames/'
REMOVE_ZERO_EVALS = True # set to True to remove zero evals from non-forced mate data since they may indicate forced stalemates
if REMOVE_ZERO_EVALS:
    model_file_path = 'logistic_regression_model_remove_zeroes.pkl'
else:
    model_file_path = 'logistic_regression_model.pkl'
#FORCE_MODEL_RETRAIN = False # set to True to retrain model, False to load existing model from disk
SPLIT_BY_ELO = True # set to True to split data into separate models for different average elo ranges, False to train single model on all data

# Current columns:
    # white Elo,
    # white move,
    # eval after white move,
    # white time left after move,
    # black Elo,
    # black move,
    # eval after black move,
    # black time left after move

column_names = ['white_elo', 'white_move', 'white_eval', 'white_time_left', 'black_elo', 'black_move', 'black_eval', 'black_time_left', 'result_code'] # column names for DataFrame
moves_and_evals = pd.DataFrame() # list to store moves and evals for regression analysis

for file_name in input_file_names:
    input_file_path = input_file_directory + file_name
    with open(input_file_path, 'r') as f:
        moves = pd.read_csv(f, sep='\t') # read tab-separated values into DataFrame
        moves_and_evals = pd.concat([moves_and_evals, moves], ignore_index=True) # add DataFrame to list for regression analysis

print(moves_and_evals.shape) # print shape of DataFrame to check number of rows and columns
print(moves_and_evals.head()) # print first few rows to check data

X_white = moves_and_evals['white_eval'] # independent variable (eval after white move)
X_black = moves_and_evals['black_eval'] # independent variable (eval after black move)
X = pd.concat([X_white, X_black], ignore_index=True).to_frame(name='eval') # combine independent variables into single DataFrame

# add average elo as a feature
white_elo_full = pd.concat([moves_and_evals['white_elo'], moves_and_evals['white_elo']], ignore_index=True)
black_elo_full = pd.concat([moves_and_evals['black_elo'], moves_and_evals['black_elo']], ignore_index=True)
X['avg_elo'] = (white_elo_full + black_elo_full) / 2

# Keep result_code as 3-class: 0=loss, 1=draw, 2=white win
Y_temp = 2 * moves_and_evals['result_code'] # 0, 1, or 2
Y = pd.concat([Y_temp, Y_temp], ignore_index=True) # duplicate dependent variable for both white and black moves
print(X.shape) # print shape of independent variable DataFrame
print(Y.shape) # print shape of dependent variable Series

print(X.head(10))
print(Y.head(10))

# split X into forced-mate evals (starting with '#') and other evals
if (REMOVE_ZERO_EVALS):
    forced_mate_mask = X['eval'].astype(str).str.startswith('#') | (X['eval'].astype(str) == '0.0')
else:
    forced_mate_mask = X['eval'].astype(str).str.startswith('#')
X_forced_mate = X[forced_mate_mask].reset_index(drop=True)
X_non_forced_mate = X[~forced_mate_mask].reset_index(drop=True)
Y_forced_mate = Y[forced_mate_mask].reset_index(drop=True)
Y_non_forced_mate = Y[~forced_mate_mask].reset_index(drop=True)

print('Forced mate X shape:', X_forced_mate.shape)
print('Non-forced mate X shape:', X_non_forced_mate.shape)

print('Forced mate Y shape:', Y_forced_mate.shape)
print('Non-forced mate Y shape:', Y_non_forced_mate.shape)

#if REMOVE_ZERO_EVALS:
    # remove zero evals from non-forced mate data since they may indicate forced stalemates
    #zero_mask = X_non_forced_mate['eval'] == 0.0
    #X_non_forced_mate = X_non_forced_mate[~zero_mask].reset_index(drop=True)
    #Y_non_forced_mate = Y_non_forced_mate[~zero_mask].reset_index(drop=True)
    #print('Non-forced mate X shape after removing zero evals:', X_non_forced_mate.shape)
    #print('Non-forced mate Y shape after removing zero evals:', Y_non_forced_mate.shape)


# convert non-forced mate evals to numeric values before regression
X_non_forced_mate['eval'] = pd.to_numeric(X_non_forced_mate['eval'], errors='coerce')
X_non_forced_mate['avg_elo'] = pd.to_numeric(X_non_forced_mate['avg_elo'], errors='coerce')
valid_non_mate_mask = X_non_forced_mate['eval'].notna() & X_non_forced_mate['avg_elo'].notna()
X_non_forced_mate = X_non_forced_mate[valid_non_mate_mask].reset_index(drop=True)
Y_non_forced_mate = Y_non_forced_mate[valid_non_mate_mask].reset_index(drop=True)

X_train, X_test = train_test_split(X_non_forced_mate, test_size=0.2, random_state=42)
Y_train, Y_test = train_test_split(Y_non_forced_mate, test_size=0.2, random_state=42)

if SPLIT_BY_ELO:
    # Define elo ranges
    elo_bins = [(0, 800), (800, 1000), (1000, 1200), (1200, 1400), (1400, 1600), (1600, 1800), (1800, 2000), (2000, 2200), (2200, 3000)]
    models = {}
    
    for elo_min, elo_max in elo_bins:
        # Filter data for this elo range
        elo_mask = (X_train['avg_elo'] >= elo_min) & (X_train['avg_elo'] < elo_max)
        X_train_elo = X_train[elo_mask]
        Y_train_elo = Y_train[elo_mask]
        
        if len(X_train_elo) < 100:
            print(f'Skipping elo range {elo_min}-{elo_max}: insufficient data ({len(X_train_elo)} samples)')
            continue
        
        # Train multinomial model for this elo range (using only eval as feature)
        model_elo = LogisticRegression(solver='lbfgs', max_iter=1000) # commented out multi_class="multinomial"
        model_elo.fit(X_train_elo[['eval']].values, Y_train_elo.values)
        
        # Evaluate on test data in same elo range
        elo_test_mask = (X_test['avg_elo'] >= elo_min) & (X_test['avg_elo'] < elo_max)
        X_test_elo = X_test[elo_test_mask]
        Y_test_elo = Y_test[elo_test_mask]
        
        test_acc = model_elo.score(X_test_elo[['eval']].values, Y_test_elo.values) if len(X_test_elo) > 0 else None
        
        print(f'Elo range {elo_min}-{elo_max}: coefs={model_elo.coef_.flatten()}, intercepts={model_elo.intercept_}, train_acc={model_elo.score(X_train_elo[["eval"]].values, Y_train_elo.values):.4f}, test_acc={test_acc}, samples={len(X_train_elo)}')
        models[(elo_min, elo_max)] = model_elo
    
    # Save models dictionary
    #model_file_path = f'logistic_regression_models_by_elo_min_{elo_min}_max_{elo_max}.pkl'
    with open(model_file_path, 'wb') as model_file:
        pickle.dump(models, model_file)
    print(f'Split regression models saved to {model_file_path}')
    
    # Plot all elo range models (win/draw/loss probabilities)
    plt.figure(figsize=(10, 6))
    x_plot = np.linspace(-20, 20, 300)
    colors = plt.cm.viridis(np.linspace(0, 1, len(models)))
    
    for (elo_min, elo_max), model_elo in models.items():
        proba = model_elo.predict_proba(x_plot.reshape(-1, 1))
        # Classes are 0=loss, 1=draw, 2=white win
        loss_prob = proba[:, 0]
        draw_prob = proba[:, 1]
        win_prob = proba[:, 2]
        plt.plot(x_plot, win_prob, label=f'elo={elo_min}-{elo_max} (win)', color=colors[list(models.keys()).index((elo_min, elo_max))], linestyle='-')
        plt.plot(x_plot, draw_prob, label=f'elo={elo_min}-{elo_max} (draw)', color=colors[list(models.keys()).index((elo_min, elo_max))], linestyle='--')
        plt.plot(x_plot, loss_prob, label=f'elo={elo_min}-{elo_max} (loss)', color=colors[list(models.keys()).index((elo_min, elo_max))], linestyle=':')
    
    plt.xlabel('Eval')
    plt.ylabel('Probability')
    plt.title('Logistic Regression Curves by Elo Range (Win/Draw/Loss)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    plt.grid(True)
    plt.show()
    # Do I also want to plot the expected value of the result (win probability + 1/2 draw probability) as a function of eval for each elo range?
else:
    # Original single model code - multinomial for 3-class output
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000)
    model.fit(X_train.values, Y_train.values)
    print('Logistic regression coefficients (eval):', model.coef_[:, 0])
    print('Logistic regression coefficients (avg_elo):', model.coef_[:, 1])
    print('Logistic regression intercepts:', model.intercept_)
    print('Training accuracy:', model.score(X_train.values, Y_train.values))
    print('Test accuracy:', model.score(X_test.values, Y_test.values))

    # save trained regression model to disk
    with open(model_file_path, 'wb') as model_file:
        pickle.dump(model, model_file)
    print(f'Regression model saved to {model_file_path}')

    # plot non-forced mate evals used for regression
    if X_test.shape[0] > 1000: # if too many points, sample 1000 for plotting
        sample_indices = np.random.choice(X_test.index, size=1000, replace=False)
        X_test_sample = X_test.loc[sample_indices]
        Y_test_sample = Y_test.loc[sample_indices]
    else:
        X_test_sample = X_test
        Y_test_sample = Y_test
    plt.scatter(X_test_sample['eval'].values, Y_test_sample.values, alpha=0.6, label='Data')

    max_magnitude_evals = X_test_sample['eval'].abs().max()
    max_magnitude_plot = min(max_magnitude_evals, 10) # ensure at most (-10, 10) range for plotting
    x_plot = np.linspace(-max_magnitude_plot, max_magnitude_plot, 300) # hard-coded (-10, 10) range for evals
    
    # For single model with avg_elo feature, use median elo for plotting
    median_elo = X_train['avg_elo'].median()
    features_plot = np.column_stack((x_plot, np.full(len(x_plot), median_elo)))
    proba = model.predict_proba(features_plot)
    # Classes are 0=loss, 1=draw, 2=white win
    loss_prob = proba[:, 0]
    draw_prob = proba[:, 1]
    win_prob = proba[:, 2]

    plt.plot(x_plot, win_prob, color='green', label='Win probability')
    plt.plot(x_plot, draw_prob, color='blue', label='Draw probability')
    plt.plot(x_plot, loss_prob, color='red', label='Loss probability')
    plt.xlabel('Eval')
    plt.ylabel('Probability')
    plt.title(f'Logistic Regression Data (Non-forced mate evals, median elo={median_elo:.0f})')
    plt.xlim(-max_magnitude_plot, max_magnitude_plot) # set x-axis limits to match plot range
    plt.ylim(0, 1) # set y-axis limits to probability range
    plt.legend()
    plt.show()
    
    # # Plot win probability only (old version)
    # plt.plot(x_plot, win_prob * 2 - 1, color='red', label='Logistic regression curve')
    # plt.xlabel('Eval')
    # plt.ylabel('Result (-1/1)')
    # plt.title('Logistic Regression Data (Non-forced mate evals)')
    # plt.xlim(-max_magnitude_plot, max_magnitude_plot) # set x-axis limits to match plot range
    # plt.ylim(-1, 1) # set y-axis limits to match plot range
    # plt.legend()
    # plt.show()

# tentative forced mate evals strategy:
# use X_forced_mate separately for forced mate eval analysis
# run regression on X_non_forced_mate/Y_non_forced_mate
# evaluate whether forced mate evals should be mapped to a numeric score before combining