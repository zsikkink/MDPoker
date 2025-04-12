import pickle

# Open the pickle file in read-binary mode.
with open("q_tables.pkl", "rb") as f:
    q_tables = pickle.load(f)

# Now, q_tables is a dictionary with keys like "BTN" and "BB".
# You can inspect its contents, for example:
print("BTN Q-Table:")
for key, value in q_tables["BTN"].items():
    print(f"State: {key[0]}, Action: {key[1]}, Q-value: {value}")

print("\nBB Q-Table:")
for key, value in q_tables["BB"].items():
    print(f"State: {key[0]}, Action: {key[1]}, Q-value: {value}")