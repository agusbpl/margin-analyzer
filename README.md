# MarginAnalyzer 📊

MarginAnalyzer is a professional **Break-even Analysis & Profit Simulator** built with Python and Streamlit. It helps businesses and entrepreneurs visualize their financial health by calculating key indicators like the break-even point, shutdown point, and profit targets.

## 🚀 Features

- **Dynamic Break-even Analysis**: Calculate units and revenue needed to cover all costs.
- **Profit Simulation**: Predict required sales to reach specific profit goals (nominal or percentage-based).
- **Interactive Visualizations**: High-quality Plotly charts showing cost structures, revenue streams, and margin areas.
- **CSV Data Import**: Upload your own cost structures for instant analysis.
- **Operational Verification**: Integrated income statement simulation to verify results.

## 🛠️ Tech Stack

- **Python 3**
- **Streamlit** (UI/UX)
- **Plotly** (Interactive Graphs)
- **Pandas/Numpy** (Data Processing)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:agusbpl/margin-analyzer.git
   cd margin-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## 📊 Data Format

The application expects a CSV file with the following columns:
- `Tipo`: (Ingreso, Variable, Fijo)
- `Concepto`: Name of the item
- `Valor`: Value ($)
- `Consumo_Unitario`: For variable costs
- `Base_Referencia`: Reference for calculation
- `Es_Erogable`: (Si/No) for shutdown point calculation

Check `sample_data.csv` for an example.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
