import random
import time
from owlready2 import *
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import numpy as np
from collections import defaultdict
import json

# Set up ontology
onto = get_ontology("http://bookstore.ontology/")

# Define ontology classes and properties
with onto:
    # Define Classes
    class Book(Thing):
        pass
    
    class Customer(Thing):
        pass
    
    class Employee(Thing):
        pass
    
    class Order(Thing):
        pass
    
    class Inventory(Thing):
        pass
    
    class Genre(Thing):
        pass
    
    class Author(Thing):
        pass
    
    # Define Object Properties
    class hasAuthor(ObjectProperty):
        domain = [Book]
        range = [Author]
    
    class hasGenre(ObjectProperty):
        domain = [Book]
        range = [Genre]
    
    class purchases(ObjectProperty):
        domain = [Customer]
        range = [Book]
    
    class worksAt(ObjectProperty):
        domain = [Employee]
        range = [Thing]  # Bookstore
    
    class hasInventory(ObjectProperty):
        domain = [Thing]  # Bookstore
        range = [Inventory]
    
    class contains(ObjectProperty):
        domain = [Inventory]
        range = [Book]
    
    class creates(ObjectProperty):
        domain = [Customer]
        range = [Order]
    
    class fulfills(ObjectProperty):
        domain = [Employee]
        range = [Order]
    
    # Define Data Properties
    class hasPrice(DataProperty):
        domain = [Book]
        range = [float]
    
    class availableQuantity(DataProperty):
        domain = [Book]
        range = [int]
    
    class hasName(DataProperty):
        domain = [Thing]
        range = [str]
    
    class hasId(DataProperty):
        domain = [Thing]
        range = [str]
    
    class hasBudget(DataProperty):
        domain = [Customer]
        range = [float]
    
    class restockThreshold(DataProperty):
        domain = [Book]
        range = [int]
    
    class timestamp(DataProperty):
        domain = [Order]
        range = [float]

# Message Bus for agent communication
class MessageBus:
    def __init__(self):
        self.messages = defaultdict(list)
        self.subscribers = defaultdict(list)
    
    def subscribe(self, topic, agent):
        """Subscribe an agent to a topic"""
        self.subscribers[topic].append(agent)
    
    def publish(self, topic, message):
        """Publish a message to a topic"""
        self.messages[topic].append(message)
        # Notify all subscribers
        for agent in self.subscribers[topic]:
            agent.receive_message(topic, message)
    
    def get_messages(self, topic):
        """Get all messages for a topic"""
        return self.messages[topic]

# Create global message bus
message_bus = MessageBus()

# Customer Agent
class CustomerAgent(Agent):
    def __init__(self, unique_id, model, budget=100.0, preferred_genres=None):
        super().__init__(unique_id, model)
        self.budget = budget
        self.preferred_genres = preferred_genres or ["Fiction", "Science"]
        self.purchased_books = []
        self.satisfaction = 0.5
        
        # Create ontology individual
        self.onto_customer = Customer(f"customer_{unique_id}")
        self.onto_customer.hasId = [str(unique_id)]
        self.onto_customer.hasName = [f"Customer_{unique_id}"]
        self.onto_customer.hasBudget = [budget]
        
        # Subscribe to relevant topics
        message_bus.subscribe("book_available", self)
        message_bus.subscribe("price_update", self)
    
    def step(self):
        #Customer behavior: browse and potentially purchase books
        if self.budget > 10 and random.random() < 0.3:  # 30% chance to browse
            self.browse_and_purchase()
    
    def browse_and_purchase(self):
        #Browse available books and make purchase decision
        available_books = [agent for agent in self.model.schedule.agents 
                          if isinstance(agent, BookAgent) and agent.stock > 0]
        
        if not available_books:
            return
        
        # Filter by preferred genres
        preferred_books = [book for book in available_books 
                          if book.genre in self.preferred_genres]
        
        if not preferred_books:
            preferred_books = available_books  # Fallback to any available book
        
        # Select a book to potentially purchase
        book = random.choice(preferred_books)
        
        if book.price <= self.budget:
            self.purchase_book(book)
    
    def purchase_book(self, book_agent):
        # Purchase a book from a book agent
        if book_agent.stock > 0 and book_agent.price <= self.budget:
            # Update budget and records
            self.budget -= book_agent.price
            self.purchased_books.append(book_agent.unique_id)
            self.satisfaction = min(1.0, self.satisfaction + 0.1)
            
            # Update book stock
            book_agent.stock -= 1
            book_agent.total_sales += 1
            
            # Update ontology
            self.onto_customer.purchases.append(book_agent.onto_book)
            book_agent.onto_book.availableQuantity = [book_agent.stock]
            
            # Create order in ontology
            order = Order(f"order_{self.unique_id}_{book_agent.unique_id}_{time.time()}")
            order.timestamp = [time.time()]
            self.onto_customer.creates.append(order)
            
            # Publish purchase message
            message_bus.publish("book_purchased", {
                "customer_id": self.unique_id,
                "book_id": book_agent.unique_id,
                "price": book_agent.price,
                "remaining_stock": book_agent.stock
            })
            
            print(f"Customer {self.unique_id} purchased {book_agent.title} for ${book_agent.price:.2f}")
    
    def receive_message(self, topic, message):
        # Handle received messages
        if topic == "book_available":
            # React to new book availability
            if random.random() < 0.2:  # 20% chance to be interested
                self.browse_and_purchase()

