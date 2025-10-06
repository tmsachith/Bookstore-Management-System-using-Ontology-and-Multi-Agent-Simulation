import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import sys
import os

# Add parent directory to path to import bookstore_system
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bookstore_system import BookstoreModel, Book, Customer, Employee, Order, message_bus
import queue

class BookstoreGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TM Sachith's Bookstore Management System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.model = None
        self.simulation_running = False
        self.simulation_thread = None
        self.step_count = 0
        self.message_queue = queue.Queue()
        
        # Create main interface
        self.create_widgets()
        self.setup_plots()
        
        # Start message monitoring
        self.root.after(100, self.check_messages)
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        title_frame.pack(fill='x', pady=(0, 10))
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Bookstore Management System", 
                              font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50')
        title_label.pack(expand=True)
        
        # Control panel
        self.create_control_panel()
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.create_simulation_tab()
        self.create_inventory_tab()
        self.create_customers_tab()
        self.create_analytics_tab()
        self.create_ontology_tab()
        self.create_messages_tab()
    
    def create_control_panel(self):
        """Create the control panel with simulation controls"""
        control_frame = tk.Frame(self.root, bg='#34495e', height=80)
        control_frame.pack(fill='x', padx=10, pady=5)
        control_frame.pack_propagate(False)
        
        # Simulation parameters
        params_frame = tk.Frame(control_frame, bg='#34495e')
        params_frame.pack(side='left', padx=10, pady=10)
        
        tk.Label(params_frame, text="Customers:", fg='white', bg='#34495e').grid(row=0, column=0, sticky='w')
        self.customers_var = tk.StringVar(value="8")
        tk.Entry(params_frame, textvariable=self.customers_var, width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(params_frame, text="Employees:", fg='white', bg='#34495e').grid(row=0, column=2, sticky='w', padx=(10,0))
        self.employees_var = tk.StringVar(value="2")
        tk.Entry(params_frame, textvariable=self.employees_var, width=5).grid(row=0, column=3, padx=5)
        
        tk.Label(params_frame, text="Books:", fg='white', bg='#34495e').grid(row=0, column=4, sticky='w', padx=(10,0))
        self.books_var = tk.StringVar(value="12")
        tk.Entry(params_frame, textvariable=self.books_var, width=5).grid(row=0, column=5, padx=5)
        
        # Control buttons
        buttons_frame = tk.Frame(control_frame, bg='#34495e')
        buttons_frame.pack(side='right', padx=10, pady=10)
        
        self.start_btn = tk.Button(buttons_frame, text="Start Simulation", 
                                  command=self.start_simulation, bg='#27ae60', fg='white',
                                  font=('Arial', 10, 'bold'), padx=20)
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(buttons_frame, text="Stop Simulation", 
                                 command=self.stop_simulation, bg='#e74c3c', fg='white',
                                 font=('Arial', 10, 'bold'), padx=20, state='disabled')
        self.stop_btn.pack(side='left', padx=5)
        
        self.step_btn = tk.Button(buttons_frame, text="Single Step", 
                                 command=self.single_step, bg='#3498db', fg='white',
                                 font=('Arial', 10, 'bold'), padx=20)
        self.step_btn.pack(side='left', padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready to start simulation")
        status_label = tk.Label(control_frame, textvariable=self.status_var, 
                               fg='#ecf0f1', bg='#34495e', font=('Arial', 9))
        status_label.pack(side='bottom', pady=5)
    
    def create_simulation_tab(self):
        """Create the main simulation overview tab"""
        sim_frame = ttk.Frame(self.notebook)
        self.notebook.add(sim_frame, text="Simulation Overview")
        
        # Statistics panel
        stats_frame = tk.LabelFrame(sim_frame, text="Current Statistics", font=('Arial', 12, 'bold'))
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        # Create statistics display
        self.stats_vars = {
            'step': tk.StringVar(value="Step: 0"),
            'total_books': tk.StringVar(value="Total Books: 0"),
            'total_stock': tk.StringVar(value="Total Stock: 0"),
            'total_sales': tk.StringVar(value="Total Sales: 0"),
            'avg_budget': tk.StringVar(value="Avg Customer Budget: $0.00"),
            'satisfaction': tk.StringVar(value="Customer Satisfaction: 0.00")
        }
        
        row = 0
        for key, var in self.stats_vars.items():
            label = tk.Label(stats_frame, textvariable=var, font=('Arial', 11))
            label.grid(row=row//3, column=row%3, sticky='w', padx=20, pady=5)
            row += 1
        
        # Activity log
        log_frame = tk.LabelFrame(sim_frame, text="Activity Log", font=('Arial', 12, 'bold'))
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.activity_log = scrolledtext.ScrolledText(log_frame, height=15, font=('Consolas', 9))
        self.activity_log.pack(fill='both', expand=True, padx=5, pady=5)
    
    def create_inventory_tab(self):
        """Create the inventory management tab"""
        inv_frame = ttk.Frame(self.notebook)
        self.notebook.add(inv_frame, text="Inventory")
        
        # Book list
        list_frame = tk.LabelFrame(inv_frame, text="Book Inventory", font=('Arial', 12, 'bold'))
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for books
        columns = ('ID', 'Title', 'Author', 'Genre', 'Price', 'Stock', 'Sales')
        self.books_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.books_tree.heading(col, text=col)
            self.books_tree.column(col, width=100)
        
        # Scrollbar for treeview
        books_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=books_scrollbar.set)
        
        self.books_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        books_scrollbar.pack(side='right', fill='y', pady=5)
    
    def create_customers_tab(self):
        """Create the customers tab"""
        cust_frame = ttk.Frame(self.notebook)
        self.notebook.add(cust_frame, text="Customers")
        
        # Customer list
        list_frame = tk.LabelFrame(cust_frame, text="Customer Information", font=('Arial', 12, 'bold'))
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Treeview for customers
        columns = ('ID', 'Budget', 'Purchased Books', 'Satisfaction', 'Preferred Genres')
        self.customers_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=120)
        
        # Scrollbar for treeview
        cust_scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=cust_scrollbar.set)
        
        self.customers_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        cust_scrollbar.pack(side='right', fill='y', pady=5)
    
    def create_analytics_tab(self):
        """Create the analytics tab with charts"""
        analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(analytics_frame, text="Analytics")
        
        self.analytics_frame = analytics_frame
    
    def create_ontology_tab(self):
        """Create the ontology inspection tab"""
        onto_frame = ttk.Frame(self.notebook)
        self.notebook.add(onto_frame, text="Ontology")
        
        # Ontology information display
        info_frame = tk.LabelFrame(onto_frame, text="Ontology Information", font=('Arial', 12, 'bold'))
        info_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.ontology_text = scrolledtext.ScrolledText(info_frame, height=20, font=('Consolas', 9))
        self.ontology_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Refresh button
        refresh_btn = tk.Button(onto_frame, text="Refresh Ontology", 
                               command=self.refresh_ontology, bg='#3498db', fg='white')
        refresh_btn.pack(pady=5)
    
    def create_messages_tab(self):
        """Create the message bus monitoring tab"""
        msg_frame = ttk.Frame(self.notebook)
        self.notebook.add(msg_frame, text="Messages")
        
        # Message display
        msg_display_frame = tk.LabelFrame(msg_frame, text="Message Bus Activity", font=('Arial', 12, 'bold'))
        msg_display_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.messages_text = scrolledtext.ScrolledText(msg_display_frame, height=20, font=('Consolas', 9))
        self.messages_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Clear messages button
        clear_btn = tk.Button(msg_frame, text="Clear Messages", 
                             command=self.clear_messages, bg='#e67e22', fg='white')
        clear_btn.pack(pady=5)
    
    def setup_plots(self):
        """Setup matplotlib plots for analytics"""
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.suptitle('Bookstore Analytics Dashboard', fontsize=16)
        
        # Initialize empty data
        self.plot_data = {
            'steps': [],
            'total_stock': [],
            'total_sales': [],
            'avg_budget': [],
            'satisfaction': []
        }
        
        # Canvas for matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, self.analytics_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)
        
        # Initialize log message after all widgets are created
        self.root.after(100, lambda: self.log_message("System initialized. Ready to start simulation."))
    
    def start_simulation(self):
        """Start the simulation in a separate thread"""
        try:
            num_customers = int(self.customers_var.get())
            num_employees = int(self.employees_var.get())
            num_books = int(self.books_var.get())
            
            self.model = BookstoreModel(num_customers, num_employees, num_books)
            self.simulation_running = True
            self.step_count = 0
            
            # Update UI
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_var.set("Simulation running...")
            
            # Clear previous data
            self.activity_log.delete(1.0, tk.END)
            self.plot_data = {key: [] for key in self.plot_data.keys()}
            
            # Start simulation thread
            self.simulation_thread = threading.Thread(target=self.run_simulation_loop)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
            self.log_message(f"Simulation started with {num_customers} customers, {num_employees} employees, {num_books} books")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for simulation parameters")
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Simulation stopped")
        self.log_message("Simulation stopped by user")
    
    def single_step(self):
        """Execute a single simulation step"""
        if self.model is None:
            try:
                num_customers = int(self.customers_var.get())
                num_employees = int(self.employees_var.get())
                num_books = int(self.books_var.get())
                self.model = BookstoreModel(num_customers, num_employees, num_books)
                self.step_count = 0
                self.log_message("Model created for single step execution")
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers for simulation parameters")
                return
        
        self.execute_step()
    
    def run_simulation_loop(self):
        """Main simulation loop running in separate thread"""
        while self.simulation_running:
            self.execute_step()
            time.sleep(1)  # 1 second delay between steps
    
    def execute_step(self):
        """Execute a single step and update GUI"""
        if self.model:
            self.step_count += 1
            self.model.step()
            
            # Queue GUI updates
            self.message_queue.put(('update_stats', None))
            self.message_queue.put(('update_inventory', None))
            self.message_queue.put(('update_customers', None))
            self.message_queue.put(('update_plots', None))
    
    def check_messages(self):
        """Check for messages from simulation thread and update GUI"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == 'update_stats':
                    self.update_statistics()
                elif msg_type == 'update_inventory':
                    self.update_inventory()
                elif msg_type == 'update_customers':
                    self.update_customers()
                elif msg_type == 'update_plots':
                    self.update_plots()
                elif msg_type == 'log_message':
                    self.log_message(data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_messages)
    
    def update_statistics(self):
        """Update the statistics display"""
        if not self.model:
            return
        
        # Get latest data
        data = self.model.datacollector.get_model_vars_dataframe()
        if not data.empty:
            latest = data.iloc[-1]
            
            self.stats_vars['step'].set(f"Step: {self.step_count}")
            self.stats_vars['total_books'].set(f"Total Books: {int(latest['Total Books'])}")
            self.stats_vars['total_stock'].set(f"Total Stock: {int(latest['Total Stock'])}")
            self.stats_vars['total_sales'].set(f"Total Sales: {int(latest['Total Sales'])}")
            self.stats_vars['avg_budget'].set(f"Avg Customer Budget: ${latest['Average Customer Budget']:.2f}")
            self.stats_vars['satisfaction'].set(f"Customer Satisfaction: {latest['Customer Satisfaction']:.2f}")
    
    def update_inventory(self):
        """Update the inventory display"""
        if not self.model:
            return
        
        # Clear existing items
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        
        # Add current book data
        book_agents = [a for a in self.model.schedule.agents if hasattr(a, 'title')]
        for book in book_agents:
            self.books_tree.insert('', 'end', values=(
                book.unique_id,
                book.title,
                book.author,
                book.genre,
                f"${book.price:.2f}",
                book.stock,
                book.total_sales
            ))
    
    def update_customers(self):
        """Update the customers display"""
        if not self.model:
            return
        
        # Clear existing items
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        # Add current customer data
        customer_agents = [a for a in self.model.schedule.agents if hasattr(a, 'budget')]
        for customer in customer_agents:
            genres = ', '.join(customer.preferred_genres)
            self.customers_tree.insert('', 'end', values=(
                customer.unique_id,
                f"${customer.budget:.2f}",
                len(customer.purchased_books),
                f"{customer.satisfaction:.2f}",
                genres
            ))
    
    def update_plots(self):
        """Update the analytics plots"""
        if not self.model:
            return
        
        # Get latest data
        data = self.model.datacollector.get_model_vars_dataframe()
        if data.empty:
            return
        
        latest = data.iloc[-1]
        
        # Update plot data
        self.plot_data['steps'].append(self.step_count)
        self.plot_data['total_stock'].append(latest['Total Stock'])
        self.plot_data['total_sales'].append(latest['Total Sales'])
        self.plot_data['avg_budget'].append(latest['Average Customer Budget'])
        self.plot_data['satisfaction'].append(latest['Customer Satisfaction'])
        
        # Keep only last 20 data points
        for key in self.plot_data:
            if len(self.plot_data[key]) > 20:
                self.plot_data[key] = self.plot_data[key][-20:]
        
        # Clear and update plots
        self.ax1.clear()
        self.ax1.plot(self.plot_data['steps'], self.plot_data['total_stock'], 'b-', linewidth=2)
        self.ax1.set_title('Total Stock Over Time')
        self.ax1.set_ylabel('Stock')
        
        self.ax2.clear()
        self.ax2.plot(self.plot_data['steps'], self.plot_data['total_sales'], 'g-', linewidth=2)
        self.ax2.set_title('Total Sales Over Time')
        self.ax2.set_ylabel('Sales')
        
        self.ax3.clear()
        self.ax3.plot(self.plot_data['steps'], self.plot_data['avg_budget'], 'r-', linewidth=2)
        self.ax3.set_title('Average Customer Budget')
        self.ax3.set_ylabel('Budget ($)')
        self.ax3.set_xlabel('Step')
        
        self.ax4.clear()
        self.ax4.plot(self.plot_data['steps'], self.plot_data['satisfaction'], 'm-', linewidth=2)
        self.ax4.set_title('Customer Satisfaction')
        self.ax4.set_ylabel('Satisfaction')
        self.ax4.set_xlabel('Step')
        
        self.canvas.draw()
    
    def refresh_ontology(self):
        """Refresh the ontology display"""
        self.ontology_text.delete(1.0, tk.END)
        
        ontology_info = []
        ontology_info.append("ONTOLOGY INSPECTION")
        ontology_info.append("=" * 50)
        ontology_info.append("")
        
        # Books
        ontology_info.append("Books in ontology:")
        for book in Book.instances():
            name = book.hasName[0] if book.hasName else 'Unnamed'
            price = f"${book.hasPrice[0]:.2f}" if book.hasPrice else 'No price'
            stock = f"{book.availableQuantity[0]}" if book.availableQuantity else 'Unknown stock'
            ontology_info.append(f"  - {name} | {price} | Stock: {stock}")
        
        ontology_info.append("")
        ontology_info.append(f"Total Customers: {len(list(Customer.instances()))}")
        ontology_info.append(f"Total Employees: {len(list(Employee.instances()))}")
        ontology_info.append(f"Total Orders: {len(list(Order.instances()))}")
        
        # Display in text widget
        self.ontology_text.insert(tk.END, "\n".join(ontology_info))
    
    def clear_messages(self):
        """Clear the messages display"""
        self.messages_text.delete(1.0, tk.END)
    
    def log_message(self, message):
        """Add a message to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.activity_log.insert(tk.END, formatted_message)
        self.activity_log.see(tk.END)
        
        # Also add to messages tab if it exists
        if hasattr(self, 'messages_text'):
            self.messages_text.insert(tk.END, formatted_message)
            self.messages_text.see(tk.END)

def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = BookstoreGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user")

if __name__ == "__main__":
    main()
