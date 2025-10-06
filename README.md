# Bookstore Management System with GUI

A comprehensive bookstore management system that combines ontology-based knowledge representation, multi-agent simulation, and a graphical user interface.

## Features

### Core System
- **Ontology-based Knowledge Representation** using Owlready2
- **Multi-Agent Simulation** with Mesa framework
- **Message Bus Communication** between agents
- **Automatic Inventory Management**
- **Customer Behavior Simulation**
- **Employee Restocking Behavior**

### GUI Features
- **Real-time Simulation Control** - Start, stop, or step through simulation
- **Live Statistics Dashboard** - Monitor key metrics in real-time
- **Inventory Management View** - Track all books, prices, and stock levels
- **Customer Analytics** - Monitor customer behavior and satisfaction
- **Interactive Charts** - Visual analytics with matplotlib integration
- **Ontology Inspector** - View and inspect the knowledge base
- **Message Bus Monitor** - Real-time message logging

## Installation

1. **Prerequisites**: Python 3.9+ and pip

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Alternative Installation** (if requirements.txt fails):
   ```bash
   pip install owlready2 mesa numpy matplotlib
   ```

## Usage

### Running the GUI Application
```bash
python run_gui.py
```

### Running the Console Version
```bash
python bookstore_system.py
```

## GUI Interface Guide

### 1. Control Panel
- **Simulation Parameters**: Set number of customers, employees, and books
- **Start Simulation**: Begin continuous simulation
- **Stop Simulation**: Halt the running simulation  
- **Single Step**: Execute one simulation step manually

### 2. Simulation Overview Tab
- **Current Statistics**: Real-time metrics display
- **Activity Log**: Timestamped events and actions

### 3. Inventory Tab
- **Book List**: Complete inventory with details
- **Columns**: ID, Title, Author, Genre, Price, Stock, Sales

### 4. Customers Tab
- **Customer Information**: Budget, purchases, satisfaction, preferences
- **Real-time Updates**: Live customer data

### 5. Analytics Tab
- **Interactive Charts**: 
  - Total Stock Over Time
  - Total Sales Over Time
  - Average Customer Budget
  - Customer Satisfaction Trends

### 6. Ontology Tab
- **Knowledge Base Inspector**: View ontology instances
- **Refresh Button**: Update ontology display

### 7. Messages Tab
- **Message Bus Activity**: Real-time agent communication
- **Clear Messages**: Reset message log

## System Architecture

### Agents
- **Customer Agents**: Browse and purchase books based on preferences and budget
- **Employee Agents**: Monitor inventory and restock low-stock items
- **Book Agents**: Track sales, manage pricing, and request restocking

### Ontology Classes
- **Book**: Represents books with properties (price, stock, author, genre)
- **Customer**: Represents customers with budget and preferences
- **Employee**: Represents store employees
- **Order**: Tracks purchase transactions
- **Author**: Book authors
- **Genre**: Book categories

### Communication
- **Message Bus**: Enables agent-to-agent communication
- **Topics**: 
  - `book_available`: New book notifications
  - `book_purchased`: Purchase events
  - `restock_needed`: Low inventory alerts
  - `book_restocked`: Restocking events
  - `price_update`: Price change notifications

## Simulation Logic

1. **Customer Behavior**:
   - Browse available books
   - Filter by preferred genres
   - Make purchase decisions based on budget
   - Update satisfaction based on purchases

2. **Employee Behavior**:
   - Monitor all book inventory levels
   - Automatically restock books below threshold
   - Respond to restock requests

3. **Book Behavior**:
   - Track sales and stock levels
   - Request restocking when low
   - Adjust prices based on demand

## File Structure
```
bookstore_system.py     # Core simulation engine
gui/
├── bookstore_gui.py    # GUI interface
├── run_gui.py         # GUI launcher from gui folder
└── __init__.py        # Package initialization
requirements.txt       # Python dependencies
README.md             # This documentation
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **GUI Not Starting**: Check Python version (3.9+ required)
3. **Slow Performance**: Reduce number of agents in simulation parameters
4. **Plot Display Issues**: Update matplotlib to latest version

### Dependencies
- **owlready2**: Ontology management
- **mesa**: Agent-based modeling
- **numpy**: Numerical operations
- **matplotlib**: Chart generation
- **tkinter**: GUI framework (included with Python)

## Customization

### Adding New Book Types
Modify the `book_data` list in `BookstoreModel.__init__()` to add new books.

### Adjusting Agent Behavior
- **Customer preferences**: Modify `preferred_genres` selection
- **Restocking thresholds**: Adjust `restock_threshold` values
- **Purchase probability**: Change random thresholds in agent logic

### GUI Customization
- **Colors**: Modify color codes in widget creation
- **Layout**: Adjust frame sizes and positions
- **Charts**: Add new plot types in analytics tab

## License
This project is for educational and demonstration purposes.

## Authors
Bookstore Management System with Ontology and Multi-Agent Simulation

---

## Run the Simulation
Go to gui folder and run python run_gui.py

For questions or issues, please check the activity log in the GUI or console output for detailed error messages.
