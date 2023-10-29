import csv
import math
import sys
import os

def sigmoid_normalize(value, mean, std_dev):
    x = (value - mean) / std_dev
    normalized_value = 10 / (1 + math.exp(-x))
    return normalized_value

def process_csv(input_filepath, output_filepath):
    with open(input_filepath, newline='') as infile:
        reader = csv.DictReader(infile)

        rows = []
        risk_values = []

        for row in reader:
            try:
                risk_value = float(row['Risk Factor'])
                risk_values.append(risk_value)
            except ValueError:  # Handle non-numeric values gracefully
                continue

            rows.append(row)

        # Calculate mean and standard deviation for sigmoid normalization
        mean_risk = sum(risk_values) / len(risk_values)
        std_dev_risk = (sum([(x - mean_risk)**2 for x in risk_values]) / len(risk_values))**0.5

        with open(output_filepath, 'w', newline='') as outfile:
            fieldnames = reader.fieldnames  # Preserves the original columns
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                try:
                    print(row['Risk Factor'])
                    print(mean_risk,std_dev_risk)
                    normalized_risk = sigmoid_normalize(float(row['Risk Factor']), mean_risk, std_dev_risk)
                    row['Risk Factor'] = normalized_risk  # Update the Risk Factor value
                except ValueError:  # If the value is non-numeric, it'll leave it as it is
                    pass

                writer.writerow(row)

if __name__ == "__main__":
    input_filepaths = sys.argv[1:]
    for input_filepath in input_filepaths:
        output_filepath = os.path.splitext(input_filepath)[0] + '_normalized.csv'
        process_csv(input_filepath, output_filepath)