# Employee Agent
class EmployeeAgent(Agent):
    def __init__(self, unique_id, model, restock_threshold=5):
        super().__init__(unique_id, model)
        self.restock_threshold = restock_threshold
        self.restocked_books = []
        
        # Create ontology individual
        self.onto_employee = Employee(f"employee_{unique_id}")
        self.onto_employee.hasId = [str(unique_id)]
        self.onto_employee.hasName = [f"Employee_{unique_id}"]
        
        # Subscribe to restock requests
        message_bus.subscribe("restock_needed", self)
        message_bus.subscribe("book_purchased", self)
    
    def step(self):
        # Employee behavior: check inventory and restock if needed
        self.check_and_restock()
    
    def check_and_restock(self):
        # Check all books and restock those with low inventory
        book_agents = [agent for agent in self.model.schedule.agents 
                      if isinstance(agent, BookAgent)]
        
        for book in book_agents:
            if book.stock <= self.restock_threshold and random.random() < 0.7:
                self.restock_book(book)
    
    def restock_book(self, book_agent):
        # Restock a specific book
        restock_amount = random.randint(10, 20)
        old_stock = book_agent.stock
        book_agent.stock += restock_amount
        self.restocked_books.append(book_agent.unique_id)
        
        # Update ontology
        book_agent.onto_book.availableQuantity = [book_agent.stock]
        
        # Publish restock message
        message_bus.publish("book_restocked", {
            "employee_id": self.unique_id,
            "book_id": book_agent.unique_id,
            "old_stock": old_stock,
            "new_stock": book_agent.stock,
            "restocked_amount": restock_amount
        })
        
        print(f"Employee {self.unique_id} restocked {book_agent.title}: {old_stock} -> {book_agent.stock}")
    
    def receive_message(self, topic, message):
        # Handle received messages
        if topic == "restock_needed":
            book_id = message.get("book_id")
            book_agents = [agent for agent in self.model.schedule.agents 
                          if isinstance(agent, BookAgent) and agent.unique_id == book_id]
            if book_agents:
                self.restock_book(book_agents[0])

# Book Agent
class BookAgent(Agent):
    def __init__(self, unique_id, model, title, author, genre, price, initial_stock=15):
        super().__init__(unique_id, model)
        self.title = title
        self.author = author
        self.genre = genre
        self.price = price
        self.stock = initial_stock
        self.total_sales = 0
        self.restock_threshold = 5
        
        # Create ontology individuals
        self.onto_book = Book(f"book_{unique_id}")
        self.onto_book.hasId = [str(unique_id)]
        self.onto_book.hasName = [title]
        self.onto_book.hasPrice = [price]
        self.onto_book.availableQuantity = [initial_stock]
        self.onto_book.restockThreshold = [self.restock_threshold]
        
        # Create author and genre individuals if they don't exist
        author_individual = Author(f"author_{author.replace(' ', '_')}")
        author_individual.hasName = [author]
        self.onto_book.hasAuthor = [author_individual]
        
        genre_individual = Genre(f"genre_{genre}")
        genre_individual.hasName = [genre]
        self.onto_book.hasGenre = [genre_individual]
    
    def step(self):
        # Book behavior: monitor stock and request restock if needed
        if self.stock <= self.restock_threshold:
            message_bus.publish("restock_needed", {
                "book_id": self.unique_id,
                "current_stock": self.stock,
                "threshold": self.restock_threshold
            })
        
        # Occasionally adjust price based on demand
        if random.random() < 0.1:  # 10% chance
            self.adjust_price()
    
    def adjust_price(self):
        # Adjust price based on sales performance
        if self.total_sales > 5:  # High demand
            self.price *= 1.05  # Increase price by 5%
        elif self.total_sales == 0 and self.stock > 10:  # Low demand
            self.price *= 0.95  # Decrease price by 5%
        
        # Update ontology
        self.onto_book.hasPrice = [self.price]
        
        # Publish price update
        message_bus.publish("price_update", {
            "book_id": self.unique_id,
            "new_price": self.price
        })

