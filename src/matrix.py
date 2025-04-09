import numpy as np
import pandas as pd

def compute_markov_matrices(P):
    """
    Computes the Q, R, N, and B matrices for an absorbing Markov chain.

    Parameters:
        P (numpy.ndarray): The overall transition matrix in canonical form.

    Returns:
        dict: A dictionary containing the computed matrices (Q, R, N, B).
    """
    # Identify the number of transient states (rows before absorbing states start)
    num_transient = 0
    for i in range(len(P)):
        if not np.allclose(P[i, i:], np.eye(1, len(P) - i, 0)):  # Check for identity in absorbing rows
            num_transient += 1
        else:
            break
    
    # Extract Q matrix (top-left block of transient states)
    Q = P[:num_transient, :num_transient]

    # Define Identity matrix I of same size as Q
    I = np.eye(Q.shape[0])

    # Compute the fundamental matrix N = (I - Q)^(-1)
    N = np.linalg.inv(I - Q)

    # Extract R matrix (top-right block of transient to absorbing states)
    R = P[:num_transient, num_transient:]

    # Compute absorption probability matrix B = N * R
    B = np.dot(N, R)

    # Convert to pandas DataFrames for better readability
    matrices = {
        "Q": pd.DataFrame(Q, columns=[f"S{i+1}" for i in range(Q.shape[0])], 
                           index=[f"S{i+1}" for i in range(Q.shape[0])]),
        "R": pd.DataFrame(R, columns=[f"A{i+1}" for i in range(R.shape[1])], 
                           index=[f"S{i+1}" for i in range(R.shape[0])]),
        "N": pd.DataFrame(N, columns=[f"S{i+1}" for i in range(N.shape[0])], 
                           index=[f"S{i+1}" for i in range(N.shape[0])]),
        "B": pd.DataFrame(B, columns=[f"A{i+1}" for i in range(B.shape[1])], 
                           index=[f"S{i+1}" for i in range(B.shape[0])])
    }

    return matrices

# Example transition matrix P
P = np.array([
    [0.00, 0.80, 0.00, 0.20],
    [0.00, 0.00, 0.90, 0.10],
    [0.00, 0.00, 0.96, 0.04],
    [0.00, 0.00, 0.00, 1.00]
])

# Compute all matrices
results = compute_markov_matrices(P)

# Print results
for name, matrix in results.items():
    print(f"\n{name} Matrix:\n", matrix)