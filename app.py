from flask import Flask, render_template, request
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import io
import base64

app = Flask(__name__)

def count_resources(json_data):
    counts = {}
    if isinstance(json_data, list):
        for item in json_data:
            if 'type' in item:
                counts[item['type']] = item['count']
    elif isinstance(json_data, dict) and 'resources' in json_data:
        for resource in json_data['resources']:
            r_type = resource['type']
            if r_type in counts:
                counts[r_type] += 1
            else:
                counts[r_type] = 1
    return counts

# Define mapping of resource type names to be modified
def modify_label(label):
    mapping = {
        "azurerm_resource_group": "resource_group",
        "azurerm_virtual_network": "virtual_network",
        "azurerm_network_interface": "network_interface",
        "azurerm_network_security_group": "security_group",
        "azurerm_windows_virtual_machine": "virtual_machine",
        "azurerm_subnet": "subnet"
    }
    # Replace the label if it exists in the mapping
    return mapping.get(label, label)

def generate_graph(counts, x_labels=None):
    plt.figure(figsize=(5, 4))
    if x_labels:
        x_labels = [modify_label(label) for label in x_labels]  # Modify x-labels
        plt.bar(x_labels, counts.values())
    else:
        plt.bar(counts.keys(), counts.values())
    plt.xlabel('Resource Type')
    plt.ylabel('Count')
    plt.xticks(rotation=25, fontsize=8)
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    plot_data = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    return plot_data

def get_resource_text(counts):
    resource_text = ""
    for resource, count in counts.items():
        resource_text += f"{resource}: {count}\n"
    return resource_text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get uploaded files
        file1 = request.files['file1']
        file2 = request.files['file2']
        # Read and load JSON files
        data1 = json.load(file1)
        data2 = json.load(file2)
        # Count resources in each file
        count1 = count_resources(data1)
        count2 = count_resources(data2)
        # Extract x-labels from JSON data for both graphs
        x_labels1 = set(item['type'] for item in data1.get('resources', []))
        x_labels2 = set(item['type'] for item in data2)  # Iterate over each item in data2
        # Ensure all unique labels from both graphs are included
        all_labels = sorted(list(x_labels1.union(x_labels2)), key=lambda x: x.lower())
        # Fill in missing counts for labels that are present in one dataset but not the other
        count1 = {label: count1.get(label, 0) for label in all_labels}
        count2 = {label: count2.get(label, 0) for label in all_labels}
        # Generate graph 1 with custom x-labels
        graph1 = generate_graph(count1, all_labels)
        # Generate graph 2 with custom x-labels
        graph2 = generate_graph(count2, all_labels)
        # Filter resource counts to include only resources from file 1
        resource_counts1 = {label: count1[label] for label in x_labels1}
        return render_template('result.html', graph1=graph1, graph2=graph2, resource_counts1=resource_counts1)
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