# Bookstore Model
class BookstoreModel(Model):
    def __init__(self, num_customers=10, num_employees=2, num_books=15):
        self.num_customers = num_customers
        self.num_employees = num_employees
        self.num_books = num_books
        self.schedule = RandomActivation(self)
        
        # Create book data
        book_data = [
            ("Python Programming", "John Smith", "Technology", 29.99),
            ("Data Science Handbook", "Jane Doe", "Technology", 39.99),
            ("Mystery Novel", "Alice Brown", "Fiction", 14.99),
            ("Science Fiction Epic", "Bob Wilson", "Science Fiction", 24.99),
            ("History of AI", "Carol Davis", "Technology", 34.99),
            ("Romance Story", "David Miller", "Romance", 12.99),
            ("Thriller Adventure", "Eve Johnson", "Thriller", 19.99),
            ("Fantasy Quest", "Frank Anderson", "Fantasy", 22.99),
            ("Biography", "Grace Taylor", "Biography", 18.99),
            ("Self Help Guide", "Henry White", "Self Help", 16.99),
            ("Cooking Recipes", "Ivy Green", "Cooking", 21.99),
            ("Travel Guide", "Jack Blue", "Travel", 25.99),
            ("Art History", "Kate Red", "Art", 32.99),
            ("Music Theory", "Leo Orange", "Music", 28.99),
            ("Philosophy Basics", "Mia Purple", "Philosophy", 26.99)
        ]
        
        # Create book agents
        for i in range(min(num_books, len(book_data))):
            title, author, genre, price = book_data[i]
            book = BookAgent(i, self, title, author, genre, price)
            self.schedule.add(book)
        
        # Create customer agents
        genres = ["Technology", "Fiction", "Science Fiction", "Romance", "Thriller", "Fantasy"]
        for i in range(num_customers):
            customer_id = num_books + i
            budget = random.uniform(50, 200)
            preferred_genres = random.sample(genres, random.randint(1, 3))
            customer = CustomerAgent(customer_id, self, budget, preferred_genres)
            self.schedule.add(customer)
        
        # Create employee agents
        for i in range(num_employees):
            employee_id = num_books + num_customers + i
            employee = EmployeeAgent(employee_id, self)
            self.schedule.add(employee)
        
        # Data collector for statistics
        self.datacollector = DataCollector(
            model_reporters={
                "Total Books": lambda m: sum(1 for a in m.schedule.agents if isinstance(a, BookAgent)),
                "Total Stock": lambda m: sum(a.stock for a in m.schedule.agents if isinstance(a, BookAgent)),
                "Total Sales": lambda m: sum(a.total_sales for a in m.schedule.agents if isinstance(a, BookAgent)),
                "Average Customer Budget": lambda m: np.mean([a.budget for a in m.schedule.agents if isinstance(a, CustomerAgent)]),
                "Customer Satisfaction": lambda m: np.mean([a.satisfaction for a in m.schedule.agents if isinstance(a, CustomerAgent)])
            }
        )
    
    def step(self):
        # Advance the model by one step
        self.datacollector.collect(self)
        self.schedule.step()

def run_simulation():
    # Run the bookstore simulation
    print("Starting Bookstore Management System Simulation...")
    print("=" * 60)
    
    # Create and run the model
    model = BookstoreModel(num_customers=8, num_employees=2, num_books=12)
    
    print(f"Created bookstore with:")
    print(f"- {model.num_books} books")
    print(f"- {model.num_customers} customers") 
    print(f"- {model.num_employees} employees")
    print("\nStarting simulation...\n")
    
    # Run simulation for 20 steps
    for step in range(20):
        print(f"\n--- Step {step + 1} ---")
        model.step()
        
        # Print some statistics every 5 steps
        if (step + 1) % 5 == 0:
            print(f"\nStatistics after step {step + 1}:")
            data = model.datacollector.get_model_vars_dataframe()
            if not data.empty:
                latest = data.iloc[-1]
                print(f"Total Stock: {latest['Total Stock']}")
                print(f"Total Sales: {latest['Total Sales']}")
                print(f"Average Customer Budget: ${latest['Average Customer Budget']:.2f}")
                print(f"Customer Satisfaction: {latest['Customer Satisfaction']:.2f}")
    
    return model

