# NHS CNS Prescribing Data Dashboard

A web-based dashboard for analyzing NHS Central Nervous System (CNS) prescribing data. This application allows users to explore prescription costs, view regional analytics, and manage the underlying dataset.

## Features

*   **Interactive Dashboard**:
    *   View prescription data with sorting capabilities (Price per Unit, Total Items, Cost).
    *   Filter data by Medicine Name, Practice/Doctor, Region, Postcode, and Category.
    *   "Total Items Tracked" counter updates dynamically based on filters.
    *   Visual indicators for the Cheapest, Average, and Highest Price per Item.
*   **Analytics**:
    *   **Regional Distribution**: Bar chart showing the number of practices per region.
    *   **Price Analysis**: Compare average costs or price-per-unit across regions for specific drugs or categories.
    *   **Category Distribution**: Pie chart showing the share of drug categories (National or Regional).
*   **Database Management**:
    *   Full CRUD (Create, Read, Update, Delete) functionality for Practices, Drugs, and Prescriptions.
    *   Secure interface for modifying the SQLite database.
*   **Data Export**:
    *   Export filtered datasets to CSV format for offline analysis.
*   **Logging**:
    *   User activities (accessing pages, modifying data) are logged to `nhs_pai/logs/app.log`.

## Technologies Used

*   **Backend**: Python 3.11, Flask
*   **Data Processing**: Pandas, NumPy
*   **Database**: SQLite
*   **Frontend**: HTML5, Bootstrap 5, Plotly.js (for charts)
*   **Testing**: Pytest

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd PAI_Individual_1
    ```

2.  **Create and activate a virtual environment**:
    *   **Windows (PowerShell)**:
        ```powershell
        python -m venv pai_indv
        .\pai_indv\Scripts\Activate.ps1
        ```
    *   **macOS/Linux**:
        ```bash
        python3 -m venv pai_indv
        source pai_indv/bin/activate
        ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  Ensure your virtual environment is activated.
2.  Navigate to the source directory:
    ```bash
    cd nhs_pai/src
    ```
3.  Run the Flask application:
    ```bash
    python app.py
    ```
4.  Open your web browser and go to: `http://127.0.0.1:5000/`

## Running Tests

The project includes a comprehensive test suite covering validation, analytics, routing, and database operations.

1.  Ensure you are in the root directory (`PAI_Individual_1`).
2.  Run all tests using `pytest`:
    ```bash
    python -m pytest nhs_pai/tests/
    ```

## Project Structure

```
PAI_Individual_1/
├── nhs_pai/
│   ├── data/               # Raw and processed CSV data, SQLite database
│   ├── logs/               # Application logs
│   ├── scripts/            # Data preprocessing scripts
│   ├── src/                # Source code
│   │   ├── templates/      # HTML templates
│   │   ├── app.py          # Main Flask application
│   │   ├── analytics.py    # Analytics logic
│   │   ├── database_manager.py # Database handling class
│   │   └── utils.py        # Validation helpers
│   └── tests/              # Unit and integration tests
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Data Sources

The application uses processed NHS prescribing data acquired from `https://digital.nhs.uk/data-and-information/publications/statistical/practice-level-prescribing-data/december-2019`. The raw data is cleaned and structured using `nhs_pai/scripts/preprocess_data.py` before being loaded into the SQLite database.