def inspect_ontology():
    # Inspect the ontology after simulation
    print("\n" + "=" * 60)
    print("ONTOLOGY INSPECTION")
    print("=" * 60)
    
    # Inspect Books
    print("\nBooks in ontology:")
    for book in Book.instances():
        print(f"- {book.hasName[0] if book.hasName else 'Unnamed'}")
        if book.hasPrice:
            print(f"  Price: ${book.hasPrice[0]:.2f}")
        if book.availableQuantity:
            print(f"  Stock: {book.availableQuantity[0]}")
        if book.hasAuthor:
            print(f"  Author: {book.hasAuthor[0].hasName[0] if book.hasAuthor[0].hasName else 'Unknown'}")
        if book.hasGenre:
            print(f"  Genre: {book.hasGenre[0].hasName[0] if book.hasGenre[0].hasName else 'Unknown'}")
    
    # Inspect Customers
    print(f"\nCustomers in ontology: {len(list(Customer.instances()))}")
    for customer in list(Customer.instances())[:3]:  # Show first 3
        print(f"- {customer.hasName[0] if customer.hasName else 'Unnamed'}")
        if customer.hasBudget:
            print(f"  Budget: ${customer.hasBudget[0]:.2f}")
        if customer.purchases:
            print(f"  Purchased books: {len(customer.purchases)}")
    
    # Inspect Employees
    print(f"\nEmployees in ontology: {len(list(Employee.instances()))}")
    
    # Inspect Orders
    print(f"\nOrders created: {len(list(Order.instances()))}")
    
    # Summary statistics
    total_books = len(list(Book.instances()))
    total_customers = len(list(Customer.instances()))
    total_employees = len(list(Employee.instances()))
    total_orders = len(list(Order.instances()))
    
    print(f"\nSUMMARY:")
    print(f"Total Books: {total_books}")
    print(f"Total Customers: {total_customers}")
    print(f"Total Employees: {total_employees}")
    print(f"Total Orders: {total_orders}")

def generate_report(model):
    # Generate simulation report
    print("\n" + "=" * 60)
    print("SIMULATION REPORT")
    print("=" * 60)
    
    # Get final statistics
    data = model.datacollector.get_model_vars_dataframe()
    
    if not data.empty:
        print(f"\nFinal Statistics:")
        latest = data.iloc[-1]
        print(f"Total Books Available: {latest['Total Books']}")
        print(f"Total Stock Remaining: {latest['Total Stock']}")
        print(f"Total Sales Made: {latest['Total Sales']}")
        print(f"Average Customer Budget: ${latest['Average Customer Budget']:.2f}")
        print(f"Average Customer Satisfaction: {latest['Customer Satisfaction']:.2f}")
    
    # Agent-specific statistics
    book_agents = [a for a in model.schedule.agents if isinstance(a, BookAgent)]
    customer_agents = [a for a in model.schedule.agents if isinstance(a, CustomerAgent)]
    employee_agents = [a for a in model.schedule.agents if isinstance(a, EmployeeAgent)]
    
    print(f"\nAgent Performance:")
    print(f"Most Popular Book: {max(book_agents, key=lambda x: x.total_sales).title}")
    print(f"Highest Sales: {max(book_agents, key=lambda x: x.total_sales).total_sales}")
    print(f"Books Needing Restock: {len([b for b in book_agents if b.stock <= b.restock_threshold])}")
    print(f"Active Customers: {len([c for c in customer_agents if c.budget > 10])}")
    print(f"Total Restocking Actions: {sum(len(e.restocked_books) for e in employee_agents)}")

if __name__ == "__main__":
    # Run the complete simulation
    try:
        model = run_simulation()
        inspect_ontology()
        generate_report(model)
        
        print("\n" + "=" * 60)
        print("Simulation completed successfully!")
        print("The system demonstrated:")
        print("✓ Ontology-based knowledge representation")
        print("✓ Multi-agent interactions (Customers, Employees, Books)")
        print("✓ Message bus communication")
        print("✓ Automatic inventory management")
        print("✓ Customer purchasing behavior")
        print("✓ Employee restocking behavior")
        print("✓ Real-time ontology updates")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error during simulation: {e}")
        import traceback
        traceback.print_exc()